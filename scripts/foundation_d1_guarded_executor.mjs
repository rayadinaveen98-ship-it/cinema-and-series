/**
 * Data Foundation V2 — guarded D1 correction primitive.
 *
 * NOT a Worker, not a deployment, not reachable by HTTP/cron. No production
 * binding here. A separately approved, protected future operation must pass
 * an env.DB handle explicitly AND a locked approval record.
 *
 * One D1Database.batch() == one atomic 1..100-row transaction.
 * Each row gets an all-original-columns SELECT abort guard followed by an
 * equally guarded UPDATE. On ANY stale input, malformed guard fails and the
 * entire D1 batch is rolled back. No schema changes, imports or migrations.
 */
import {createHash} from "node:crypto";

const ALLOWED_COLUMNS=Object.freeze({
  catalogue_titles:new Set([
    "id","wikidata_qid","wikipedia_page_id","title","release_year",
    "date_precision","language_name","country_code","source_category",
    "source_url","verification_status","created_at","updated_at",
    "language_source","language_source_url"
  ]),
  series_titles:new Set([
    "id","wikidata_qid","wikipedia_page_id","title","native_title",
    "series_kind","language_name","country_code","first_air_year",
    "last_air_year","lifecycle_status","season_count","episode_count",
    "source_category","source_url","verification_status","created_at",
    "updated_at","language_source","language_source_url",
    "first_air_year_source","first_air_year_source_url"
  ])
});
const BLOCKED=new Set(["Q20967570","Q20649744","Q109519684"]);
const LANG_UNKNOWN=new Set(["","unknown","xx","und","n/a","na","none","null"]);
const QID=/^Q[1-9][0-9]*$/;
const SOURCE="wikidata:P364";
const PLAN_SCHEMA="foundation-v2-owner-approval-v1";

const canonical=value=>JSON.stringify(value,Object.keys(value).sort());
function require(condition,message){if(!condition)throw new Error(message);}
export function hashOfBatch(items) {
  // Order and every original row value are included. Approval is pinned to
  // a full immutable review-plan hash by the future authorized runner.
  return createHash("sha256").update(JSON.stringify(items)).digest("hex");
}
export function checkRows(items,{limit=100}={}) {
  require(Array.isArray(items) && items.length>0 && items.length<=limit && limit<=100,
    "Guarded batch must have 1..100 records");
  const table=items[0]?.table;
  require(Object.hasOwn(ALLOWED_COLUMNS,table),"Only existing film/series tables supported");
  const seen=new Set();
  for(const item of items){
    const row=item?.row;
    require(item?.table===table && row && typeof row==="object" && !Array.isArray(row),
      "Mixed tables or missing complete original row");
    const keys=Object.keys(row);
    require(keys.length>=10 && keys.every(k=>ALLOWED_COLUMNS[table].has(k)),
      "Unexpected or incomplete D1 source row");
    for(const key of ["id","wikidata_qid","title","language_name","language_source",
                      "language_source_url","updated_at"]){
      require(Object.hasOwn(row,key),"Incomplete field-level snapshot: "+key);
    }
    const qid=row.wikidata_qid;
    require(QID.test(qid) && item.qid===qid && !BLOCKED.has(qid) && !seen.has(qid),
      "Held, duplicate or mismatched film/series QID");
    seen.add(qid);
    require(typeof row.id==="string" && row.id.length>0 &&
      typeof row.title==="string" && row.title.length>0,"Invalid original identity");
    require(LANG_UNKNOWN.has(String(row.language_name??"").trim().toLowerCase()) &&
      (row.language_source===null || row.language_source==="") &&
      (row.language_source_url===null || row.language_source_url===""),
      "Known language or existing provenance cannot be overwritten");
    require(typeof item.proposed_language==="string" &&
      !LANG_UNKNOWN.has(item.proposed_language.trim().toLowerCase()) &&
      item.proposed_language.trim().length>0,"Invalid proposed language");
    require(item.evidence_url==="https://www.wikidata.org/wiki/"+qid,
      "Unverified source URL");
    if(table==="catalogue_titles"){
      require(Number.isInteger(row.release_year) && row.country_code==="IN",
        "Film identity country/release year drift");
    }else{
      require(Object.hasOwn(row,"first_air_year"),
        "Series first-air-year missing in original snapshot");
    }
  }
  return table;
}

function guard(item){
  const row=item.row;
  const table=item.table;
  const keys=Object.keys(row).sort();
  const condition=keys.map(k=>k+" IS ?").join(" AND ");
  const values=keys.map(k=>row[k]);
  // SQLITE JSON1 intentionally throws on invalid JSON ONLY when the original
  // row has changed: CASE is lazy, so a valid row completes without error.
  const guardSQL="SELECT CASE WHEN EXISTS (SELECT 1 FROM "+table+
    " WHERE "+condition+") THEN 1 ELSE json_extract('foundation_guard_abort','$') END AS ok";
  const updateSQL="UPDATE "+table+
    " SET language_name=?,language_source=?,language_source_url=?,"+
    "updated_at=CURRENT_TIMESTAMP WHERE "+condition;
  return {guardSQL,updateSQL,values};
}
export function prepareAtomicBatch(db,items){
  checkRows(items);
  require(db && typeof db.prepare==="function" && typeof db.batch==="function",
    "D1 database binding unavailable");
  const statements=[];
  for(const item of items){
    const {guardSQL,updateSQL,values}=guard(item);
    statements.push(db.prepare(guardSQL).bind(...values));
    statements.push(db.prepare(updateSQL).bind(
      item.proposed_language,SOURCE,item.evidence_url,...values
    ));
  }
  return statements;
}

export function validateOwnerApproval(approval,items){
  require(approval?.schema===PLAN_SCHEMA && approval?.approved===true &&
    approval?.status==="OWNER_APPROVED_FOR_PRODUCTION" &&
    approval?.database_name==="cinema-and-series" &&
    approval?.freeze_exception_scope==="language_fields_only" &&
    approval?.exact_batch_sha256===hashOfBatch(items) &&
    typeof approval?.owner_approval_reference==="string" &&
    /^https:\/\/github\.com\/rayadinaveen98-ship-it\/cinema-and-series\/issues\/[0-9]+$/.test(
      approval.owner_approval_reference
    ),"Explicit, exact-batch owner authorization is required");
  require(approval.production_write_enabled===true,
    "Production write switch is disabled");
}
/**
 * Called ONLY from a separately protected future production operation, not
 * from this repository's existing CI. Never use a timestamp-only approval.
 */
export async function applyApprovedBatch(db,items,approval){
  checkRows(items);
  validateOwnerApproval(approval,items);
  const statements=prepareAtomicBatch(db,items);
  const result=await db.batch(statements);
  require(Array.isArray(result) && result.length===items.length*2,
    "D1 returned an unexpected batch result length");
  for(let i=0;i<items.length;i++){
    require(result[i*2]?.success===true && result[i*2+1]?.success===true &&
      result[i*2+1]?.meta?.changes===1,
      "D1 changed row-count mismatch: verify before any retry");
  }
  // This fresh read happens AFTER the atomic transaction. Never auto-retry a
  // write whose outcome is uncertain; reconcile against the encrypted backup.
  const verification=await verifyAppliedBatch(db,items);
  return {
    schema:"foundation-v2-atomic-approval-batch-result-v1",
    database:"cinema-and-series",table:items[0].table,
    changed:items.length,verified_after_count:verification.verified,
    after_state_sha256:verification.after_sha256,
    batch_sha256:hashOfBatch(items),
    owner_approval_reference:approval.owner_approval_reference,
    rollback_supported_by_sealed_snapshot:true
  };
}

function valuesEqual(a,b){return a===b || (a==null && b==null);}
function matchedNonLanguage(original,after){
  const mutable=new Set(["language_name","language_source","language_source_url","updated_at"]);
  return Object.keys(original).every(k=>mutable.has(k)||valuesEqual(original[k],after[k])) &&
    Object.keys(original).length===Object.keys(after).length &&
    Object.keys(original).every(k=>Object.hasOwn(after,k));
}
function verifyAppliedRow(item,row){
  const original=item.row;
  require(row && matchedNonLanguage(original,row),"Unrelated column changed in post-write verification");
  require(row.id===original.id && row.wikidata_qid===original.wikidata_qid &&
    row.language_name===item.proposed_language &&
    row.language_source===SOURCE && row.language_source_url===item.evidence_url,
    "Post-write value/source verification failed");
}
/** Independent current-state SELECT verification: never retry writes on failure. */
export async function verifyAppliedBatch(db,items){
  checkRows(items);
  const after=[];
  for(const item of items){
    const result=await db.prepare("SELECT * FROM "+item.table+
      " WHERE id=? AND wikidata_qid=?").bind(item.row.id,item.qid).first();
    verifyAppliedRow(item,result);
    after.push(result);
  }
  return {verified:after.length,
    after_sha256:createHash("sha256").update(JSON.stringify(after)).digest("hex"),
    after};
}
/**
 * Restore exactly the four language/provenance/timestamp fields. A later,
 * unrelated edit to ANY column blocks the full inverse transaction.
 */
export async function applyApprovedInverseBatch(db,originalItems,afterRows,approval){
  checkRows(originalItems);
  validateOwnerApproval(approval,originalItems);
  require(approval.rollback_approved===true &&
    approval.rollback_batch_sha256===hashOfBatch(originalItems),
    "Separate, exact rollback approval is mandatory");
  require(Array.isArray(afterRows) && afterRows.length===originalItems.length,
    "Missing verified post-write state for inverse");
  const statements=[];
  for(let i=0;i<originalItems.length;i++){
    const item=originalItems[i],row=afterRows[i];
    verifyAppliedRow(item,row);
    const columns=Object.keys(row).sort();
    const expected=columns.map(c=>row[c]);
    const where=columns.map(c=>c+" IS ?").join(" AND ");
    statements.push(db.prepare(
      "SELECT CASE WHEN EXISTS (SELECT 1 FROM "+item.table+" WHERE "+where+
      ") THEN 1 ELSE json_extract('foundation_inverse_guard_abort','
) END AS ok"
    ).bind(...expected));
    statements.push(db.prepare(
      "UPDATE "+item.table+
      " SET language_name=?,language_source=?,language_source_url=?,updated_at=?"+
      " WHERE "+where
    ).bind(item.row.language_name,item.row.language_source,
           item.row.language_source_url,item.row.updated_at,...expected));
  }
  const results=await db.batch(statements);
  require(Array.isArray(results) && results.length===originalItems.length*2 &&
    results.every((x,i)=>x.success===true && (i%2===0 || x.meta?.changes===1)),
    "D1 inverse changes mismatch; inspect before any retry");
  for(const item of originalItems){
    const restored=await db.prepare("SELECT * FROM "+item.table+
      " WHERE id=? AND wikidata_qid=?").bind(item.row.id,item.qid).first();
    require(restored && Object.keys(item.row).every(k=>valuesEqual(item.row[k],restored[k])) &&
      Object.keys(restored).length===Object.keys(item.row).length,
      "Exact original full-row recovery verification failed");
  }
  return {
    schema:"foundation-v2-atomic-rollback-batch-result-v1",
    restored:originalItems.length,
    batch_sha256:hashOfBatch(originalItems),
    production_rollback_approved:true,
    approval_reference:approval.owner_approval_reference,
    unrelated_fields_unchanged:true
  };
}
