#!/usr/bin/env node
/** Zero-Cloudflare credential tests of the real Worker D1-binding probe. */
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync,mkdtempSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {Miniflare,convertV4MiniflareOptions} from "miniflare";
import worker,{assertScratchBinding} from "./foundation_staging_worker_probe.mjs";

const STAGE_UUID="00000000-0000-4000-8000-000000000099";
const PROD_UUID="00000000-0000-4000-8000-000000000001";
const MIGRATIONS=[
  "migrations/0017_year_precision_catalogue.sql",
  "migrations/0027_catalogue_title_language_provenance.sql",
  "migrations/0018_series_catalogue.sql",
  "migrations/0019_series_language_provenance.sql",
  "migrations/0020_series_first_air_year_provenance.sql"
];
async function setup(){
  const dir=mkdtempSync(join(tmpdir(),"foundation-worker-probe-"));
  let mf;
  try{
    mf=new Miniflare(convertV4MiniflareOptions({
      modules:true,compatibilityDate:"2026-09-16",
      script:'export default {fetch(){return new Response("local-only")}}',
      d1Databases:{DB:STAGE_UUID},
      resourcePersistencePath:join(dir,"persist")
    }));
    const db=await mf.getD1Database("DB");
    for(const path of MIGRATIONS){
      const statements=readFileSync(path,"utf8").split("\n")
        .filter(line=>!line.trimStart().startsWith("--"))
        .join("\n").split(";").map(s=>s.trim()).filter(Boolean);
      for(const sql of statements){
        assert.match(sql,/^(?:(?:CREATE|ALTER)\s|UPDATE series_titles\s+SET language_source\b)/i);
        await db.prepare(sql).run();
      }
    }
    return {
      db,
      env:{
        DB:db,
        FOUNDATION_ONLY_MODE:"isolated-nonproduction-D1",
        FOUNDATION_STAGE_NAME:"foundation-v2-qa-39946487548-1",
        FOUNDATION_STAGE_UUID:STAGE_UUID,
        FOUNDATION_PRODUCTION_UUID:PROD_UUID,
        FOUNDATION_EPHEMERAL_TOKEN:"local-test-only-not-valid-in-cloudflare"
      },
      async close(){await mf.dispose();rmSync(dir,{recursive:true,force:true});}
    };
  }catch(error){
    if(mf)await mf.dispose();
    rmSync(dir,{recursive:true,force:true});
    throw error;
  }
}
const request=token=>new Request("https://test.invalid/__foundation_staging_probe",{
  method:"POST",headers:{"x-foundation-ephemeral-token":token}
});
test("fail closed on production identity, wrong scratch name or no D1 handle",async()=>{
  const x=await setup();
  try{
    assert.throws(()=>assertScratchBinding({...x.env,
      FOUNDATION_STAGE_UUID:PROD_UUID}),/scratch|production|identity/i);
    assert.throws(()=>assertScratchBinding({...x.env,
      FOUNDATION_STAGE_NAME:"cinema-and-series"}),/disposable QA/i);
    assert.throws(()=>assertScratchBinding({...x.env,DB:null}),/binding/i);
    const bad=await worker.fetch(request(x.env.FOUNDATION_EPHEMERAL_TOKEN),
      {...x.env,FOUNDATION_STAGE_UUID:PROD_UUID});
    assert.equal(bad.status,409);
    const none=await x.db.prepare("SELECT count(*) AS n FROM catalogue_titles").first();
    assert.equal(none.n,0);
  }finally{await x.close();}
});

test("no credentials, wrong method, wrong route and wrong token must do no work",async()=>{
  const x=await setup();
  try{
    const requests=[
      request("wrong-token"),
      new Request("https://test.invalid/other",{
        method:"POST",headers:{"x-foundation-ephemeral-token":
          x.env.FOUNDATION_EPHEMERAL_TOKEN}}),
      new Request("https://test.invalid/__foundation_staging_probe")
    ];
    for(const requestValue of requests){
      const response=await worker.fetch(requestValue,x.env);
      assert.equal(response.status,404);
    }
    assert.equal((await x.db.prepare("SELECT count(*) AS n FROM series_titles").first()).n,0);
  }finally{await x.close();}
});

test("scratch Worker Binding atomic forward, full inverse and both conflict cases",async()=>{
  const x=await setup();
  try{
    const response=await worker.fetch(
      request(x.env.FOUNDATION_EPHEMERAL_TOKEN),x.env);
    assert.equal(response.status,200);
    const result=await response.json();
    assert.equal(result.actual_worker_d1_batch_forward_inverse,true);
    assert.equal(result.original_rows_fully_restored,true);
    assert.equal(result.stale_last_row_atomic_abort,true);
    assert.equal(result.competing_edit_inverse_atomic_abort,true);
    assert.equal(result.unrelated_sentinel_untouched,true);
    assert.equal(result.production_database_writes,0);
    assert.equal(result.production_corrections_authorized,false);
    for(const table of ["catalogue_titles","series_titles"]){
      const rows=(await x.db.prepare("SELECT * FROM "+table).all()).results;
      assert.equal(rows.length,4);
      assert.equal(rows.filter(r=>r.language_name==="Unknown").length,3);
      assert.equal(rows.filter(r=>r.language_name==="Tamil").length,1);
      assert.equal(rows.filter(r=>r.language_source!==null).length,0);
    }
    const second=await worker.fetch(
      request(x.env.FOUNDATION_EPHEMERAL_TOKEN),x.env);
    assert.equal(second.status,409,"Repeat canary must refuse duplicate QA records");
  }finally{await x.close();}
});
