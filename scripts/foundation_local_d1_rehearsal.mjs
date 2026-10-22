#!/usr/bin/env node
/** Data Foundation V2 isolated Miniflare D1 recovery QA. No remote credentials. */
import assert from "node:assert/strict";
import {readFileSync,writeFileSync,mkdtempSync,rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {Miniflare,convertV4MiniflareOptions} from "miniflare";

const FIELDS=["id","wikidata_qid","title","release_year","country_code","language_name"];
const HELD=new Set(["Q20967570","Q109519684","Q20649744"]);
const SOURCE="Wikidata P364 (LOCAL_QA_ONLY)";
const CHECK_TABLE="CREATE TABLE qa_guard(value INTEGER NOT NULL CHECK(value=0));";
const FWD_GUARD="INSERT INTO qa_guard(value) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM catalogue_titles WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name IS ? AND language_source IS NULL AND language_source_url IS NULL)";
const FWD_UPDATE="UPDATE catalogue_titles SET language_name=?,language_source=?,language_source_url=? WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name IS ? AND language_source IS NULL AND language_source_url IS NULL";
const REV_GUARD="INSERT INTO qa_guard(value) SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM catalogue_titles WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name=? AND language_source=? AND language_source_url=?)";
const REV_UPDATE="UPDATE catalogue_titles SET language_name=?,language_source=NULL,language_source_url=NULL WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name=? AND language_source=? AND language_source_url=?";
const ROWS="SELECT * FROM catalogue_titles ORDER BY wikidata_qid";
function require(x,m){assert.ok(x,m);}
function oldParams(row){return FIELDS.map(k=>row.before[k]);}
function sourceUrl(row){return "https://www.wikidata.org/wiki/"+row.before.wikidata_qid;}
function options(persist){return convertV4MiniflareOptions({
 modules:true,compatibilityDate:"2026-09-16",
 script:'export default {fetch(){return new Response("local QA only")}}',
 d1Databases:{DB:"00000000-0000-4000-8000-000000000017"},
 resourcePersistencePath:persist
});}
function checkInput(x){
 require(x?.schema==="data-foundation-v2-local-d1-input-v1","Invalid fixture schema");
 require(x.db_reads_this_run===0 && x.production_writes===0,"Production operations not allowed");
 require(x.eligible.length===17 && x.held.length===3 && x.original.length===20,"Unexpected 17/3/20 input");
 require(new Set(x.original.map(y=>y.wikidata_qid)).size===20,"Duplicate film QIDs");
 require([...HELD].every(q=>x.held.some(y=>y.before.wikidata_qid===q)),"Held identity escaped");
}
async function rows(db){return (await db.prepare(ROWS).all()).results;}
async function one(db,sql,...params){
 const r=await db.prepare(sql).bind(...params).run();
 require(r.meta?.changes===1,"Expected one local row change");
}
function statements(db,items,reverse=false){
 const input=reverse?[...items].reverse():items;
 return input.flatMap(item=>{
   const old=oldParams(item), core=old.slice(0,5);
   return reverse?[
     db.prepare(REV_GUARD).bind(...core,item.after,SOURCE,sourceUrl(item)),
     db.prepare(REV_UPDATE).bind(item.before.language_name,...core,item.after,SOURCE,sourceUrl(item))
   ]:[
     db.prepare(FWD_GUARD).bind(...old),
     db.prepare(FWD_UPDATE).bind(item.after,SOURCE,sourceUrl(item),...old)
   ];
 });
}
async function batch(db,items,reverse=false){
 const results=await db.batch(statements(db,items,reverse));
 require(results.length===34,"Incomplete D1 batch response");
 for(let i=1;i<results.length;i+=2)
   require(results[i].meta?.changes===1,"Expected one changed row per D1 update");
}
async function applySchemaMigration(db,path){
 // D1 exec() interprets comment-only lines as empty SQL statements.
 // These migration files contain ordinary CREATE/ALTER/INDEX commands;
 // discard whole-line "--" comments, then execute each statement safely.
 const sql=readFileSync(path,"utf8").split("\n")
   .filter(line=>!line.trimStart().startsWith("--")).join("\n");
 const commands=sql.split(";").map(x=>x.trim()).filter(Boolean);
 require(commands.length>0,"Empty local catalogue migration: "+path);
 for(const command of commands){
   require(/^(CREATE|ALTER)\s/i.test(command),"Unexpected migration command");
   await db.prepare(command).run();
 }
}
async function seed(db,original){
 await applySchemaMigration(db,"migrations/0017_year_precision_catalogue.sql");
 await applySchemaMigration(db,"migrations/0027_catalogue_title_language_provenance.sql");
 await db.prepare(CHECK_TABLE).run();
 const insert="INSERT INTO catalogue_titles(id,wikidata_qid,title,release_year,country_code,language_name,source_category,source_url) VALUES(?,?,?,?,?,?,?,?)";
 for(const r of original)
   await one(db,insert,...FIELDS.map(k=>r[k]),"foundation-local-qa","https://www.wikidata.org/wiki/"+r.wikidata_qid);
 await one(db,insert,"unrelated-qa","Q999999999","Unrelated sentinel film",1975,"IN","Tamil",
           "foundation-local-qa","https://www.wikidata.org/wiki/Q999999999");
}
function equal(a,b,label){assert.deepEqual(a,b,label);}
async function main(){
 require(process.argv.length===4,"Expected fixture and output JSON paths");
 const input=JSON.parse(readFileSync(process.argv[2],"utf8"));
 checkInput(input);
 const folder=mkdtempSync(join(tmpdir(),"foundation-v2-d1-"));
 const persist=join(folder,"state");
 let mf;
 try{
   mf=new Miniflare(options(persist));
   const db=await mf.getD1Database("DB");
   await seed(db,input.original);
   const before=await rows(db);
   require(before.length===21,"Wrong local D1 seed count");
   const byQid=new Map(before.map(x=>[x.wikidata_qid,x]));
   require(input.original.every(row=>FIELDS.every(k=>byQid.get(row.wikidata_qid)?.[k]===row[k])),
           "Local D1 seed lost saved production before-values");

   await batch(db,input.eligible);
   const after=await rows(db), indexed=new Map(after.map(x=>[x.wikidata_qid,x]));
   require(after.length===21,"Unexpected row count after changes");
   require(input.eligible.every(item=>{
     const value=indexed.get(item.before.wikidata_qid);
     return value?.language_name===item.after && value?.language_source===SOURCE
            && value?.language_source_url===sourceUrl(item);
   }),"Local D1 did not update all 17 languages and provenance");
   require(input.held.every(item=>indexed.get(item.before.wikidata_qid)?.language_name==="Unknown"),
           "Held film modified");
   equal(before.filter(r=>HELD.has(r.wikidata_qid)||r.wikidata_qid==="Q999999999"),
         after.filter(r=>HELD.has(r.wikidata_qid)||r.wikidata_qid==="Q999999999"),
         "Held or unrelated records changed");
   await batch(db,input.eligible,true);
   equal(await rows(db),before,"Inverse did not restore all original D1 fields");

   // Stale last row: SQL CHECK guard must fail and rollback previous 16.
   const last=input.eligible.at(-1);
   await one(db,"UPDATE catalogue_titles SET language_name='Concurrent edit' WHERE wikidata_qid=?",
             last.before.wikidata_qid);
   const staleBefore=await rows(db);
   let staleRejected=false;
   try{await batch(db,input.eligible);}catch{staleRejected=true;}
   require(staleRejected,"D1 failed to reject stale batch");
   equal(await rows(db),staleBefore,"D1 failed to atomically rollback stale batch");
   await one(db,"UPDATE catalogue_titles SET language_name='Unknown' WHERE wikidata_qid=?",
             last.before.wikidata_qid);

   // Intervening edit during rollback: inverse must also abort atomically.
   await batch(db,input.eligible);
   await one(db,"UPDATE catalogue_titles SET language_name='Newer edit' WHERE wikidata_qid=?",
             input.eligible[0].before.wikidata_qid);
   const tampered=await rows(db);
   let inverseRejected=false;
   try{await batch(db,input.eligible,true);}catch{inverseRejected=true;}
   require(inverseRejected,"D1 failed to reject competing edit");
   equal(await rows(db),tampered,"D1 inverse overwrote newer edit");
   await mf.dispose();mf=undefined;

   mf=new Miniflare(options(persist));
   const reopened=await mf.getD1Database("DB");
   equal(await rows(reopened),tampered,"Local D1 did not persist unchanged rejected state");
   await mf.dispose();mf=undefined;

   const report={
     schema:"data-foundation-v2-local-d1-rehearsal-v1",
     runtime:"miniflare_same_local_D1_runtime_with_catalogue_schema_0017_and_0027",
     reviewed_film_languages:17, held_disputed_films:3,
     local_rows:21, full_original_record_inverse:true,
     held_and_unrelated_unchanged:true,
     stale_forward_batch_atomic:staleRejected,
     newer_edit_inverse_batch_atomic:inverseRejected,
     miniflare_reopen_persists_state:true,
     current_production_d1_schema_fully_mirrored:false,
     cloudflare_remote_d1_rehearsed:false,
     cloudflare_production_writes:0,
     cloudflare_production_reads:0,
     owner_approved_production_write:false,
     notes:"Local D1 emulator only; separate remote staging D1 and complete production backup still untested."
   };
   writeFileSync(process.argv[3],JSON.stringify(report,null,2)+"\n");
   console.log("FOUNDATION_MINIFLARE_D1="+JSON.stringify({
     local_changed:17,held:3,stale_batch_atomic:staleRejected,
     inverse_batch_atomic:inverseRejected,production_writes:0}));
 }finally{
   if(mf)await mf.dispose();
   rmSync(folder,{recursive:true,force:true});
 }
}
await main();
