#!/usr/bin/env node
/** Build owner-review manifest from a PRIVATELY decrypted recovery snapshot.
 * No Cloudflare network access, SQL execution, production credentials or writes.
 * Only hashes/counts make it into the downloadable artifact.
 */
import {readFileSync,writeFileSync,mkdirSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {pathToFileURL} from "node:url";
import {createHash} from "node:crypto";
import {checkRows,hashOfBatch} from "./foundation_d1_guarded_executor.mjs";

const require=(ok,msg)=>{if(!ok)throw new Error(msg)};
function manifest(snapshot,{batchSize=100}={}){
  require(snapshot?.schema==="foundation-v2-full-row-recovery-v1" &&
    snapshot.production_database==="cinema-and-series" &&
    snapshot.production_writes===0 && snapshot.ready_to_apply===false &&
    Array.isArray(snapshot.full_rows) && snapshot.full_rows.length===16681 &&
    Array.isArray(snapshot.drift_issues) && snapshot.drift_issues.length===0,
    "Expected complete, zero-drift authenticated recovery snapshot");
  require(Number.isInteger(batchSize) && batchSize>=1 && batchSize<=100,
    "Unsafe batch size");
  const batches=[];
  const tables=[["catalogue_titles",11667],["series_titles",5014]];
  let index=0;
  for(const [table,expected] of tables){
    const items=snapshot.full_rows.filter(r=>r.table===table)
      .sort((a,b)=>a.qid.localeCompare(b.qid));
    require(items.length===expected,"Correction set changed from 11667/5014");
    for(let offset=0;offset<items.length;offset+=batchSize){
      const group=items.slice(offset,offset+batchSize);
      require(checkRows(group)===table,"Prepared D1 exact snapshot failed validation");
      batches.push({
        number:++index,table,records:group.length,
        original_and_proposed_rows_sha256:hashOfBatch(group),
        production_write_performed:false,
      });
    }
  }
  require(batches.length===168 && batches.reduce((a,b)=>a+b.records,0)===16681,
    "Full 168-batch correction coverage changed");
  const planSha=createHash("sha256").update(
    JSON.stringify(batches.map(b=>[b.number,b.table,b.records,
      b.original_and_proposed_rows_sha256]))).digest("hex");
  return {
    schema:"foundation-v2-owner-approval-manifest-v1",
    source_encrypted_recovery_run:39935377448,
    independent_recovery_proof_run:39935974111,
    whole_catalogue_existing_titles:70175,
    reviewed_existing_films:11667,
    reviewed_existing_series:5014,
    total_language_corrections_requested:16681,
    batch_size_limit:batchSize,
    total_batches:168,
    manifest_sha256:planSha,
    batches,
    source_evidence:"Wikidata P364 original-language claim; not independently studio-confirmed",
    production_approval_granted:false,
    production_write_switch_enabled:false,
    production_reads:0,production_writes:0,
    further_requirements:[
      "Owner explicitly approves THIS manifest SHA-256 and exact 168 batches",
      "Protected execution deployable restricted to expected production D1 database UUID",
      "Take fresh encrypted full-row backup and Time Travel bookmark immediately before start",
      "Every atomic D1.batch enforces full-column freshness and is verified after commit",
      "Never auto-retry indeterminate network responses; reconcile and resume idempotently",
      "Keep production ingress and poster jobs frozen until independent quality audit passes",
    ],
  };
}
export {manifest};

const args=process.argv.slice(2);
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  require(args.length===2,"Expected private input JSON and public-safe output path");
  const snapshot=JSON.parse(readFileSync(args[0],"utf8"));
  const result=manifest(snapshot);
  mkdirSync(dirname(args[1]),{recursive:true});
  writeFileSync(args[1],JSON.stringify(result,null,2)+"\n","utf8");
  console.log("FOUNDATION_OWNER_APPROVAL_MANIFEST="+JSON.stringify({
    corrections:result.total_language_corrections_requested,
    batches:result.total_batches,manifest_sha256:result.manifest_sha256,
    production_writes:0,approved:false,
  }));
}
