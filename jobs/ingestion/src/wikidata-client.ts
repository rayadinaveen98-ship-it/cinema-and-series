const canonicalEntityUrl=(id:string) =>
  'https://www.wikidata.org/wiki/Special:EntityData/'+id+'.json';
const isQId=(id:string)=>/^Q[1-9][0-9]*$/.test(id);
const maximumResponseBytes=1024*1024;

export class SourceFetchError extends Error {
  readonly code: string;
  readonly retryAfterSeconds: number | null;
  constructor(code:string,retryAfterSeconds:number|null=null) {
    super(code);
    this.code=code;
    this.retryAfterSeconds=retryAfterSeconds;
  }
}
export interface WikidataSnapshot {
  sourceId: string;
  canonicalSourceUrl: string;
  retrievedAt: string;
  revisionId: number | null;
  /** Raw, unverified Wikidata entity. Never auto-publish P577 or P364 claims. */
  rawEntity: Record<string, unknown>;
}
export interface WikidataClientOptions {
  fetcher?: typeof fetch;
  pause?: (milliseconds:number)=>Promise<void>;
  now?: ()=>Date;
  userAgent: string;
  /** For all sessions, 1 request / 1 second or slower; no parallel calls. */
  minimumIntervalMs?: number;
}

function retryDelaySeconds(value:string | null):number|null {
  if(!value) return null;
  const parsed=Number(value.trim());
  if(Number.isFinite(parsed) && parsed>=0) return Math.min(Math.ceil(parsed),3600);
  const when=Date.parse(value);
  if(Number.isFinite(when)) return Math.min(Math.max(0,Math.ceil((when-Date.now())/1000)),3600);
  return null;
}
async function limitedJson(response:Response):Promise<unknown> {
  const mime=(response.headers.get('content-type')??'').toLowerCase();
  if(!mime.includes('application/json') && !mime.includes('application/ld+json')) {
    throw new SourceFetchError('UNEXPECTED_RESPONSE_TYPE');
  }
  const stated=response.headers.get('content-length');
  if(stated && Number(stated)>maximumResponseBytes) throw new SourceFetchError('SOURCE_RESPONSE_TOO_LARGE');
  if(!response.body) throw new SourceFetchError('EMPTY_SOURCE_RESPONSE');
  const reader=response.body.getReader();
  const buffers:Uint8Array[]=[];
  let bytes=0;
  try {
    while(true) {
      const part=await reader.read();
      if(part.done) break;
      bytes+=part.value.byteLength;
      if(bytes>maximumResponseBytes) {
        await reader.cancel();
        throw new SourceFetchError('SOURCE_RESPONSE_TOO_LARGE');
      }
      buffers.push(part.value);
    }
  } finally {
    reader.releaseLock();
  }
  const buffer=new Uint8Array(bytes);
  let offset=0;
  for(const item of buffers){buffer.set(item,offset);offset+=item.byteLength;}
  try {
    return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(buffer)) as unknown;
  } catch {
    throw new SourceFetchError('INVALID_SOURCE_JSON');
  }
}

function isObject(value:unknown):value is Record<string,unknown> {
  return typeof value==='object' && value!==null && !Array.isArray(value);
}

/**
 * Explicitly invoked fetch-only adapter. Does not import titles or stage rows.
 * Enforces conservative pacing, source allowlist, no redirects and stop-on-429.
 * All tests inject a mock fetcher; CI never contacts Wikimedia.
 */
export class WikidataReadOnlyClient {
  private readonly fetcher:typeof fetch;
  private readonly pause:(ms:number)=>Promise<void>;
  private readonly now:()=>Date;
  private readonly agent:string;
  private readonly interval:number;

  constructor(options:WikidataClientOptions) {
    if(!/^CinemaAndSeriesPilot\/[0-9]+\.[0-9]+ \(.+\)$/.test(options.userAgent) ||
       !options.userAgent.includes('https://github.com/rayadinaveen98-ship-it/cinema-and-series')) {
      throw new SourceFetchError('DESCRIPTIVE_USER_AGENT_REQUIRED');
    }
    if(options.minimumIntervalMs!==undefined &&
       (!Number.isInteger(options.minimumIntervalMs) || options.minimumIntervalMs<1000)) {
      throw new SourceFetchError('RATE_LIMIT_TOO_AGGRESSIVE');
    }
    this.fetcher=options.fetcher??fetch;
    this.pause=options.pause??(ms=>new Promise(resolve=>setTimeout(resolve,ms)));
    this.now=options.now??(()=>new Date());
    this.agent=options.userAgent;
    this.interval=options.minimumIntervalMs??1000;
  }

  async fetchEntities(ids:readonly string[]):Promise<WikidataSnapshot[]> {
    if(!Array.isArray(ids) || ids.length<1 || ids.length>5 ||
       new Set(ids).size!==ids.length || ids.some(id=>typeof id!=='string'||!isQId(id))) {
      throw new SourceFetchError('INVALID_ENTITY_BATCH');
    }
    const snapshots:WikidataSnapshot[]=[];
    for(let index=0;index<ids.length;index++) {
      if(index>0) await this.pause(this.interval);
      const id=ids[index]!;
      const url=canonicalEntityUrl(id);
      let response:Response;
      try {
        response=await this.fetcher(url,{
          method:'GET',redirect:'error',
          headers:{'User-Agent':this.agent,'Accept':'application/json'},
          signal:AbortSignal.timeout(10000)
        });
      } catch {
        throw new SourceFetchError('SOURCE_NETWORK_ERROR');
      }
      if(response.status===429 || response.status===503) {
        throw new SourceFetchError('SOURCE_BACKOFF_REQUIRED',
          retryDelaySeconds(response.headers.get('retry-after')));
      }
      if(!response.ok) throw new SourceFetchError('SOURCE_HTTP_'+response.status);
      const result=await limitedJson(response);
      if(!isObject(result) || !isObject(result.entities)) {
        throw new SourceFetchError('SOURCE_PAYLOAD_MALFORMED');
      }
      const entity=result.entities[id];
      if(!isObject(entity) || entity.id!==id || entity.type!=='item') {
        throw new SourceFetchError('SOURCE_IDENTITY_MISMATCH');
      }
      const revision=entity.lastrevid;
      snapshots.push({
        sourceId:'wikidata:'+id,
        canonicalSourceUrl:'https://www.wikidata.org/wiki/'+id,
        retrievedAt:this.now().toISOString(),
        revisionId:typeof revision==='number' && Number.isSafeInteger(revision) && revision>0
          ? revision:null,
        rawEntity:entity
      });
    }
    return snapshots;
  }
}
