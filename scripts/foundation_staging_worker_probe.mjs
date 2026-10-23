/**
 * Synthetic nonproduction D1 Worker Binding smoke test only.
 * No Cloudflare route/deploy/cron. Operator must bind exact UUID-verified
 * foundation-v2-qa-* scratch DB; NEVER bind the live database.
 */
import {
  hashOfBatch,applyApprovedBatch,applyApprovedInverseBatch,verifyAppliedBatch
} from "./foundation_d1_guarded_executor.mjs";

const require=(v,msg)=>{if(!v)throw new Error(msg);};
const UUID=/^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$/;
const TABLES=["catalogue_titles","series_titles"];
const APPROVAL_REF="https://github.com/rayadinaveen98-ship-it/cinema-and-series/issues/999999";
export function assertScratchBinding(env){
  require(env?.FOUNDATION_ONLY_MODE==="isolated-nonproduction-D1" &&
    /^foundation-v2-qa-[1-9][0-9]{5,14}-[1-9][0-9]{0,3}$/.test(
      env?.FOUNDATION_STAGE_NAME??""),
    "Refuse anything but a named disposable QA database");
  require(UUID.test(env.FOUNDATION_STAGE_UUID??"") &&
    UUID.test(env.FOUNDATION_PRODUCTION_UUID??"") &&
    env.FOUNDATION_STAGE_UUID.toLowerCase()!==env.FOUNDATION_PRODUCTION_UUID.toLowerCase(),
    "Scratch UUID absent or matches production");
  require(env.DB && typeof env.DB.prepare==="function" &&
    typeof env.DB.batch==="function","Missing actual D1 Worker Binding");
}
function syntheticApproval(items,rollback=false){
  return {
    schema:"foundation-v2-owner-approval-v1",
    approved:true,status:"OWNER_APPROVED_FOR_PRODUCTION",
    database_name:"cinema-and-series",freeze_exception_scope:"language_fields_only",
    exact_batch_sha256:hashOfBatch(items),
    owner_approval_reference:APPROVAL_REF,production_write_enabled:true,
    rollback_approved:rollback,rollback_batch_sha256:hashOfBatch(items)
  };
}
// Synthetic approval exists ONLY inside this scratch-gated test Worker.
// It never constitutes real owner authorization or a production runner.
const qaIdentity=(table,i)=>({
  id:"foundation-d1-probe-"+table+"-"+i,
  qid:"Q"+(table==="catalogue_titles"?987650000+i:987660000+i),
  title:"Foundation QA "+table+" "+i
});
async function seed(db,table){
  const ids=[];
  for(let i=1;i<=4;i++){
    const {id,qid,title}=qaIdentity(table,i);
    const keys=["id","wikidata_qid","title","language_name",
      "country_code","source_category","source_url",
      table==="catalogue_titles"?"release_year":"first_air_year"];
    const values=[id,qid,title,i===4?"Tamil":"Unknown","IN",
      "qa-disposable-only","https://www.wikidata.org/wiki/"+qid,2018];
    const sql="INSERT INTO "+table+" ("+keys.join(",")+
      ") VALUES ("+keys.map(()=>"?").join(",")+")";
    const result=await db.prepare(sql).bind(...values).run();
    require(result?.success===true && result.meta?.changes===1,
      "Scratch seed failed");
    ids.push({id,qid});
  }
  return ids;
}
async function readRows(db,table,ids){
  const rows=[];
  for(const {id,qid} of ids){
    const row=await db.prepare("SELECT * FROM "+table+
      " WHERE id=? AND wikidata_qid=?").bind(id,qid).first();
    require(row?.id===id && row?.wikidata_qid===qid,"Scratch identity missing");
    rows.push(row);
  }
  return rows;
}
function itemsFor(table,rows){
  return rows.slice(0,3).map(row=>({
    table,row,qid:row.wikidata_qid,proposed_language:"Telugu",
    evidence_url:"https://www.wikidata.org/wiki/"+row.wikidata_qid
  }));
}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export async function probeActualBinding(env){
  assertScratchBinding(env);
  const db=env.DB;
  // This marker exists ONLY in a newly created staging database. A malicious
  // or accidental production D1 binding lacks it and fails before any insert.
  const marker=await db.prepare(
    "SELECT stage_name,stage_uuid,access_nonce FROM foundation_v2_stage_proof "+
    "WHERE id=1"
  ).first();
  require(marker?.stage_name===env.FOUNDATION_STAGE_NAME &&
    marker?.stage_uuid?.toLowerCase()===
      env.FOUNDATION_STAGE_UUID?.toLowerCase() &&
    marker?.access_nonce===env.FOUNDATION_EPHEMERAL_TOKEN,
    "Actual bound database has not proved disposable QA identity");
  const snapshots={};
  for(const table of TABLES){
    const ids=await seed(db,table);
    snapshots[table]={ids,before:await readRows(db,table,ids)};
  }
  for(const table of TABLES){
    const snap=snapshots[table],items=itemsFor(table,snap.before);
    const outcome=await applyApprovedBatch(db,items,syntheticApproval(items));
    require(outcome.changed===3 && outcome.verified_after_count===3,
      "Worker Binding forward failed");
    const after=await verifyAppliedBatch(db,items);
    const inverse=await applyApprovedInverseBatch(
      db,items,after.after,syntheticApproval(items,true));
    require(inverse.restored===3 &&
      same(await readRows(db,table,snap.ids),snap.before),
      "Exact Worker Binding inverse failed");
  }
  const film=snapshots.catalogue_titles;
  const filmItems=itemsFor("catalogue_titles",film.before);
  const stale=filmItems.at(-1);
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind("Another QA editor",stale.row.id).run();
  const prior=await readRows(db,"catalogue_titles",film.ids);
  let staleRejected=false;
  try{await applyApprovedBatch(db,filmItems,syntheticApproval(filmItems));}
  catch{staleRejected=true;}
  require(staleRejected && same(await readRows(db,"catalogue_titles",film.ids),prior),
    "Stale last film failed atomic rollback");
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind(stale.row.title,stale.row.id).run();

  const series=snapshots.series_titles;
  const seriesItems=itemsFor("series_titles",series.before);
  await applyApprovedBatch(db,seriesItems,syntheticApproval(seriesItems));
  const post=await verifyAppliedBatch(db,seriesItems);
  const conflict=seriesItems.at(-1);
  await db.prepare("UPDATE series_titles SET title=? WHERE id=?")
    .bind("Independent QA editor",conflict.row.id).run();
  const current=await readRows(db,"series_titles",series.ids);
  let conflictRejected=false;
  try{
    await applyApprovedInverseBatch(
      db,seriesItems,post.after,syntheticApproval(seriesItems,true));
  }catch{conflictRejected=true;}
  require(conflictRejected &&
    same(await readRows(db,"series_titles",series.ids),current),
    "Competing edit failed inverse atomicity");
  await db.prepare("UPDATE series_titles SET title=? WHERE id=?")
    .bind(conflict.row.title,conflict.row.id).run();
  const corrected=await verifyAppliedBatch(db,seriesItems);
  await applyApprovedInverseBatch(
    db,seriesItems,corrected.after,syntheticApproval(seriesItems,true));
  for(const table of TABLES){
    const snap=snapshots[table];
    require(same(await readRows(db,table,snap.ids),snap.before),
      "QA scratch did not return to exact starting state");
  }
  return {
    schema:"foundation-v2-worker-binding-scratch-probe-v1",
    actual_worker_d1_batch_forward_inverse:true,
    film_language_rows_tested:3,series_language_rows_tested:3,
    original_rows_fully_restored:true,
    stale_last_row_atomic_abort:true,
    competing_edit_inverse_atomic_abort:true,
    unrelated_sentinel_untouched:true,
    production_database_queries:0,production_database_writes:0,
    synthetic_scratch_records:8,production_corrections_authorized:false
  };
}
export default {
  async fetch(request,env){
    try{
      if(request.method!=="POST" ||
         new URL(request.url).pathname!=="/__foundation_staging_probe" ||
         !env.FOUNDATION_EPHEMERAL_TOKEN ||
         request.headers.get("x-foundation-ephemeral-token") !==
           env.FOUNDATION_EPHEMERAL_TOKEN){
        return Response.json({error:"not_found"},{status:404});
      }
      assertScratchBinding(env);
      return Response.json(await probeActualBinding(env));
    }catch{
      // NEVER disclose SQL errors, row values, UUIDs or secret tokens.
      return Response.json({error:"staging_probe_rejected_or_failed"},
        {status:409});
    }
  }
};
