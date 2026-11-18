# Safe ingestion pipeline — persisted stage-only foundation

## Implemented

- Pure preflight `src/stage.ts`: bounded 40-record evaluation, source allowlist, ID and alias review, invalid-date quarantine.
- PostgreSQL writer `src/persist.ts`: exactly one transaction per submitted batch to stage candidates, unresolved review tickets, source identity pointers and audit.
- Batch idempotency uses sourceKey + batchKey uniqueness plus a SHA-256 digest. Same payload/key replays without duplicate rows or audit. Changed payload with reused key fails.
- Advisory lock serializes concurrent staging per source; unique DB constraints provide the final race guard.
- JSONB fields are stored as object/array types using Postgres.js `tx.json`, never as JSON strings.
- Source records created from staged-only pointers have `retrieved_at = NULL`: do not confuse a submitted URL with a verified network fetch.
- Fail-closed limits: up to 40 records and 64 KiB serialized batch input; initial canonical identity lookup is capped at 500 titles (safe pilot limit, NOT at-scale design).
- All new candidate records, including matching IDs and alias conflicts, require review. No publishing is possible through this module.

## Verification

Run `pnpm --filter @cinema/ingestion run test` and `typecheck` for preflight. Database integration tests run only with `STAGING_TEST_DB_URL` pointing to a local database specifically named `cinema_test`, after migrations 0001–0004:

    pnpm --filter @cinema/ingestion run test:db

The disposable PostgreSQL CI job verifies replays, immutable audit, duplicate prevention, forced rollback, and concurrent same-key calls. Hosted Neon was only migrated; **no persisted stage requests were executed there**.

## Not implemented

No network connector, bulk source fetching, automatic scheduling, reviewer authentication/UI, approval-publishing actions, retries/backoff policy, or live data-change feed. Before actual remote import, add licensed source fetching, checkpointed batches and indexed identity matching (replace pilot-only 500-title lookup). Never expose this writer as an unauthenticated public endpoint.
