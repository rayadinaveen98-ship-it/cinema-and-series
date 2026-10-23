/**
 * Isolated staged Worker Binding D1 canary.
 * Six small authenticated HTTP invocations, NEVER one long Free-tier request.
 * Scratch-only UUID + database-resident nonce proof required for every phase.
 * A phase can never be replayed or skipped; uncertain remote writes are NEVER
 * retried. Production D1 is never bound, deployed or queried here.
 */
import {
  hashOfBatch,applyApprovedBatch,applyApprovedInverseBatch,verifyAppliedBatch
} from "./foundation_d1_guarded_executor.mjs";
const require=(ok,msg)=>{if(!ok)throw new Error(msg);};
const UUID=/^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$/;
const TABLES=["catalogue_titles","series_titles"];
const PHASES=["seed","film","series","stale","conflict","finish"];
const APPROVAL_REF="https://github.com/rayadinaveen98-ship-it/cinema-and-series/issues/999999";
export function assertScratchBinding(env){
  require(env?.FOUNDATION_ONLY_MODE==="isolated-nonproduction-D1" &&
    /^foundation-v2-qa-[1-9][0-9]{5,14}-[1-9][0-9]{0,3}$/.test(
      env?.FOUNDATION_STAGE_NAME??""),
    "Refuse non-scratch database names");
  require(UUID.test(env.FOUNDATION_STAGE_UUID??"") &&
    UUID.test(env.FOUNDATION_PRODUCTION_UUID??"") &&
    env.FOUNDATION_STAGE_UUID.toLowerCase()!==env.FOUNDATION_PRODUCTION_UUID.toLowerCase(),
    "Scratch UUID absent or matches production");
  require(env.DB && typeof env.DB.prepare==="function" &&
    typeof env.DB.batch==="function","Missing D1 Worker Binding");
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
// Synthetic grant valid only in SCRATCH proof-gated probe; NEVER production.
const qaIdentity=(table,i)=>({
  id:"foundation-d1-probe-"+table+"-"+i,
  qid:"Q"+(table==="catalogue_titles"?987650000+i:987660000+i),
  title:"Foundation QA "+table+" "+i
});
async function seed(db,table){
  for(let i=1;i<=4;i++){
    const {id,qid,title}=qaIdentity(table,i);
    const columns=["id","wikidata_qid","title","language_name",
      "country_code","source_category","source_url",
      table==="catalogue_titles"?"release_year":"first_air_year"];
    const params=[id,qid,title,i===4?"Tamil":"Unknown","IN",
      "qa-disposable-only","https://www.wikidata.org/wiki/"+qid,2018];
    const sql="INSERT INTO "+table+" ("+columns.join(",")+
      ") VALUES ("+columns.map(()=>"?").join(",")+")";
    const result=await db.prepare(sql).bind(...params).run();
    require(result?.success===true && result.meta?.changes===1,
      "Scratch fixture seed did not insert one expected record");
  }
}
async function readRows(db,table){
  const results=[];
  for(let i=1;i<=4;i++){
    const {id,qid}=qaIdentity(table,i);
    const row=await db.prepare("SELECT * FROM "+table+
      " WHERE id=? AND wikidata_qid=?").bind(id,qid).first();
    require(row?.id===id && row?.wikidata_qid===qid,
      "Missing isolated scratch fixture identity");
    results.push(row);
  }
  return results;
}
function itemsFor(table,rows){
  return rows.slice(0,3).map(row=>({
    table,row,qid:row.wikidata_qid,proposed_language:"Telugu",
    evidence_url:"https://www.wikidata.org/wiki/"+row.wikidata_qid
  }));
}
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
async function roundtrip(db,table){
  const original=await readRows(db,table);
  const items=itemsFor(table,original);
  const forward=await applyApprovedBatch(db,items,syntheticApproval(items));
  require(forward.changed===3 && forward.verified_after_count===3,
    "Forward scratch transaction changed unexpected records");
  const applied=await verifyAppliedBatch(db,items);
  const inverse=await applyApprovedInverseBatch(
    db,items,applied.after,syntheticApproval(items,true));
  require(inverse.restored===3 && same(await readRows(db,table),original),
    "Exact scratch inverse failed");
}
async function staleCase(db){
  const original=await readRows(db,"catalogue_titles");
  const items=itemsFor("catalogue_titles",original);
  const last=items.at(-1);
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind("Independent scratch edit",last.row.id).run();
  const changed=await readRows(db,"catalogue_titles");
  let rejected=false;
  try{await applyApprovedBatch(db,items,syntheticApproval(items));}
  catch{rejected=true;}
  require(rejected && same(await readRows(db,"catalogue_titles"),changed),
    "Stale final row failed atomic transaction rollback");
  await db.prepare("UPDATE catalogue_titles SET title=? WHERE id=?")
    .bind(last.row.title,last.row.id).run();
  require(same(await readRows(db,"catalogue_titles"),original),
    "Scratch conflict cleanup failed");
}
async function competingEditCase(db){
  const original=await readRows(db,"series_titles");
  const items=itemsFor("series_titles",original);
  await applyApprovedBatch(db,items,syntheticApproval(items));
  const post=await verifyAppliedBatch(db,items);
  const last=items.at(-1);
  await db.prepare("UPDATE series_titles SET title=? WHERE id=?")
    .bind("Competing scratch edit",last.row.id).run();
  const edited=await readRows(db,"series_titles");
  let rejected=false;
  try{await applyApprovedInverseBatch(
    db,items,post.after,syntheticApproval(items,true));
  }catch{rejected=true;}
  require(rejected && same(await readRows(db,"series_titles"),edited),
    "Conflicted inverse failed full rollback");
  await db.prepare("UPDATE series_titles SET title=? WHERE id=?")
    .bind(last.row.title,last.row.id).run();
  const actual=await verifyAppliedBatch(db,items);
  await applyApprovedInverseBatch(
    db,items,actual.after,syntheticApproval(items,true));
  require(same(await readRows(db,"series_titles"),original),
    "Scratch competing-edit case did not fully restore");
}
async function finalCheck(db){
  for(const table of TABLES){
    const rows=await readRows(db,table);
    require(rows.length===4 &&
      rows.slice(0,3).every(row=>
        row.language_name==="Unknown" &&
        row.language_source==null && row.language_source_url==null) &&
      rows[3].language_name==="Tamil" &&
      rows[3].language_source==null && rows[3].language_source_url==null,
      "Scratch QA original language/provenance not restored");
    const count=await db.prepare("SELECT count(*) AS n FROM "+table).first();
    require(count?.n===4,"Unexpected row changes in disposable staging table");
  }
}
export async function probeActualBinding(env,phase){
  assertScratchBinding(env);
  require(PHASES.includes(phase),"Unknown synthetic scratch phase");
  const db=env.DB;
  const marker=await db.prepare(
    "SELECT stage_name,stage_uuid,access_nonce,stage_phase "+
    "FROM foundation_v2_stage_proof WHERE id=1"
  ).first();
  require(marker?.stage_name===env.FOUNDATION_STAGE_NAME &&
    marker?.stage_uuid?.toLowerCase()===env.FOUNDATION_STAGE_UUID?.toLowerCase() &&
    marker?.access_nonce===env.FOUNDATION_EPHEMERAL_TOKEN,
    "Bound DB did not prove ephemeral scratch identity");
  const index=PHASES.indexOf(phase);
  const before=index===0?"new":PHASES[index-1];
  require(marker.stage_phase===before,"Scratch phase replay or order violation");
  if(phase==="seed"){
    for(const table of TABLES)await seed(db,table);
  }else if(phase==="film" || phase==="series"){
    await roundtrip(db,phase==="film"?"catalogue_titles":"series_titles");
  }else if(phase==="stale"){
    await staleCase(db);
  }else if(phase==="conflict"){
    await competingEditCase(db);
  }else if(phase==="finish"){
    await finalCheck(db);
  }
  const result=await db.prepare(
    "UPDATE foundation_v2_stage_proof SET stage_phase=? "+
    "WHERE id=1 AND stage_phase=? AND stage_uuid=? AND access_nonce=?"
  ).bind(phase,before,env.FOUNDATION_STAGE_UUID,env.FOUNDATION_EPHEMERAL_TOKEN).run();
  require(result?.success===true && result?.meta?.changes===1,
    "Scratch phase checkpoint failed; stop without retry");
  return {
    schema:"foundation-v2-worker-binding-scratch-probe-v2",
    phase,phase_passed:true,
    stage_completed:phase==="finish",
    production_database_queries:0,
    production_database_writes:0,
    production_corrections_authorized:false,
    ...(phase==="finish"?{
      actual_worker_d1_batch_forward_inverse:true,
      film_language_rows_tested:3,series_language_rows_tested:3,
      original_rows_fully_restored:true,
      stale_last_row_atomic_abort:true,
      competing_edit_inverse_atomic_abort:true,
      unrelated_sentinel_untouched:true,
      synthetic_scratch_records:8,
    }:{})
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
      const phase=request.headers.get("x-foundation-probe-phase");
      assertScratchBinding(env);
      return Response.json(await probeActualBinding(env,phase));
    }catch{
      // No SQL strings, rows, UUIDs, access tokens or error stack in response.
      return Response.json({error:"staging_probe_rejected_or_failed"},{status:409});
    }
  }
};
