# Change log

## 2026-11-18

- Approved ₹0 pilot architecture and original product foundation.
- Initialized repository (main branch).
- Started feature/foundation-architecture-domain-20261118 for Stage 00 documents and Stage 01 preliminary domain/schema work.
- Added synthetic domain tests, TypeScript compilation and isolated PostgreSQL migration/integrity CI; passed on PR branch.
- Provisioned separate Neon Free pilot (plain-violet-46536395 / cinema_pilot, PostgreSQL 17) without touching existing projects.
- Applied 0001/0002 schema migrations: 18 tables, pg_trgm present.
- Added 1 curated source-traceable RRR film with 2 release events, 2 source records and 6 field-evidence links. Duplicate seed rerun verified idempotent.
- Historical query returns original premiere 2022-03-25 and excludes OTT premiere 2022-05-20 from that calendar.
- No Cloudflare Worker deployed, no app UI/APK built and no paid services provisioned.

- Implemented Hono/Drizzle read-only API: title listing, details, search, verified original-release history, language and genre directories. API request tests, typecheck and Worker dry-run passed.
- Fixed pnpm CI workspace setup and Node 22 TypeScript strip-mode compatibility; all latest jobs passed.
- No Cloudflare Worker deployment, no Android UI/APK, no paid services.

- Added guest-first POST recommendation ranking and GET similar-title API, with input caps, error cases and deterministic tests.
- Added stage-only Wikidata source preflight, 40-record safety limit, duplicate/alias/type conflict quarantine and its independent CI job.
- Latest four-job CI passed (run 44236729306); Neon remains one RRR record without bulk importer writes.

- Fixed On This Day to exclude same-year and future original-premiere dates; verified through domain and API tests.
- All four jobs green on historical-cutoff commit 5963287f9 (CI runs 44237255769, 44237261186). PR remains draft and no new movie records were published.

- Implemented transactional stage-only import persistence using Postgres.js, including source+batch idempotency, payload digest conflict rejection, serialized concurrent replay, quarantine, review queue records and structured JSONB audit.
- Added migration 0003 for batch/position/review uniqueness and 0004 to distinguish unverified source pointers from actually fetched records (nullable retrieved_at). Both tested on disposable PostgreSQL then applied to isolated Neon Free pilot.
- All 8 disposable persistence tests passed after fixing a JSONB-string serialization bug; no synthetic staging runs or data were written to hosted Neon. Existing RRR and two release records preserved.
- No public deployment, APK, paid resource or main-branch merge.

- Replaced 500-title prefix candidate lookup with scoped source-ID/title/alias pg_trgm matching and fail-closed ambiguous-set cap; disposable PostgreSQL tests exceed 500 records and exercise 601 same-title collisions.
- Added explicit Wikidata read-only source client with mock HTTP tests for identification, pacing, 429/503 backoff, response caps and untrusted entity identity. No real Wikimedia network requests were performed by CI.
- Added internal review decision state machine: new candidates can qualify for further editorial checking only with a source snapshot; ambiguous matches are blocked; rejection, locks, notes, audit, races and rollback tested. Reviewer authentication and publishing are NOT implemented.
- Four CI jobs passed on commit 3cd961f2312571a69655459fcb92b3d68f29fc3f; Neon pilot remains unchanged.

- Added isolated Wikidata claim-assessment module: candidate title label matching, strict day-precision Gregorian P577 observations, multi-date conflict flags, source P364/P136 Q-ID preservation. No inferred original-premiere or streaming verification.
- Added stage quarantine for incoming candidates that self-declare verified historical release events without separate evidence.
- Added structured field-evidence assessment to the internal nonpublishing quality review audit; synthetic/disposable PostgreSQL checks passed.
- Current Stage 01 is still gated on independent verified data, source-to-staging operational pipeline, operator authentication and release certification.
