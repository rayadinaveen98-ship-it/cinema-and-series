#!/usr/bin/env node
/** Data Foundation V2: real D1.batch local tests, NEVER remote. */
import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync,mkdtempSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {Miniflare,convertV4MiniflareOptions} from "miniflare";
import {
  checkRows,prepareAtomicBatch,validateOwnerApproval,
  hashOfBatch,applyApprovedBatch,applyApprovedInverseBatch,verifyAppliedBatch
} from "./foundation_d1_guarded_executor.mjs";

const TOKEN="https://github.com/rayadinaveen98-ship-it/cinema-and-series/issues/999999";
function grant(items){
  return {
    schema:"foundation-v2-owner-approval-v1",
    approved:true,status:"OWNER_APPROVED_FOR_PRODUCTION",
    database_name:"cinema-and-series",
    freeze_exception_scope:"language_fields_only",
    exact_batch_sha256:hashOfBatch(items),
    owner_approval_reference:TOKEN,
    production_write_enabled:true,
  };
}
const qid=i=>"Q"+(70000000+i);
const sqlString=v=>"'"+String(v).replaceAll("'","''")+"'";
function migrations(db,paths){
  return (async()=>{
    for(const path of paths){
      const statements=readFileSync(path,"utf8")
        .split("\n").filter(line=>!line.trimStart().startsWith("--"))
        .join("\n").split(";").map(x=>x.trim()).filter(Boolean);
      for(const statement of statements){
        assert.match(statement,/^(?:(?:CREATE|ALTER)\s|UPDATE series_titles\s+SET language_source\b)/i);
        await db.prepare(statement).run();
      }
    }
  })();
}
async function environment(){
  const dir=mkdtempSync(join(tmpdir(),"foundation-guarded-d1-"));
  let mf;
  try{
    mf=new Miniflare(convertV4MiniflareOptions({
      modules:true,compatibilityDate:"2026-09-16",
      script:'export default {fetch(){return new Response("isolated test")}}',
      d1Databases:{DB:"00000000-0000-4000-8000-000000000099"},
      resourcePersistencePath:join(dir,"persist"),
    }));
    const db=await mf.getD1Database("DB");
    await migrations(db,[
      "migrations/0017_year_precision_catalogue.sql",
      "migrations/0027_catalogue_title_language_provenance.sql",
      "migrations/0018_series_catalogue.sql",
      "migrations/0019_series_language_provenance.sql",
      "migrations/0020_series_first_air_year_provenance.sql",
    ]);
    return {db,dispose:async()=>{await mf.dispose();rmSync(dir,{recursive:true,force:true});}};
  }catch(e){
    if(mf)await mf.dispose();
    rmSync(dir,{recursive:true,force:true});
    throw e;
  }
}
async function seed(db,table,n=7){
  for(let i=1;i<=n;i++){
    const q=qid(i+(table==="series_titles"?200:0));
    if(table==="catalogue_titles"){
      await db.prepare("INSERT INTO catalogue_titles "+
        "(id,wikidata_qid,title,release_year,language_name,country_code,source_category,source_url)"+
        " VALUES (?,?,?,?,?,?,?,?)").bind(
        "f-"+q,q,"Example Film "+i,2018,"Unknown","IN","qa","https://www.wikidata.org/wiki/"+q
      ).run();
    }else{
      await db.prepare("INSERT INTO series_titles "+
        "(id,wikidata_qid,title,first_air_year,language_name,country_code,source_category,source_url)"+
        " VALUES (?,?,?,?,?,?,?,?)").bind(
        "s-"+q,q,"Example Series "+i,2018,"Unknown","IN","qa","https://www.wikidata.org/wiki/"+q
      ).run();
    }
  }
  const found=(await db.prepare("SELECT * FROM "+table+" ORDER BY wikidata_qid").all()).results;
  return found.map(row=>({
    table,row,qid:row.wikidata_qid,proposed_language:"Telugu",
    evidence_url:"https://www.wikidata.org/wiki/"+row.wikidata_qid
  }));
}
async function rows(db,table){
  return (await db.prepare("SELECT * FROM "+table+" ORDER BY wikidata_qid").all()).results;
}

test("must refuse missing approval even with valid DB handle",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",2);
    assert.throws(()=>validateOwnerApproval({},items),/approval|authorization/i);
    await assert.rejects(()=>applyApprovedBatch(fixture.db,items,{}));
    assert.equal((await rows(fixture.db,"catalogue_titles"))[0].language_name,"Unknown");
    const rejected=grant(items);rejected.exact_batch_sha256="x".repeat(64);
    assert.throws(()=>validateOwnerApproval(rejected,items));
    const off=grant(items);off.production_write_enabled=false;
    assert.throws(()=>validateOwnerApproval(off,items));
  }finally{await fixture.dispose();}
});

test("atomic film D1 transaction changes exactly 7 and no unrelated identity",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",7);
    const before=await rows(fixture.db,"catalogue_titles");
    const result=await applyApprovedBatch(fixture.db,items,grant(items));
    assert.equal(result.changed,7);
    const after=await rows(fixture.db,"catalogue_titles");
    assert.deepEqual(after.map(x=>x.wikidata_qid),before.map(x=>x.wikidata_qid));
    assert(after.every(x=>x.language_name==="Telugu" &&
      x.language_source==="wikidata:P364"));
    await assert.rejects(()=>applyApprovedBatch(fixture.db,items,grant(items)),
      /D1|failed|JSON|SQLite|malformed|guard/i);
    assert.deepEqual(await rows(fixture.db,"catalogue_titles"),after);
  }finally{await fixture.dispose();}
});

test("stale final row rolls back all preceding updates atomically",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",7);
    const last=items.at(-1).qid;
    await fixture.db.prepare("UPDATE catalogue_titles SET title='Other editor' WHERE wikidata_qid=?")
      .bind(last).run();
    const before=await rows(fixture.db,"catalogue_titles");
    await assert.rejects(()=>applyApprovedBatch(fixture.db,items,grant(items)));
    assert.deepEqual(await rows(fixture.db,"catalogue_titles"),before);
  }finally{await fixture.dispose();}
});

test("series language guard preserves original years and supports exact updates",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"series_titles",6);
    const result=await applyApprovedBatch(fixture.db,items,grant(items));
    assert.equal(result.changed,6);
    const after=await rows(fixture.db,"series_titles");
    assert(after.every(x=>x.language_name==="Telugu" && x.first_air_year===2018));
    assert(after.every(x=>x.language_source_url==="https://www.wikidata.org/wiki/"+x.wikidata_qid));
  }finally{await fixture.dispose();}
});

test("identity, held films, mixed tables, unknown provenance and size overflow rejected",()=>{
  const row={
    id:"f-Q80000",wikidata_qid:"Q80000",title:"A",release_year:2000,
    country_code:"IN",language_name:"Unknown",language_source:null,
    language_source_url:null,updated_at:"2026-01-01",created_at:"2026-01-01",
    source_category:"qa",source_url:"https://www.wikidata.org/wiki/Q80000"
  };
  const item={table:"catalogue_titles",qid:"Q80000",row,
              proposed_language:"Tamil",evidence_url:"https://www.wikidata.org/wiki/Q80000"};
  assert.equal(checkRows([item]),"catalogue_titles");
  const bad={...item,row:{...row,language_source:"unrelated"}};
  assert.throws(()=>checkRows([bad]));
  assert.throws(()=>checkRows([item,{...item}]));
  assert.throws(()=>checkRows([{...item,row:{...row,wikidata_qid:"Q20649744"},qid:"Q20649744"}]));
  assert.throws(()=>checkRows(Array(101).fill(item)));
  assert.throws(()=>checkRows([{...item,evidence_url:"https://example.com"}]));
});


test("approved inverse restores every original film column exactly",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",5);
    const before=await rows(fixture.db,"catalogue_titles");
    await applyApprovedBatch(fixture.db,items,grant(items));
    const afterVerified=await verifyAppliedBatch(fixture.db,items);
    assert.equal(afterVerified.verified,5);
    const denied=grant(items);
    await assert.rejects(()=>applyApprovedInverseBatch(
      fixture.db,items,afterVerified.after,denied
    ),/rollback approval/i);
    const approval={...grant(items),rollback_approved:true,
      rollback_batch_sha256:hashOfBatch(items)};
    const inverse=await applyApprovedInverseBatch(
      fixture.db,items,afterVerified.after,approval);
    assert.equal(inverse.restored,5);
    assert.deepEqual(await rows(fixture.db,"catalogue_titles"),before);
  }finally{await fixture.dispose();}
});

test("a newer series edit prevents inverse from partially restoring previous rows",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"series_titles",5);
    await applyApprovedBatch(fixture.db,items,grant(items));
    const after=await verifyAppliedBatch(fixture.db,items);
    await fixture.db.prepare("UPDATE series_titles SET title='Independent editor' "+
      "WHERE wikidata_qid=?").bind(items.at(-1).qid).run();
    const newer=await rows(fixture.db,"series_titles");
    const approval={...grant(items),rollback_approved:true,
      rollback_batch_sha256:hashOfBatch(items)};
    await assert.rejects(()=>applyApprovedInverseBatch(
      fixture.db,items,after.after,approval),/SQLite|JSON|malformed|constraint|D1|guard/i);
    assert.deepEqual(await rows(fixture.db,"series_titles"),newer);
  }finally{await fixture.dispose();}
});

test("missing non-language columns are rejected BEFORE writing any film records",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",3);
    const before=await rows(fixture.db,"catalogue_titles");
    const truncated=items.map((item,i)=>{
      if(i!==1)return item;
      const row={...item.row};delete row.source_url;
      return {...item,row};
    });
    await assert.rejects(
      ()=>applyApprovedBatch(fixture.db,truncated,grant(truncated)),
      /sealed snapshot missing|D1 columns/i
    );
    assert.deepEqual(await rows(fixture.db,"catalogue_titles"),before);
  }finally{await fixture.dispose();}
});

test("unreviewed live migration blocks all writes even with a full old snapshot",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"catalogue_titles",3);
    await fixture.db.prepare("ALTER TABLE catalogue_titles ADD COLUMN unreviewed_note TEXT").run();
    const before=await rows(fixture.db,"catalogue_titles");
    await assert.rejects(
      ()=>applyApprovedBatch(fixture.db,items,grant(items)),
      /unknown live D1 column/i
    );
    assert.deepEqual(await rows(fixture.db,"catalogue_titles"),before);
  }finally{await fixture.dispose();}
});

test("a schema change after forward apply prevents rollback from silently missing a column",async()=>{
  const fixture=await environment();
  try{
    const items=await seed(fixture.db,"series_titles",3);
    await applyApprovedBatch(fixture.db,items,grant(items));
    const after=await verifyAppliedBatch(fixture.db,items);
    await fixture.db.prepare("ALTER TABLE series_titles ADD COLUMN later_editor TEXT").run();
    const before=await rows(fixture.db,"series_titles");
    const approval={...grant(items),rollback_approved:true,
      rollback_batch_sha256:hashOfBatch(items)};
    await assert.rejects(
      ()=>applyApprovedInverseBatch(fixture.db,items,after.after,approval),
      /unknown live D1 column/i
    );
    assert.deepEqual(await rows(fixture.db,"series_titles"),before);
  }finally{await fixture.dispose();}
});
