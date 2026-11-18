import { createHash } from 'node:crypto';
import type { Sql, TransactionSql } from 'postgres';
import { evaluateBatch } from './stage.ts';
import { readCandidateIdentities } from './candidates.ts';

export interface StageBatchRequest {
  /** Explicitly reviewed source adapter. No other source accepted in v1. */
  sourceKey: 'wikidata';
  /** Stable caller-owned idempotency key; replaying a changed payload is forbidden. */
  batchKey: string;
  records: readonly unknown[];
}
export interface PersistedBatch {
  runId: string;
  replayed: boolean;
  staged: number;
  quarantined: number;
  pendingReview: number;
}

type ValidatedBatch = StageBatchRequest & { digest: string };

function validateBatchRequest(request: StageBatchRequest): ValidatedBatch {
  if (request.sourceKey !== 'wikidata' ||
      typeof request.batchKey !== 'string' ||
      !/^[a-zA-Z0-9:_.-]{1,80}$/.test(request.batchKey)) {
    throw new RangeError('INVALID_BATCH_IDENTITY');
  }
  if (!Array.isArray(request.records) ||
      request.records.length < 1 || request.records.length > 40) {
    throw new RangeError('BATCH_SIZE_OUT_OF_RANGE');
  }
  let serialized: string;
  try {
    serialized = JSON.stringify(request.records);
  } catch {
    throw new RangeError('BATCH_NOT_JSON_SERIALIZABLE');
  }
  if (typeof serialized !== 'string' || Buffer.byteLength(serialized, 'utf8') > 65536) {
    throw new RangeError('BATCH_PAYLOAD_TOO_LARGE');
  }
  const digest=createHash('sha256')
    .update(request.sourceKey+'\\n'+serialized)
    .digest('hex');
  return {...request,digest};
}

/**
 * Runs ONLY within an externally managed transaction, exported for rollback tests.
 * No mutations of titles, release_events, streaming_offers or external_ids.
 */
export async function stageInsideTransaction(
  tx: TransactionSql,
  request: StageBatchRequest
): Promise<PersistedBatch> {
  const batch=validateBatchRequest(request);

  // Serializes concurrent staging of the same source; a unique DB key is
  // the ultimate safeguard. The lock exists only for the transaction.
  await tx`SELECT pg_advisory_xact_lock(hashtext(${'cinema:ingest:'+batch.sourceKey}))`;

  const [prior]=await tx`
    SELECT id::text AS id, payload_digest, run_status,
           processed_count::integer AS processed_count,
           rejected_count::integer AS rejected_count
    FROM ingestion_runs
    WHERE source_key=${batch.sourceKey} AND batch_key=${batch.batchKey}
    LIMIT 1
  `;
  if (prior) {
    if (prior.payload_digest !== batch.digest) {
      throw new Error('BATCH_KEY_PAYLOAD_CONFLICT');
    }
    if (prior.run_status!=='completed') {
      throw new Error('BATCH_PENDING_REVIEW_OR_RECOVERY');
    }
    return {
      runId:String(prior.id),replayed:true,
      staged:Number(prior.processed_count),
      quarantined:Number(prior.rejected_count),
      pendingReview:Number(prior.processed_count)-Number(prior.rejected_count)
    };
  }

  // Read real canonical identities from DB, never take caller-supplied
  // identity or publishability claims as authoritative.
  const catalogue=await readCandidateIdentities(tx,batch.records);
  const decisions=evaluateBatch(batch.records,catalogue);

  const [created]=await tx`
    INSERT INTO ingestion_runs
      (source_key, batch_key, payload_digest, run_status)
    VALUES
      (${batch.sourceKey},${batch.batchKey},${batch.digest},'running')
    RETURNING id::text AS id
  `;
  if (!created) throw new Error('INGESTION_RUN_NOT_CREATED');
  const runId=String(created.id);

  for (let position=0; position<batch.records.length; position++) {
    const disposition=decisions.decisions[position]!;
    const input=batch.records[position];
    const candidateJson=JSON.stringify(input ?? null) ?? 'null';
    let sourceRecordId:string | null=null;

    // Only legitimate, validated allowlisted records create a provenance
    // reference. Never overwrite an existing source's original evidence.
    if (disposition.disposition!=='quarantined' && disposition.sourceId) {
      const externalId=disposition.sourceId.split(':')[1]!;
      const canonicalUrl='https://www.wikidata.org/wiki/'+externalId;
      const [added]=await tx`
        INSERT INTO source_records
          (source_key,external_record_id,source_url,license_code,retrieved_at)
        VALUES ('wikidata',${externalId},${canonicalUrl},'CC0',NULL)
        ON CONFLICT (source_key,external_record_id) DO NOTHING
        RETURNING id::text AS id
      `;
      if (added) {
        sourceRecordId=String(added.id);
      } else {
        const [existing]=await tx`
          SELECT id::text AS id FROM source_records
          WHERE source_key='wikidata' AND external_record_id=${externalId}
        `;
        if (!existing) throw new Error('SOURCE_RECORD_IDENTITY_INCONSISTENT');
        sourceRecordId=String(existing.id);
      }
    }

    // Use the driver's JSON parameter serializer; passing JSON.stringify(text)
    // as a plain value would store a JSONB STRING, not an object/array.
    const reviewStatus=disposition.disposition==='quarantined'?'rejected':'pending';
    const [staging]=await tx`
      INSERT INTO staging_records
        (ingestion_run_id,source_record_id,raw_candidate,review_status,issue_codes,batch_position)
      VALUES (
        ${runId}::uuid,
        ${sourceRecordId}::uuid,
        ${tx.json(JSON.parse(candidateJson))}::jsonb,
        ${reviewStatus},
        ${tx.json(disposition.issues)}::jsonb,
        ${position}
      )
      RETURNING id::text AS id
    `;
    if (!staging) throw new Error('STAGING_INSERT_NOT_CONFIRMED');

    const reason=disposition.issues[0] ?? 'NEEDS_HUMAN_REVIEW';
    await tx`
      INSERT INTO review_queue(staging_record_id,reason_code,status)
      VALUES (${String(staging.id)}::uuid,${reason},'open')
      ON CONFLICT (staging_record_id,reason_code) DO NOTHING
    `;
  }

  await tx`
    UPDATE ingestion_runs
    SET run_status='completed',
        processed_count=${decisions.total},
        rejected_count=${decisions.quarantined},
        checkpoint=${String(decisions.total)},
        finished_at=now()
    WHERE id=${runId}::uuid
  `;

  // Safe, minimal audit event only; deliberately no publication of any title.
  const audit={
    runId,source:batch.sourceKey,batchKey:batch.batchKey,
    staged:decisions.total,quarantined:decisions.quarantined
  };
  await tx`
    INSERT INTO catalogue_audit_log(actor_type,action,changes)
    VALUES ('import_job','stage_only_batch',${tx.json(audit)}::jsonb)
  `;

  return {
    runId,replayed:false,staged:decisions.total,
    quarantined:decisions.quarantined,
    pendingReview:decisions.total-decisions.quarantined
  };
}

export async function persistStageBatch(
  sql: Sql,
  request: StageBatchRequest
): Promise<PersistedBatch> {
  validateBatchRequest(request);
  return sql.begin(tx=>stageInsideTransaction(tx,request));
}
