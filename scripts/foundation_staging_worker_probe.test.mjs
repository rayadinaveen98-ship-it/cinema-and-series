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
    await db.prepare("CREATE TABLE foundation_v2_stage_proof ("+
      "id INTEGER PRIMARY KEY CHECK(id=1),stage_name TEXT NOT NULL,"+
      "stage_uuid TEXT NOT NULL,access_nonce TEXT NOT NULL,"+
      "stage_phase TEXT NOT NULL DEFAULT 'new')").run();
    await db.prepare("INSERT INTO foundation_v2_stage_proof (id,stage_name,stage_uuid,access_nonce) VALUES (1,?,?,?)")
      .bind("foundation-v2-qa-39946487548-1",STAGE_UUID,
        "local-test-only-not-valid-in-cloudflare").run();
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
const request=(token,phase="seed")=>new Request("https://test.invalid/__foundation_staging_probe",{
  method:"POST",headers:{"x-foundation-ephemeral-token":token,
    "x-foundation-probe-phase":phase}
});
test("fail closed on production identity, wrong scratch name or no D1 handle",async()=>{
  const x=await setup();
  try{
    assert.throws(()=>assertScratchBinding({...x.env,
      FOUNDATION_STAGE_UUID:PROD_UUID}),/scratch|production|identity/i);
    assert.throws(()=>assertScratchBinding({...x.env,
      FOUNDATION_STAGE_NAME:"cinema-and-series"}),/scratch|database names/i);
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
    const phases=["seed","film","series","stale","conflict","finish"];
    let result;
    for(const phase of phases){
      const response=await worker.fetch(
        request(x.env.FOUNDATION_EPHEMERAL_TOKEN,phase),x.env);
      assert.equal(response.status,200,"Expected approved phase: "+phase);
      result=await response.json();
      assert.equal(result.phase,phase);
      assert.equal(result.phase_passed,true);
      assert.equal(result.production_database_writes,0);
    }
    assert.equal(result.stage_completed,true);
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

test("missing database-resident proof rejects a fake scratch Worker binding",async()=>{
  const x=await setup();
  try{
    await x.db.prepare("DELETE FROM foundation_v2_stage_proof").run();
    const response=await worker.fetch(
      request(x.env.FOUNDATION_EPHEMERAL_TOKEN),x.env);
    assert.equal(response.status,409);
    assert.equal((await x.db.prepare(
      "SELECT count(*) AS n FROM catalogue_titles").first()).n,0);
    assert.equal((await x.db.prepare(
      "SELECT count(*) AS n FROM series_titles").first()).n,0);
  }finally{await x.close();}
});

test("mismatched database-resident UUID blocks worker writes",async()=>{
  const x=await setup();
  try{
    await x.db.prepare(
      "UPDATE foundation_v2_stage_proof SET stage_uuid=? WHERE id=1"
    ).bind(PROD_UUID).run();
    const response=await worker.fetch(
      request(x.env.FOUNDATION_EPHEMERAL_TOKEN),x.env);
    assert.equal(response.status,409);
    assert.equal((await x.db.prepare(
      "SELECT count(*) AS n FROM catalogue_titles").first()).n,0);
  }finally{await x.close();}
});

test("phase skipping, replay and invalid phases must not mutate scratch D1",async()=>{
  const x=await setup();
  try{
    const token=x.env.FOUNDATION_EPHEMERAL_TOKEN;
    for(const phase of ["film","series","not-a-phase"]){
      const response=await worker.fetch(request(token,phase),x.env);
      assert.equal(response.status,409,"Skip/invalid phase must fail: "+phase);
    }
    const seeded=await worker.fetch(request(token,"seed"),x.env);
    assert.equal(seeded.status,200);
    const original=(await x.db.prepare("SELECT * FROM catalogue_titles").all()).results;
    assert.equal(original.length,4);
    assert.equal((await worker.fetch(request(token,"seed"),x.env)).status,409);
    assert.equal((await worker.fetch(request(token,"series"),x.env)).status,409);
    assert.deepEqual((await x.db.prepare("SELECT * FROM catalogue_titles").all()).results,original);
    assert.equal((await x.db.prepare(
      "SELECT stage_phase FROM foundation_v2_stage_proof WHERE id=1").first()).stage_phase,
      "seed");
  }finally{await x.close();}
});

test("authenticated preview readiness proves the actual scratch D1 without writes",async()=>{
  const x=await setup();
  try{
    const path="https://test.invalid/__foundation_staging_probe_health";
    const unauthenticated=await worker.fetch(new Request(path),x.env);
    assert.equal(unauthenticated.status,404);
    const request=new Request(path,{
      headers:{"x-foundation-ephemeral-token":x.env.FOUNDATION_EPHEMERAL_TOKEN}
    });
    const response=await worker.fetch(request,x.env);
    assert.equal(response.status,200);
    const result=await response.json();
    assert.equal(result.schema,"foundation-v2-worker-binding-health-v1");
    assert.equal(result.scratch_binding_verified,true);
    assert.equal(result.scratch_write_performed,false);
    assert.equal(result.production_database_writes,0);
    for(const table of ["catalogue_titles","series_titles"]){
      assert.equal((await x.db.prepare(
        "SELECT count(*) AS n FROM "+table).first()).n,0);
    }
    assert.equal((await x.db.prepare(
      "SELECT stage_phase FROM foundation_v2_stage_proof WHERE id=1"
    ).first()).stage_phase,"new");
  }finally{await x.close();}
});

test("preview health rejects mismatched scratch proof instead of treating 404 as ready",async()=>{
  const x=await setup();
  try{
    await x.db.prepare("UPDATE foundation_v2_stage_proof SET stage_uuid=? WHERE id=1")
      .bind(PROD_UUID).run();
    const response=await worker.fetch(new Request(
      "https://test.invalid/__foundation_staging_probe_health",{
        headers:{"x-foundation-ephemeral-token":x.env.FOUNDATION_EPHEMERAL_TOKEN}
      }),x.env);
    assert.equal(response.status,409);
    assert.equal((await x.db.prepare(
      "SELECT count(*) AS n FROM catalogue_titles").first()).n,0);
  }finally{await x.close();}
});
