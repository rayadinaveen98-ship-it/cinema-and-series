import { Hono } from 'hono';
import { isLanguageTag, isValidMonthDay } from '@cinema/domain';
import type { CatalogueRepository } from './contracts.ts';
import { NeonCatalogueRepository } from './repository.ts';

type Bindings = { DATABASE_URL?: string };
type StoreFactory = (url: string) => CatalogueRepository;
type HttpErrorCode = 'BAD_REQUEST' | 'DATABASE_UNAVAILABLE';

class HttpError extends Error {
  readonly status: 400 | 503;
  readonly code: HttpErrorCode;
  constructor(status: 400 | 503, code: HttpErrorCode, message: string) {
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
