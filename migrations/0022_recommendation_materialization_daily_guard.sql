-- P1 recommendation metadata production-population daily safety guard.
-- Workers Free D1 allows 100,000 rows written per UTC day. The P1 production
-- population is intentionally limited to one reviewed shard per UTC date.

CREATE TABLE IF NOT EXISTS recommendation_materialization_daily_guard (
  utc_date TEXT PRIMARY KEY,
  shard_index INTEGER NOT NULL CHECK (shard_index BETWEEN 0 AND 7),
  projection_sha256 TEXT NOT NULL,
  workflow_run_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Shard 0 was successfully materialized before this guard table existed.
-- Seed that verified production write so a second shard cannot run on the same
-- UTC quota day after this migration is deployed.
INSERT OR IGNORE INTO recommendation_materialization_daily_guard (
  utc_date,
  shard_index,
  projection_sha256,
  workflow_run_id
) VALUES (
  '2026-09-18',
  0,
  '4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448',
  '35323383185'
);
