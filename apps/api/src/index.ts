import { Hono } from 'hono';
import { isLanguageTag, isValidMonthDay } from '@cinema/domain';
import type { CatalogueRepository } from './contracts.ts';
import { NeonCatalogueRepository } from './repository.ts';

type Bindings = { DATABASE_URL?: string };
type StoreFactory = (url: string) => CatalogueRepository;
type HttpErrorCode = 'BAD_REQUEST' | 'DATABASE_UNAVAILABLE' | 'PAYLOAD_TOO_LARGE';

class HttpError extends Error {
  readonly status: 400 | 413 | 503;
  readonly code: HttpErrorCode;
  constructor(status: 400 | 413 | 503, code: HttpErrorCode, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const uuidPattern=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function positiveInt(
  raw: string | undefined,
  name: string,
  fallback: number | null,
  maximum: number
): number {
  if (raw === undefined && fallback !== null) return fallback;
  if (!raw || !/^[0-9]+$/.test(raw)) {
    throw new HttpError(400,'BAD_REQUEST',name+' must be a positive integer');
  }
  const value=Number(raw);
  if (!Number.isSafeInteger(value) || value<1 || value>maximum) {
    throw new HttpError(400,'BAD_REQUEST',name+' is out of range');
  }
  return value;
}

function languageCode(value: string | undefined): string | undefined {
  if (value===undefined) return undefined;
  if (!isLanguageTag(value)) throw new HttpError(400,'BAD_REQUEST','Invalid language code');
  return value.toLowerCase();
}

function genreCode(value: string | undefined): string | undefined {
  if (value===undefined) return undefined;
  if (!/^[a-z][a-z0-9-]{1,39}$/.test(value)) {
    throw new HttpError(400,'BAD_REQUEST','Invalid genre code');
  }
  return value;
}


/**
 * Read a bounded UTF-8 JSON request without ever buffering an unbounded payload.
 * No personal identifier or viewing history is accepted by this endpoint.
 */
async function readBoundedJson(request: Request, maximumBytes = 4096): Promise<unknown> {
  const mime=(request.headers.get('content-type')??'').split(';',1)[0]?.toLowerCase().trim();
  if (mime!=='application/json') {
    throw new HttpError(400,'BAD_REQUEST','Content-Type must be application/json');
  }
  const declared=request.headers.get('content-length');
  if (declared!==null && (!/^\d+$/.test(declared) || Number(declared)>maximumBytes)) {
    throw new HttpError(413,'PAYLOAD_TOO_LARGE','Request payload exceeds limit');
  }
  const reader=request.body?.getReader();
  if (!reader) throw new HttpError(400,'BAD_REQUEST','JSON request body is required');
  const parts:Uint8Array[]=[];
  let total=0;
  try {
    while(true) {
      const chunk=await reader.read();
      if (chunk.done) break;
      total+=chunk.value.byteLength;
      if (total>maximumBytes) {
        await reader.cancel();
        throw new HttpError(413,'PAYLOAD_TOO_LARGE','Request payload exceeds limit');
      }
      parts.push(chunk.value);
    }
  } finally {
    reader.releaseLock();
  }
  const all=new Uint8Array(total);
  let offset=0;
  for (const part of parts) {
    all.set(part,offset);
    offset+=part.length;
  }
  try {
    return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(all)) as unknown;
  } catch {
    throw new HttpError(400,'BAD_REQUEST','Malformed JSON');
  }
}

function checkedPreferences(data:unknown): {languages:string[];genres:string[]} {
  if (typeof data!=='object' || data===null || Array.isArray(data)) {
    throw new HttpError(400,'BAD_REQUEST','Expected preferences object');
  }
  const input=data as Record<string,unknown>;
  const keys=Object.keys(input);
  if (keys.some(x=>x!=='languages' && x!=='genres')) {
    throw new HttpError(400,'BAD_REQUEST','Unrecognized preferences field');
  }
  if (!Array.isArray(input.languages) || !Array.isArray(input.genres) ||
      input.languages.length>8 || input.genres.length>12 ||
      input.languages.some(x=>typeof x!=='string' || !isLanguageTag(x)) ||
      input.genres.some(x=>typeof x!=='string' || !/^[a-z][a-z0-9-]{1,39}$/.test(x))) {
    throw new HttpError(400,'BAD_REQUEST','Invalid language or genre preferences');
  }
  const languages=[...new Set((input.languages as string[]).map(x=>x.toLowerCase().split('-')[0]!).filter(Boolean))];
  const genres=[...new Set((input.genres as string[]).map(x=>x.toLowerCase()))];
  if (languages.length+genres.length===0) {
    throw new HttpError(400,'BAD_REQUEST','Choose at least one language or genre');
  }
  return {languages,genres};
}

/** Exported app factory supports real Hono HTTP tests without a Neon credential. */
export function createApp(createStore: StoreFactory = (url) => new NeonCatalogueRepository(url)) {
  const app = new Hono<{ Bindings: Bindings }>();

  const store = (bindings: Bindings): CatalogueRepository => {
    if (!bindings?.DATABASE_URL) {
      throw new HttpError(503,'DATABASE_UNAVAILABLE','Catalogue database is not configured');
    }
    return createStore(bindings.DATABASE_URL);
  };

  app.use('/v1/*', async (c,next) => {
    c.header('X-Content-Type-Options','nosniff');
    await next();
  });

  app.get('/v1/health',(c)=>c.json({
    service:'cinema-and-series-api',
    status:'alive',
    catalogueReady:false,
    mode:'read-only-pilot'
  }));

  app.get('/v1/languages',async(c)=> {
    const data=await store(c.env).languages();
    c.header('Cache-Control','public,max-age=300,s-maxage=3600');
    return c.json({data});
  });

  app.get('/v1/genres',async(c)=> {
    const data=await store(c.env).genres();
    c.header('Cache-Control','public,max-age=300,s-maxage=3600');
    return c.json({data});
  });

  app.get('/v1/titles',async(c)=>{
    const limit=positiveInt(c.req.query('limit'),'limit',20,50);
    const cursor=c.req.query('cursor');
    if (cursor!==undefined && !uuidPattern.test(cursor)) {
      throw new HttpError(400,'BAD_REQUEST','Invalid cursor');
    }
    const type=c.req.query('type');
    if (type!==undefined && type!=='movie' && type!=='series') {
      throw new HttpError(400,'BAD_REQUEST','Invalid title type');
    }
    const language=languageCode(c.req.query('language'));
    const genre=genreCode(c.req.query('genre'));
    const page=await store(c.env).list({
      limit,
      ...(cursor?{cursor}:{}),
      ...(type?{type:type as 'movie'|'series'}:{}),
      ...(language?{language}:{}),
      ...(genre?{genre}:{})
    });
    c.header('Cache-Control','public,max-age=60,s-maxage=120');
    return c.json({data:page.items,page:{nextCursor:page.nextCursor}});
  });

  app.get('/v1/search',async(c)=>{
    const q=c.req.query('q')?.trim();
    if (!q || Array.from(q).length<2 || Array.from(q).length>100) {
      throw new HttpError(400,'BAD_REQUEST','Search needs 2 to 100 characters');
    }
    const limit=positiveInt(c.req.query('limit'),'limit',20,30);
    const data=await store(c.env).search(q,limit);
    c.header('Cache-Control','public,max-age=30,s-maxage=60');
    return c.json({data});
  });

  app.get('/v1/releases/on-this-day',async(c)=>{
    const month=positiveInt(c.req.query('month'),'month',null,12);
    const day=positiveInt(c.req.query('day'),'day',null,31);
    if (!isValidMonthDay(month,day)) {
      throw new HttpError(400,'BAD_REQUEST','Invalid calendar day');
    }
    const limit=positiveInt(c.req.query('limit'),'limit',20,50);
    const data=await store(c.env).onThisDay({month,day,limit});
    c.header('Cache-Control','public,max-age=300,s-maxage=3600');
    return c.json({data});
  });


  app.post('/v1/recommendations',async(c)=>{
    const preferences=checkedPreferences(await readBoundedJson(c.req.raw));
    const limit=positiveInt(c.req.query('limit'),'limit',20,30);
    const data=await store(c.env).recommend(preferences,limit);
    c.header('Cache-Control','no-store');
    return c.json({data});
  });

  app.get('/v1/titles/:id/similar',async(c)=>{
    const id=c.req.param('id');
    if (!uuidPattern.test(id)) throw new HttpError(400,'BAD_REQUEST','Invalid title ID');
    const limit=positiveInt(c.req.query('limit'),'limit',12,30);
    const data=await store(c.env).similar(id,limit);
    if (data===null) return c.json({error:{code:'NOT_FOUND',message:'Title not found'}},404);
    c.header('Cache-Control','public,max-age=60,s-maxage=120');
    return c.json({data});
  });

  app.get('/v1/titles/:id',async(c)=>{
    const id=c.req.param('id');
    if (!uuidPattern.test(id)) throw new HttpError(400,'BAD_REQUEST','Invalid title ID');
    const data=await store(c.env).detail(id);
    if (!data) return c.json({error:{code:'NOT_FOUND',message:'Title not found'}},404);
    c.header('Cache-Control','public,max-age=60,s-maxage=120');
    return c.json({data});
  });

  app.notFound(c=>c.json({error:{code:'NOT_FOUND',message:'Route not found'}},404));
  app.onError((error,c)=>{
    if (error instanceof HttpError) {
      return c.json({error:{code:error.code,message:error.message}},error.status);
    }
    // Never leak SQL statements, database URLs, or authentication information.
    console.error('Cinema API request failed');
    return c.json({error:{code:'INTERNAL_ERROR',message:'Unexpected service error'}},500);
  });

  return app;
}

export default createApp();
