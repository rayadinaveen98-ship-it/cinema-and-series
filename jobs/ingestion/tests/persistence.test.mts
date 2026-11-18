import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import postgres from 'postgres';
import { persistStageBatch, stageInsideTransaction } from '../src/persist.ts';

const url=process.env.STAGING_TEST_DB_URL;
if(!url) throw new Error('STAGING_TEST_DB_URL required; never use a production database');
const parsed=new URL(url);
if (!['localhost','127.0.0.1'].includes(parsed.hostname) || parsed.pathname!=='/cinema_test') {
  throw new Error('Refusing staging integration test outside disposable local cinema_test');
}
const sql=postgres(url,{max:6,ssl:false,prepare:false,connect_timeout:5});
after(async()=>{await sql.end({timeout:5});});

const fixture=(id:string,title:string,kind='movie')=>({
  sourceId:'wikidata:'+id,
  sourceUrl:'https://www.wikidata.org/wiki/'+id,
  type:kind,originalTitle:title,
  originalLanguages:['te'],genres:['action'],
  releaseEvents:[{
    date:'2020-02-29',kind:'original_premiere',
    verification:'unverified',sourceRecordId:'synthetic-validation-only'
  }]
});

async function persistedCounts(runId:string) {
  const [row]=await sql`
    SELECT
      (SELECT COUNT(*)::integer FROM staging_records WHERE ingestion_run_id=${runId}::uuid) AS staged,
      (SELECT COUNT(*)::integer FROM review_queue WHERE staging_record_id IN (
        SELECT id FROM staging_records WHERE ingestion_run_id=${runId}::uuid
      )) AS reviews
  `;
  return row;
}
test('transactionally writes new candidate, source provenance and one review item',async()=>{
  const before=await sql`SELECT count(*)::integer AS value FROM titles`;
  const request={sourceKey:'wikidata' as const,batchKey:'initial-stage-001',records:[
    fixture('Q880000101','Synthetic Telugu One')
  ]};
  const result=await persistStageBatch(sql,request);
  assert.equal(result.replayed,false);
  assert.equal(result.staged,1);
  assert.equal(result.pendingReview,1);
  assert.equal(result.quarantined,0);
  assert.deepEqual(await persistedCounts(result.runId),{staged:1,reviews:1});
  const shape=await sql`SELECT jsonb_typeof(raw_candidate) AS record_type,
    jsonb_typeof(issue_codes) AS issues_type
    FROM staging_records WHERE ingestion_run_id=${result.runId}::uuid`;
  assert.deepEqual(shape[0],{record_type:'object',issues_type:'array'});

  const [run]=await sql`SELECT run_status,processed_count::integer AS n,
    rejected_count::integer AS rejected FROM ingestion_runs WHERE id=${result.runId}::uuid`;
  assert.deepEqual(run,{run_status:'completed',n:1,rejected:0});
  const afterRows=await sql`SELECT count(*)::integer AS value FROM titles`;
  assert.equal(before[0]?.value,afterRows[0]?.value,'staging must not publish titles');
  const [pointer]=await sql`SELECT retrieved_at FROM source_records
    WHERE source_key='wikidata' AND external_record_id='Q880000101'`;
  assert.equal(pointer?.retrieved_at,null,'unfetched source pointers must not claim a retrieval time');
});

test('replaying same key and payload returns identical run without new rows or audit',async()=>{
  const input={sourceKey:'wikidata' as const,batchKey:'replay-002',records:[
    fixture('Q880000102','Synthetic Replay')
  ]};
  const first=await persistStageBatch(sql,input);
  const second=await persistStageBatch(sql,input);
  assert.equal(first.runId,second.runId);
  assert.equal(second.replayed,true);
  assert.deepEqual(await persistedCounts(first.runId),{staged:1,reviews:1});
  const audits=await sql`SELECT changes FROM catalogue_audit_log
    WHERE action='stage_only_batch'`;
  assert.equal(audits.filter(row=>row.changes?.batchKey==='replay-002').length,1);
  const dbTypes=await sql`SELECT jsonb_typeof(changes) AS type
    FROM catalogue_audit_log WHERE action='stage_only_batch'`;
  assert.ok(dbTypes.every(row=>row.type==='object'));
});

test('changed payload with same idempotency key is rejected and leaves existing run intact',async()=>{
  const req={sourceKey:'wikidata' as const,batchKey:'conflict-003',records:[fixture('Q880000103','Before')]};
  const first=await persistStageBatch(sql,req);
  await assert.rejects(persistStageBatch(sql,{
    ...req,records:[fixture('Q880000103','After')]
  }),/BATCH_KEY_PAYLOAD_CONFLICT/);
  assert.deepEqual(await persistedCounts(first.runId),{staged:1,reviews:1});
});

test('invalid dates, mismatched URLs and repeated source IDs are quarantined',async()=>{
  const badDate={...fixture('Q880000104','Bad Calendar'),
    releaseEvents:[{...fixture('Q880000104','Bad Calendar').releaseEvents[0],date:'2021-02-29'}]};
  const spoof={...fixture('Q880000105','Wrong Host'),sourceUrl:'https://www.wikidata.org.example.org/wiki/Q880000105'};
  const duplicated=fixture('Q880000106','Repeated');
  const result=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'quarantine-004',
    records:[badDate,spoof,duplicated,duplicated]
  });
  assert.equal(result.quarantined,3);
  assert.equal(result.pendingReview,1);
  assert.deepEqual(await persistedCounts(result.runId),{staged:4,reviews:4});
  const statuses=await sql`
    SELECT batch_position,review_status,source_record_id IS NOT NULL AS has_source
    FROM staging_records WHERE ingestion_run_id=${result.runId}::uuid
    ORDER BY batch_position
  `;
  assert.deepEqual(statuses.map(x=>x.review_status),['rejected','rejected','pending','rejected']);
  assert.deepEqual(statuses.map(x=>x.has_source),[false,false,true,false]);
});

test('authoritative external ID and media-type mismatch is quarantined, published title untouched',async()=>{
  const [original]=await sql`
    INSERT INTO titles(title_type,original_title,publication_status)
    VALUES ('movie','Synthetic Canonical Guard','published')
    RETURNING id::text AS id
  `;
  const [src]=await sql`
    INSERT INTO source_records(source_key,external_record_id,source_url,license_code)
    VALUES ('wikidata','Q880000107','https://www.wikidata.org/wiki/Q880000107','CC0')
    RETURNING id::text AS id
  `;
  await sql`
    INSERT INTO external_ids(title_id,source_key,external_id,source_record_id)
    VALUES (${String(original!.id)}::uuid,'wikidata','Q880000107',${String(src!.id)}::uuid)
  `;
  const result=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'type-guard-005',
    records:[fixture('Q880000107','Synthetic Series Imposter','series')]
  });
  assert.equal(result.quarantined,1);
  const [title]=await sql`
    SELECT title_type,original_title,publication_status
    FROM titles WHERE id=${String(original!.id)}::uuid
  `;
  assert.deepEqual(title,{
    title_type:'movie',original_title:'Synthetic Canonical Guard',publication_status:'published'
  });
});

test('two concurrent transactions with same batch key resolve to exactly one run',async()=>{
  const req={sourceKey:'wikidata' as const,batchKey:'concurrent-006',
    records:[fixture('Q880000108','Parallel One')]};
  const [a,b]=await Promise.all([persistStageBatch(sql,req),persistStageBatch(sql,req)]);
  assert.equal(a.runId,b.runId);
  assert.equal([a.replayed,b.replayed].filter(Boolean).length,1);
  assert.deepEqual(await persistedCounts(a.runId),{staged:1,reviews:1});
  const runs=await sql`
    SELECT count(*)::integer AS n FROM ingestion_runs WHERE source_key='wikidata' AND batch_key='concurrent-006'
  `;
  assert.equal(runs[0]?.n,1);
});

test('forced exception within transaction rolls back run, stage, review, source and audit',async()=>{
  const req={sourceKey:'wikidata' as const,batchKey:'rollback-007',
    records:[fixture('Q880000109','Rollback Candidate')]};
  await assert.rejects(sql.begin(async tx=>{
    await stageInsideTransaction(tx,req);
    throw new Error('SYNTHETIC_FORCED_ROLLBACK');
  }),/SYNTHETIC_FORCED_ROLLBACK/);
  const rows=await sql`
    SELECT
      (SELECT COUNT(*)::integer FROM ingestion_runs WHERE batch_key='rollback-007') AS runs,
      (SELECT COUNT(*)::integer FROM source_records WHERE source_key='wikidata' AND external_record_id='Q880000109') AS sources,
      (SELECT COUNT(*)::integer FROM catalogue_audit_log WHERE changes->>'batchKey'='rollback-007') AS audits
  `;
  assert.deepEqual(rows[0],{runs:0,sources:0,audits:0});
});

test('client-supplied malformed batch or too-large payload fails before any transaction',async()=>{
  await assert.rejects(persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'INVALID KEY',records:[fixture('Q880000111','Bad')]
  }),/INVALID_BATCH_IDENTITY/);
  await assert.rejects(persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'oversized-008',
    records:[fixture('Q880000112','X'.repeat(70_000))]
  }),/BATCH_PAYLOAD_TOO_LARGE/);
  await assert.rejects(persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'empty-009',records:[]
  }),/BATCH_SIZE_OUT_OF_RANGE/);
  const rows=await sql`
    SELECT count(*)::integer AS n FROM ingestion_runs
    WHERE batch_key IN ('oversized-008','empty-009')
  `;
  assert.equal(rows[0]?.n,0);
});


test('indexed lookup matches a canonical title even when catalogue exceeds former 500-row cap',async()=>{
  await sql`
    INSERT INTO titles(title_type,original_title,publication_status)
    SELECT 'movie','Filler Example ' || gs::text,'published'
    FROM generate_series(1,550) AS gs
  `;
  const [target]=await sql`
    INSERT INTO titles(title_type,original_title,publication_status)
    VALUES ('movie','Original Multilingual Collision','published')
    RETURNING id::text AS id
  `;
  const [source]=await sql`
    INSERT INTO source_records(source_key,external_record_id,source_url,license_code)
    VALUES ('wikidata','Q880000120','https://www.wikidata.org/wiki/Q880000120','CC0')
    RETURNING id::text AS id
  `;
  await sql`
    INSERT INTO external_ids(title_id,source_key,external_id,source_record_id)
    VALUES (${String(target!.id)}::uuid,'wikidata','Q880000120',${String(source!.id)}::uuid)
  `;
  const result=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'index-over-500',
    records:[fixture('Q880000120','New Localized Name')]
  });
  assert.equal(result.pendingReview,1);
  const [stage]=await sql`
    SELECT issue_codes,review_status
    FROM staging_records WHERE ingestion_run_id=${result.runId}::uuid
  `;
  assert.deepEqual(stage?.issue_codes,['SOURCE_MATCH_REQUIRES_FIELD_REVIEW']);
  assert.equal(stage?.review_status,'pending');
});
test('indexed title-localization collisions still require review, never auto-merge',async()=>{
  const [target]=await sql`
    INSERT INTO titles(title_type,original_title,publication_status)
    VALUES ('movie','Distinct Telugu Canonical Name','published')
    RETURNING id::text AS id
  `;
  await sql`
    INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
    VALUES (${String(target!.id)}::uuid,NULL,'Ambiguous Localized Identity','alternative')
  `;
  const result=await persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'alias-identity',
    records:[fixture('Q880000121','Ambiguous Localized Identity')]
  });
  const [stage]=await sql`
    SELECT issue_codes,review_status FROM staging_records
    WHERE ingestion_run_id=${result.runId}::uuid
  `;
  assert.deepEqual(stage?.issue_codes,['AMBIGUOUS_TITLE_ALIAS']);
  assert.equal(stage?.review_status,'pending');
});


test('too many ambiguous title candidates fail closed without partial staging',async()=>{
  await sql`
    INSERT INTO titles(title_type,original_title,publication_status)
    SELECT 'movie','Shared Overloaded Title','published'
    FROM generate_series(1,601)
  `;
  await assert.rejects(persistStageBatch(sql,{
    sourceKey:'wikidata',batchKey:'ambiguity-limit-601',
    records:[fixture('Q880000125','Shared Overloaded Title')]
  }),/AMBIGUOUS_CANDIDATE_LIMIT_EXCEEDED/);
  const [checks]=await sql`
    SELECT (SELECT count(*)::integer FROM ingestion_runs
      WHERE batch_key='ambiguity-limit-601') AS runs,
      (SELECT count(*)::integer FROM source_records
      WHERE source_key='wikidata' AND external_record_id='Q880000125') AS sources
  `;
  assert.deepEqual(checks,{runs:0,sources:0});
});
