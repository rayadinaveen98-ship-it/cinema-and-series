# Catalogue Growth Milestone — 10K

Status: ACTIVE

## Target
Reach and verify at least **10,000 combined catalogue titles in production**.

Quality guardrails:
- Movies and Series must both contribute materially; do not satisfy the target by inflating only one media type.
- Preserve provenance and confidence rules already frozen in the repository.
- Do not infer unsupported exact dates or verification states.
- Prefer deterministic, resumable, idempotent ingestion/backfill jobs.
- Production count, not local/generated count, is the acceptance metric.

## Acceptance
Milestone is complete only when production verification confirms:
1. combined movies + series >= 10,000;
2. both movie and series production counts are non-trivial and ingestion remains healthy;
3. app CI is green;
4. ingestion/backfill workflow(s) complete successfully;
5. production API/live catalogue smoke verification passes.

## Execution strategy
1. Audit current production counts and recent ingestion workflow health.
2. Remove remaining throughput bottlenecks in movie and series backfills.
3. Expand historical/year/language/country coverage using existing open-source adapters and safe fallbacks.
4. Run bounded batches to remain within Cloudflare D1 free-tier limits.
5. Verify counts after each batch and continue until the acceptance target is reached.

No user-facing progress report is required before acceptance unless execution is blocked by an external limitation that requires user action.
