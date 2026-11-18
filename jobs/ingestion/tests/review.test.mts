import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import postgres from 'postgres';
import {persistStageBatch} from '../src/persist.ts';
import {applyStageReview,reviewInsideTransaction} from '../src/review.ts';

const url=process.env.STAGING_TEST_DB_URL;
if(!url)throw new Error('STAGING_TEST_DB_URL must be provided');
const parsed=new URL(url);
if(!['127.0.0.1','localhost'].includes(parsed.hostname) || parsed.pathname!=='/cinema_test'){
  throw new Error('Refusing reviewer tests on non-disposable PostgreSQL');
}
const sql=postgres(url,{max:5,ssl:false,prepare:false,connect_timeout:5});
after(async()=>sql.end({timeout:5}));

const candidate=(id:string,name:string)=>({
  type:'movie',
  sourceId:'wikidata:'+id,
  sourceUrl:'https://www.wikidata.org/wiki/'+id,
  originalTitle:name,
  originalLanguages:['te'],
  genres:['drama'],
  releaseEvents:[] as unknown[]
});
async function stage(id:string,batchKey:string){
  const run=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey,records:[candidate(id,'Synthetic Review '+id)]
  });
  const [row]=await sql`
    SELECT id::text AS id,source_record_id::text AS source_id
    FROM staging_records
    WHERE ingestion_run_id=${run.runId}::uuid
  `;
  assert.ok(row);
  return {stageId:String(row.id),sourceId:String(row.source_id)};
}
async function status(stageId:string){
  const [row]=await sql`
    SELECT s.review_status AS stage_status,q.status AS ticket_status,
      q.reviewer_note AS reviewer_note
    FROM staging_records s
    JOIN review_queue q ON q.staging_record_id=s.id
    WHERE s.id=${stageId}::uuid
  `;
  return row;
}
const note='Verified by disposable QA operator with source snapshot reference.';

test('qualification requires actual source snapshot and leaves published tables untouched',async()=>{
  const before=await sql`SELECT (SELECT count(*)::integer FROM titles) AS titles,
    (SELECT count(*)::integer FROM release_events) AS releases`;
  const {stageId,sourceId}=await stage('Q990002001','qualify-proof-1');
  const review={stageId,reviewerCode:'qa_operator_01',decision:'qualify' as const,note};
  await assert.rejects(applyStageReview(sql,review),/SOURCE_SNAPSHOT_REQUIRED/);
  assert.equal((await status(stageId))?.ticket_status,'open');
  // Synthetic fetched evidence is created ONLY inside the disposable PostgreSQL test.
  await sql`UPDATE source_records
    SET retrieved_at=now(),raw_payload=${sql.json({id:'Q990002001',type:'item',lastrevid:7})}::jsonb
    WHERE id=${sourceId}::uuid`;
  const result=await applyStageReview(sql,review);
  assert.deepEqual(result,{stageId,status:'validated',published:false});
  assert.equal((await status(stageId))?.ticket_status,'resolved');
  const afterCounts=await sql`SELECT (SELECT count(*)::integer FROM titles) AS titles,
    (SELECT count(*)::integer FROM release_events) AS releases`;
  assert.deepEqual(afterCounts,before);
  await assert.rejects(applyStageReview(sql,review),/REVIEW_NOT_OPEN/);
});

test('rejecting a staged candidate is final and logged without publishing',async()=>{
  const {stageId}=await stage('Q990002002','review-reject-2');
  const result=await applyStageReview(sql,{
    stageId,reviewerCode:'qa_operator_01',decision:'reject',
    note:'Claim is unsupported by enough independent editorial evidence.'
  });
  assert.equal(result.status,'rejected');
  assert.equal(result.published,false);
  assert.equal((await status(stageId))?.ticket_status,'rejected');
  const [audit]=await sql`SELECT count(*)::integer AS n
    FROM catalogue_audit_log
    WHERE action='stage_quality_decision'
      AND changes->>'stageId'=${stageId}`;
  assert.equal(audit?.n,1);
});

test('quarantined candidates cannot be made valid through review command',async()=>{
  const run=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'rejected-review-3',
    records:[{...candidate('Q990002003','Impossible'),sourceUrl:'https://example.com/bad'}]
  });
  const [row]=await sql`SELECT id::text AS id FROM staging_records
    WHERE ingestion_run_id=${run.runId}::uuid`;
  await assert.rejects(applyStageReview(sql,{
    stageId:String(row!.id),reviewerCode:'qa_operator_01',decision:'qualify',note
  }),/REVIEW_NOT_OPEN/);
});

test('ambiguous title alias remains blocked even with a matching source snapshot',async()=>{
  const [t]=await sql`INSERT INTO titles(title_type,original_title,publication_status)
    VALUES ('movie','Source Name Distinct','published') RETURNING id::text AS id`;
  await sql`INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
    VALUES (${String(t!.id)}::uuid,NULL,'Collision Localized Title','alternative')`;
  const run=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'alias-review-4',
    records:[candidate('Q990002004','Collision Localized Title')]
  });
  const [s]=await sql`SELECT id::text AS id,source_record_id::text AS source_id
    FROM staging_records WHERE ingestion_run_id=${run.runId}::uuid`;
  await sql`UPDATE source_records
    SET retrieved_at=now(),raw_payload=${sql.json({id:'Q990002004',type:'item'})}::jsonb
    WHERE id=${String(s!.source_id)}::uuid`;
  await assert.rejects(applyStageReview(sql,{
    stageId:String(s!.id),reviewerCode:'qa_operator_01',decision:'qualify',note
  }),/IDENTITY_REVIEW_REQUIRED/);
  assert.equal((await status(String(s!.id)))?.stage_status,'pending');
});

test('two concurrent reviewer decisions cannot resolve same ticket twice',async()=>{
  const {stageId}=await stage('Q990002005','review-race-5');
  const cmd={stageId,reviewerCode:'qa_operator_01',decision:'reject' as const,note};
  const results=await Promise.allSettled([
    applyStageReview(sql,cmd),applyStageReview(sql,cmd)
  ]);
  assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
  assert.equal(results.filter(x=>x.status==='rejected').length,1);
  const [audit]=await sql`SELECT count(*)::integer AS n FROM catalogue_audit_log
    WHERE action='stage_quality_decision' AND changes->>'stageId'=${stageId}`;
  assert.equal(audit?.n,1);
});

test('forced error rolls back review decision, ticket status and audit',async()=>{
  const {stageId}=await stage('Q990002006','review-rollback-6');
  const cmd={stageId,reviewerCode:'qa_operator_01',decision:'reject' as const,note};
  await assert.rejects(sql.begin(async tx=>{
    await reviewInsideTransaction(tx,cmd);
    throw new Error('SYNTHETIC_REVIEW_ROLLBACK');
  }),/SYNTHETIC_REVIEW_ROLLBACK/);
  assert.deepEqual({
    stage:(await status(stageId))?.stage_status,
    ticket:(await status(stageId))?.ticket_status
  },{stage:'pending',ticket:'open'});
  const [audit]=await sql`SELECT count(*)::integer AS n FROM catalogue_audit_log
    WHERE action='stage_quality_decision' AND changes->>'stageId'=${stageId}`;
  assert.equal(audit?.n,0);
});

test('review command rejects missing review notes and malformed operator or ID',async()=>{
  for(const bad of [
    {stageId:'bad',reviewerCode:'qa_operator_01',decision:'reject' as const,note},
    {stageId:'00000000-0000-4000-8000-000000000001',reviewerCode:'',decision:'reject' as const,note},
    {stageId:'00000000-0000-4000-8000-000000000001',reviewerCode:'qa_operator_01',decision:'reject' as const,note:'short'}
  ]) {
    await assert.rejects(applyStageReview(sql,bad),/INVALID_REVIEW_COMMAND/);
  }
});
