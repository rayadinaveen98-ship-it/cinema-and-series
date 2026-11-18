import assert from 'node:assert/strict';
import { neon } from '@neondatabase/serverless';
import { createApp } from '../src/index.ts';
import { validateSmokeUrl, readonlyAssertions } from './safety.ts';

/**
 * Opt-in live in-process Hono -> Drizzle neon-http -> Neon read-only smoke.
 * NO Worker deployment, NO network listener, NO database writes.
 * This is intentionally separate from 'pnpm test' and automatic PR CI.
 */
async function run(): Promise<void> {
  const url=validateSmokeUrl(process.env.CINEMA_SMOKE_DATABASE_URL);
  const sql=neon(url);

  // A dedicated, least-privilege reader is mandatory; connection as the
  // owner/superuser or a role with any relevant write permission is rejected
  // BEFORE issuing catalogue requests.
  const permissions=await sql`
    WITH required(name) AS (
      VALUES
        ('titles'),('title_languages'),('title_genres'),('title_localizations'),
        ('genres'),('languages'),('release_events'),('series_debuts'),
        ('source_records'),('streaming_offers'),('providers')
    )
    SELECT
      current_user AS reader_role,
      name AS table_name,
      has_table_privilege(current_user,format('public.%I',name),'SELECT') AS can_read,
      has_table_privilege(current_user,format('public.%I',name),'INSERT') AS can_insert,
      has_table_privilege(current_user,format('public.%I',name),'UPDATE') AS can_update,
      has_table_privilege(current_user,format('public.%I',name),'DELETE') AS can_delete,
      has_table_privilege(current_user,format('public.%I',name),'TRUNCATE') AS can_truncate,
      has_table_privilege(current_user,format('public.%I',name),'REFERENCES') AS can_reference,
      has_table_privilege(current_user,format('public.%I',name),'TRIGGER') AS can_trigger,
      has_schema_privilege(current_user,'public','CREATE') AS can_create_schema,
      (p.rolsuper OR p.rolcreatedb OR p.rolcreaterole OR p.rolbypassrls) AS is_admin,
      (
        has_table_privilege(current_user,'public.ingestion_runs','SELECT') OR
        has_table_privilege(current_user,'public.staging_records','SELECT') OR
        has_table_privilege(current_user,'public.review_queue','SELECT') OR
        has_table_privilege(current_user,'public.catalogue_audit_log','SELECT')
      ) AS can_read_sensitive
    FROM required CROSS JOIN pg_roles p
    WHERE p.rolname=current_user
  `;
  readonlyAssertions(permissions as Record<string,unknown>[]);

  const app=createApp();
  const env={DATABASE_URL:url};
  const req=async(path:string,init?:RequestInit)=>{
    const r=await app.request('http://localhost'+path,init,env);
    const json=await r.json() as Record<string,any>;
    return {status:r.status,body:json,headers:r.headers};
  };
  const check=(name:string,got:number,expected:number)=>{
    assert.equal(got,expected,name+' failed HTTP status');
    console.log('PASS '+name);
  };

  let res=await req('/v1/health');
  check('liveness',res.status,200);
  assert.equal(res.body.catalogueReady,false);

  res=await req('/v1/titles?limit=20');
  check('browse',res.status,200);
  assert.ok(Array.isArray(res.body.data) && res.body.data.length>=13);
  assert.equal(new Set(res.body.data.map((t:{id:string})=>t.id)).size,res.body.data.length);

  res=await req('/v1/titles?limit=5');
  check('cursor first page',res.status,200);
  assert.equal(res.body.data.length,5);
  const firstIds=new Set(res.body.data.map((t:{id:string})=>t.id));
  assert.ok(typeof res.body.page?.nextCursor==='string');
  const next=await req('/v1/titles?limit=5&cursor='+encodeURIComponent(res.body.page.nextCursor));
  check('cursor second page',next.status,200);
  assert.ok(next.body.data.length>0 && next.body.data.every((t:{id:string})=>!firstIds.has(t.id)));

  res=await req('/v1/titles?type=series&limit=30');
  check('series filter',res.status,200);
  assert.ok(res.body.data.length>=2 && res.body.data.every((t:{type:string})=>t.type==='series'));

  res=await req('/v1/titles?language=ko&limit=30');
  check('Korean originals',res.status,200);
  assert.ok(res.body.data.length>=2);

  res=await req('/v1/search?q=Spirited%20Away');
  check('original-script alias search',res.status,200);
  assert.ok(res.body.data.some((t:{originalTitle:string})=>t.originalTitle==='千と千尋の神隠し'));

  res=await req('/v1/releases/on-this-day?month=11&day=2');
  check('original theatrical anniversary',res.status,200);
  assert.ok(res.body.data.some((t:{originalTitle:string;originalPremiereDate:string})=>
    t.originalTitle==='Intouchables' && t.originalPremiereDate==='2011-11-02'));

  const dark='c73e1404-0000-4000-8000-000000000205';
  res=await req('/v1/titles/'+dark);
  check('series detail',res.status,200);
  assert.equal(res.body.data.type,'series');
  assert.ok(res.body.data.releases.some((r:{kind:string;date:string;provider:string})=>
    r.kind==='series_debut' && r.date==='2017-12-01' && r.provider==='netflix'));
  assert.ok(Array.isArray(res.body.data.providers));
  assert.equal(res.body.data.providers.length,0,'historical launch is not a live OTT offer');

  res=await req('/v1/recommendations?limit=10',{
    method:'POST',
    headers:{'content-type':'application/json'},
    body:JSON.stringify({languages:['ko'],genres:['thriller']})
  });
  check('guest recommendation',res.status,200);
  assert.equal(res.headers.get('cache-control'),'no-store');
  assert.ok(res.body.data.length>0 && res.body.data.every((x:{score:number})=>x.score>0));

  res=await req('/v1/titles/'+dark+'/similar?limit=10');
  check('similar titles',res.status,200);
  assert.ok(res.body.data.every((t:{id:string})=>t.id!==dark));

  res=await req('/v1/languages');
  check('language directory',res.status,200);
  assert.ok(res.body.data.some((x:{code:string})=>x.code==='ko'));
  res=await req('/v1/genres');
  check('genre directory',res.status,200);
  assert.ok(res.body.data.some((x:{code:string})=>x.code==='thriller'));

  res=await req('/v1/titles/00000000-0000-4000-8000-000000000000');
  check('unknown title 404',res.status,404);
  res=await req('/v1/titles?cursor=not-a-uuid');
  check('invalid cursor 400',res.status,400);

  console.log('PASS LIVE_HONO_NEON_READONLY_SMOKE');
}
run().catch(()=>{
  // Do not emit connection strings, query details or raw driver messages.
  console.error('FAIL LIVE_HONO_NEON_READONLY_SMOKE');
  process.exitCode=1;
});
