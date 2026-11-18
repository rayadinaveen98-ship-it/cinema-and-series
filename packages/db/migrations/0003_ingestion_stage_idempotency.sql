-- 0003: idempotent, stage-only batch persistence. Additive; no catalogue or published records changed.
BEGIN;
ALTER TABLE ingestion_runs
  ADD COLUMN batch_key text,
  ADD COLUMN payload_digest text;
ALTER TABLE ingestion_runs
  ADD CONSTRAINT ingestion_batch_identity_check CHECK (
    (batch_key IS NULL AND payload_digest IS NULL)
    OR
    (batch_key ~ '^[a-zA-Z0-9:_.-]{1,80}$'
      AND payload_digest ~ '^[0-9a-f]{64}$')
  );
CREATE UNIQUE INDEX ingestion_run_source_batch_unique
  ON ingestion_runs(source_key,batch_key)
  WHERE batch_key IS NOT NULL;

-- Position uniquely distinguishes even malformed, sourceless candidates.
ALTER TABLE staging_records ADD COLUMN batch_position integer
  CHECK (batch_position >= 0);
CREATE UNIQUE INDEX staging_run_position_unique
  ON staging_records(ingestion_run_id,batch_position)
  WHERE batch_position IS NOT NULL;

-- One issue reason per staged record; repeated commits cannot multiply review tickets.
CREATE UNIQUE INDEX review_queue_staging_reason_unique
  ON review_queue(staging_record_id,reason_code);
COMMIT;
