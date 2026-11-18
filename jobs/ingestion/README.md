# Cinema & Series ingestion and editorial foundation

## Implemented and CI-verified

- `src/stage.ts`: stage-only record preflight (max 40 candidates, canonical Wikidata Q-ID references, duplicate/invalid/date/type quarantine).
- `src/candidates.ts`: scoped candidate recall using external ID, title, localized alias and pg_trgm; never loads an arbitrary first 500 titles. More than 600 candidates causes a fail-closed error.
- `src/persist.ts`: atomic stage/review/audit transaction, SHA-256 batch digest, idempotent replay, concurrent run serialization, correct JSONB storage. **Never publishes titles**.
- `src/wikidata-client.ts`: explicit read-only fetch of 1–5 Q-entities from Wikidata's stable entity data interface. Requires descriptive User-Agent with project contact URL; sequential requests at least 1000 ms apart, response <= 1 MiB, stop-and-backoff on 429/503. **No scheduled job, no live connector run in CI, and no conversion to publishable film metadata.**
- `src/review.ts`: internal stage-only quality decision ('reject' or 'qualify') with row locks, snapshot-required gate for a new candidate, minimum evidence note and audit. Qualifying means **eligible for further editorial checking**; it is not fact verification/publication. Ambiguous identity records cannot qualify through this simplified path.

## Test evidence

- `pnpm --filter @cinema/ingestion run typecheck`
- `pnpm --filter @cinema/ingestion run test` (pure preflight plus mocked Wikidata client, no outbound requests)
- `pnpm --filter @cinema/ingestion run test:db` (only on disposable localhost PostgreSQL named `cinema_test` with migrations 0001–0004).

CI exercises >500 catalogue rows, localized-alias collisions, >600 ambiguous candidates fail closed, replay, concurrency, rejected/qualified decision atomicity, snapshot absence, source mismatch and rollback. The external source client is **mocked** in tests. No live Wikimedia requests or Neon staging writes have occurred.

## Critical boundaries

- Reviewer codes are caller-supplied and are NOT authenticated identities. No public reviewer endpoint, account access, role-based controls or human review UI exists. Do not deploy this reviewer module before authorized access/RBAC is implemented.
- Source pointers with no actual fetch must retain `retrieved_at=NULL`. Synthetic fetch records in disposable CI are not evidence of real-world title facts.
- Historical publication dates, original languages, dub/territory streaming offers and genres are NOT promoted from unverified Wikidata statements.
- At-scale identity indexing/EXPLAIN and data-quality benchmarks still need real representative catalogue data.
- No scheduled bulk fetch, checkpoint/resume persistence, source mapping, authenticated editorial UI, production publishing or public backend exists.

## Field evidence assessment — 2026-11-18

`src/field-evidence.ts` reads raw Wikidata labels, date statements (P577), original-language item IDs (P364) and genre item IDs (P136). Its output is unverified evidence for human comparison only. P577 must have exact day precision (Wikibase precision 11) and an unambiguous Gregorian day to be considered an observable date. The report never classifies P577 as an original theatrical premiere, and never maps raw language/genre Q-IDs to our canonical codes without separate reference checks.

`compareStagedFields` records matching title labels and publication dates, missing fields, conflicting publication dates and unsupported self-verified release claims. All results explicitly set `originalPremiereVerified=false`, `streamingVerified=false` and `publishable=false`. A staged record claiming an already-verified release is quarantined by the preflight rather than trusted.

The internal `review.ts` qualify transaction now includes this nonpublishing evidence matrix in an audit entry (field booleans and issue codes only; no raw media text or reviewer note). It does **not** turn the fields into verified public facts, and cannot bypass independent theatrical-release and territory-specific streaming checks.

The Wikidata claim mapping follows official JSON-format documentation: https://doc.wikimedia.org/Wikibase/master/php/docs_topics_json.html and https://www.wikidata.org/wiki/Property:P577 . The source adapter still uses injected/mock HTTP in CI, not a live Wikimedia crawl.

Outstanding: independently corroborated original premiere / country / language classification, curated field provenance for actual records, authenticated editor/RBAC, publish/withdraw lifecycle, source freshness, human UI and source-permission review.
