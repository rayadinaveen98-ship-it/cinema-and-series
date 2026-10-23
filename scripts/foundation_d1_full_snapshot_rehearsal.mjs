#!/usr/bin/env node
/**
 * Full-size, sealed-data D1 rehearsal; strictly LOCAL Miniflare.
 *
 * Input: independently authenticated, ephemeral PRIVATE recovery JSON.
 * Output: counts/hashes/booleans only. Never log or publish row data.
 * No Cloudflare credentials, network calls, deployment or production binding.
 *
 * This tests the actual guarded D1.batch executor on all 168 exact batches.
 * It does NOT substitute for disposable REMOTE D1 staging or owner approval.
 */
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,rmSync} from "node:fs";
import {dirname,join} from "node:path";
import {tmpdir} from "node:os";
import {Miniflare,convertV4MiniflareOptions} from "miniflare";
import {manifest} from "./foundation_d1_approval_manifest.mjs";
import {
  checkRows,hashOfBatch,validateD1SchemaSnapshot,
  applyApprovedBatch,applyApprovedInverseBatch
} from "./foundation_d1_guarded_executor.mjs";

const TABLES=["catalogue_titles","series_titles"];
const MIGRATIONS=[
  "migrations/0017_year_precision_catalogue.sql",
  "migrations/0027_catalogue_title_language_provenance.sql",
  "migrations/0018_series_catalogue.sql",
  "migrations/0019_series_language_provenance.sql",
  "migrations/0020_series_first_air_year_provenance.sql"
];
const reject=(condition,message)=>{if(!condition)throw new Error(message);};
const assertLocal=()=>{
  reject(!process.env.CLOUDFLARE_API_TOKEN && !process.env.CLOUDFLARE_ACCOUNT_ID &&
    !process.env.CLOUDFLARE_D1_TOKEN,
    "Remote Cloudflare credentials forbidden in isolated D1 runner");
};
const mockApproval=items=>({
  schema:"foundation-v2-owner-approval-v1",
  approved:true,status:"OWNER_APPROVED_FOR_PRODUCTION",
  database_name:"cinema-and-series",freeze_exception_scope:"language_fields_only",
  exact_batch_sha256:hashOfBatch(items),
  owner_approval_reference:
    "https://github.com/rayadinaveen98-ship-it/cinema-and-series/issues/999999",
  production_write_enabled:true
}); // SYNTHETIC test grant; no production handle is available.

async function migrate(db){
  for(const file of MIGRATIONS){
    const statements=readFileSync(file,"utf8").split("\n")
      .filter(line=>!line.trimStart().startsWith("--"))
      .join("\n").split(";").map(s=>s.trim()).filter(Boolean);
    for(const sql of statements){
      reject(/^(?:(?:CREATE|ALTER)\s|UPDATE series_titles\s+SET language_source\b)/i.test(sql),
        "Unexpected migration command in local runner");
      await db.prepare(sql).run();
    }
  }
}

function exactBatches(snapshot,review){
  const list=[];
  for(const table of TABLES){
    const ordered=snapshot.full_rows.filter(item=>item.table===table)
      .sort((a,b)=>a.qid.localeCompare(b.qid));
    for(let i=0;i<ordered.length;i+=100){
      const items=ordered.slice(i,i+100);
      checkRows(items);
      const locked=review.batches[list.length];
      reject(locked.table===table && locked.number===list.length+1 &&
        locked.records===items.length &&
        locked.original_and_proposed_rows_sha256===hashOfBatch(items),
        "Snapshot drift from locked 168-batch manifest");
      list.push(items);
    }
  }
  reject(list.length===168,"Incomplete locked batch plan");
  return list;
}

async function seed(db,batches){
  for(const table of TABLES){
    const group=batches.find(items=>items[0].table===table);
    reject(group,"Missing snapshot table");
    await validateD1SchemaSnapshot(db,group);
  }
  for(const items of batches){
    const table=checkRows(items);
    const statements=items.map(({row})=>{
      const keys=Object.keys(row);
      const placeholders=keys.map(()=>"?").join(",");
      return db.prepare("INSERT INTO "+table+" ("+keys.join(",")+
        ") VALUES ("+placeholders+")").bind(...keys.map(k=>row[k]));
    });
    const result=await db.batch(statements);
    reject(Array.isArray(result) && result.length===items.length &&
      result.every(entry=>entry.success===true && entry.meta?.changes===1),
      "Local seed did not insert each exact original record");
  }
  for(const table of TABLES){
    const qid="Q999999999";
    const columns=["id","wikidata_qid","title","language_name",
      "source_category","source_url"];
    const values=["foundation-qa-control-"+table,qid,"Untouched QA control",
      "Tamil","QA","https://www.wikidata.org/wiki/"+qid];
    columns.push(table==="catalogue_titles"?"release_year":"first_air_year");
    values.push(2000);
    await db.prepare("INSERT INTO "+table+" ("+columns.join(",")+
      ") VALUES ("+columns.map(()=>"?").join(",")+")").bind(...values).run();
  }
}

async function selectBatch(db,items){
  const table=checkRows(items);
  const qids=items.map(item=>item.qid);
  return (await db.prepare("SELECT * FROM "+table+" WHERE wikidata_qid IN ("+
    qids.map(()=>"?").join(",")+") ORDER BY wikidata_qid").bind(...qids).all()).results;
}

async function sentinelCheck(db){
  for(const table of TABLES){
    const row=await db.prepare("SELECT * FROM "+table+
      " WHERE id=?").bind("foundation-qa-control-"+table).first();
    reject(row?.language_name==="Tamil" && row.title==="Untouched QA control",
      "Unrelated QA sentinel changed");
  }
}

async function run(db,snapshot){
  const review=manifest(snapshot);
  const groups=exactBatches(snapshot,review);
  await migrate(db);
  await seed(db,groups);
  await sentinelCheck(db);
  const expected={catalogue_titles:11668,series_titles:5015};
  for(const table of TABLES){
    const value=await db.prepare("SELECT count(*) AS n FROM "+table).first();
    reject(value.n===expected[table],"Original staging row count changed");
  }
  const afterGroups=[];
  for(const items of groups){
    const result=await applyApprovedBatch(db,items,mockApproval(items));
    reject(result.changed===items.length &&
      result.verified_after_count===items.length,
      "Full-size guarded forward batch mismatch");
    const after=await selectBatch(db,items);
    const afterIndex=new Map(after.map(row=>[row.wikidata_qid,row]));
    reject(afterIndex.size===items.length,"Missing post-write inverse inputs");
    afterGroups.push(items.map(item=>afterIndex.get(item.qid)));
  }
  await sentinelCheck(db);
  let restored=0;
  for(let i=groups.length-1;i>=0;i--){
    const items=groups[i],approval={
      ...mockApproval(items),rollback_approved:true,
      rollback_batch_sha256:hashOfBatch(items)
    };
    const result=await applyApprovedInverseBatch(db,items,afterGroups[i],approval);
    reject(result.restored===items.length,"Exact 100-row D1 inverse failed");
    restored+=result.restored;
  }
  reject(restored===16681,"Incomplete inverse recovery");
  await sentinelCheck(db);

  // Last-row stale mutation must atomically abort ALL 100 prior changes.
  const film=groups.find(items=>items[0].table==="catalogue_titles");
  const last=film.at(-1);
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind("Independent QA edit",last.row.id).run();
  const beforeStale=await selectBatch(db,film);
  let staleBlocked=false;
  try{await applyApprovedBatch(db,film,mockApproval(film));}
  catch{staleBlocked=true;}
  reject(staleBlocked &&
    JSON.stringify(await selectBatch(db,film))===JSON.stringify(beforeStale),
    "Stale last-row D1 forward failed atomic rollback");
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind(last.row.title,last.row.id).run();

  // A newer series edit must block the FULL guarded inverse.
  const series=groups.find(items=>items[0].table==="series_titles");
  await applyApprovedBatch(db,series,mockApproval(series));
  const actual=await selectBatch(db,series);
  const lookup=new Map(actual.map(row=>[row.wikidata_qid,row]));
  const after=series.map(item=>lookup.get(item.qid));
  const conflict=series.at(-1);
  await db.prepare("UPDATE series_titles SET title=? WHERE id=?")
    .bind("Independent newer QA edit",conflict.row.id).run();
  const beforeConflict=await selectBatch(db,series);
  let rollbackBlocked=false;
  try{
    await applyApprovedInverseBatch(db,series,after,{
      ...mockApproval(series),rollback_approved:true,
      rollback_batch_sha256:hashOfBatch(series)
    });
  }catch{rollbackBlocked=true;}
  reject(rollbackBlocked &&
    JSON.stringify(await selectBatch(db,series))===JSON.stringify(beforeConflict),
    "Newer edit was erased or inverse batch partially committed");
  await sentinelCheck(db);
  return {
    schema:"foundation-v2-full-miniflare-d1-recovery-qa-v1",
    simulation:"isolated Miniflare D1 Worker Binding, real repo migrations",
    source:"AES-GCM authenticated 16,681-row historical snapshot",
    films:11667,series:5014,existing_title_changes_rehearsed:16681,
    atomic_batches:168,max_batch_size:100,
    manifest_sha256:review.manifest_sha256,
    all_forward_batches_verified:true,
    complete_inverse_restored_all_columns:true,
    stale_last_row_atomic_abort:true,
    competing_edit_inverse_atomic_abort:true,
    unrelated_control_records_untouched:true,
    remote_d1_staging_passed:false,
    production_approval_granted:false,
    production_reads:0,production_writes:0,
    evidence_standard:"Wikidata P364; not studio-verified"
  };
}

async function main(){
  reject(process.argv.length===4,"Expected PRIVATE snapshot JSON and SAFE report path");
  assertLocal();
  const freeze=JSON.parse(readFileSync("ops/data-foundation-v2-freeze.json","utf8"));
  reject(freeze.active===true && freeze.baseline.total===70175,
    "Production catalogue freeze/baseline is not active");
  const snapshot=JSON.parse(readFileSync(process.argv[2],"utf8"));
  const dir=mkdtempSync(join(tmpdir(),"foundation-full-d1-"));
  let mf;
  try{
    mf=new Miniflare(convertV4MiniflareOptions({
      modules:true,compatibilityDate:"2026-09-16",
      script:'export default {fetch(){return new Response("local-only")}}',
      d1Databases:{DB:"00000000-0000-4000-8000-000000000099"},
      resourcePersistencePath:join(dir,"persist")
    }));
    const db=await mf.getD1Database("DB");
    const result=await run(db,snapshot);
    mkdirSync(dirname(process.argv[3]),{recursive:true});
    writeFileSync(process.argv[3],JSON.stringify(result,null,2)+"\n","utf8");
    console.log("FOUNDATION_FULL_D1_QA="+JSON.stringify({
      total:result.existing_title_changes_rehearsed,
      batches:result.atomic_batches,exact_inverse:true,
      stale_atomic:true,concurrent_inverse_guard:true,production_writes:0
    }));
  }finally{
    if(mf)await mf.dispose();
    rmSync(dir,{recursive:true,force:true});
  }
}
main().catch(error=>{
  // Never serialize database rows, bound arguments or plaintext exception
  // data to CI logs. A stable diagnostic marker is enough for triage.
  console.error("FOUNDATION_FULL_D1_QA=failed_check_private_runner");
  process.exitCode=1;
});
