# Stage-only ingestion preflight

This is a pure data evaluation module. It has NO network access, hosted database credentials, scheduled runs, automatic publishing or write endpoints.

Limits: 40 records per batch; only matching canonical Wikidata Q-IDs under https://www.wikidata.org/wiki/Q... are allowed in the initial pilot. Other sources require a separate licensing and adapter review.

Every new record requires a human/source-quality review before publication. Existing external-ID matches are reviewed for field conflicts; title aliases never silently merge unrelated records.

Output dispositions: needs_new_review; needs_existing_review; quarantined.

Testing: pnpm --filter @cinema/ingestion run typecheck && pnpm --filter @cinema/ingestion run test

Next gates: authorized bounded fetching, a transactional persisted staging writer, DB idempotency and rollback tests, source rate limiting, checkpoint retries, and publication audit.

Do not treat deterministic in-memory evaluation as persisted import idempotency. No change to the existing Neon pilot is made by this code.
