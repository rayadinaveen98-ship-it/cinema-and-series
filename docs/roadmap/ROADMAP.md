# Cinema & Series roadmap

## Stage 00 — IMPLEMENTED (documents committed; awaiting PR integration)

Product contract, ADR, architecture flowcharts, data policy, free-tier guardrails and acceptance checklist.

## Stage 01 — FOUNDATION IMPLEMENTATION IN PROGRESS

Repository conventions, dependency-free domain tests, TypeScript typecheck, SQL migrations 0001–0004 and disposable PostgreSQL integration passed in CI. Neon Free pilot created in aws-ap-southeast-1 (project plain-violet-46536395; database cinema_pilot), with verified migration applied and 1 source-traced RRR sample. Reapplying curated seed created no duplicates. Read-only API is implemented, typechecked, request-tested and Worker bundle-checked, but is NOT DEPLOYED and has not performed a live Worker-to-Neon HTTP query. Mobile is not implemented. Personalized recommendations and similar-title reads have passed CI. The stage-only ingestion evaluator also passed strict TypeScript and quarantine tests; no import runs or published changes were made.

Stage 01 EXIT requires:
- all foundation CI passing and versioned tests;
- dependency/TypeScript and API builds verified after real package installation;
- reproducible database migration and rollback checked against disposable PostgreSQL;
- approximately 60 manually/source-verified films/series across language groups;
- duplicate and incorrect-date protection demonstrated;
- provider terms audited;
- persisted stage-only transactions/replay/rollback and internal review decisions COMPLETE for disposable PostgreSQL; Neon migrations applied. Automated fetching-to-staging, authenticated reviewer operations and publication still pending;
- read-only discovery performance checked on multi-language catalogue, not just the single RRR record.

## Stage 02 — NOT STARTED

Design system: premium title holders, onboarding, home, discovery, search, historical releases, details; accessibility and performance specifications. Founder visual approval before full UI build.

## Stage 03 — NOT STARTED

Implement actual API, mobile views, preference persistence, language/genre recommendation, historical release queries, pagination and error states.

## Stage 04 — NOT STARTED

Batched imports and size/performance measurements with credible multilingual data and provider verification.

## Stage 05 — NOT STARTED

Build versioned APK; CI + real Android phone/tablet tests, visual QA, recovery testing and stable-candidate record.

## Stage 06 — NOT STARTED

Separate launch readiness/security/attribution/budget review and explicit release approval.

## Zero-rupee gate

No infrastructure provisioning or paid tier upgrade without a separate authorization. Free tier thresholds must be monitored rather than silently exceeded.

## Latest development checkpoint — 2026-11-18

Implemented and CI-verified: guest-first recommendation API, related-title API, original-premiere earlier-year cutoff and stage-only Wikidata source preflight. Four CI jobs green on commit 5963287f9. Neon read-only pilot confirms RRR relevance score 8 for original language Telugu + action genre; since the pilot contains only RRR, More Like This is honestly empty.

Still NOT implemented or approved for public launch: transactional persisted importer, human review workflow, approximately 59 more curated pilot titles, direct Hono-to-Neon live integration, large-dataset latency tests, a released Worker and any mobile APK. Do not count Stage 01 as complete or Stage 02 as started.

## Transactional staging checkpoint — 2026-11-18

Implemented and CI verified: migration 0003 (unique source+batch key and digest, unique candidate position and review ticket) and migration 0004 (no false retrieval timestamps); Node-only Postgres.js 3.4.9 staging writer. A single database transaction stages source pointers, candidates, review tickets, counters and audit. Tests verify changed-payload rejection, same-batch replay, concurrency, quarantine, rollback and correct JSONB object/array storage. Candidate matching now searches indexed Wikidata external IDs, title names and localized aliases instead of loading a fixed 500-record prefix; exceptionally ambiguous sets exceeding 600 matches fail closed. Large-scale query plan/load benchmarks remain pending.

Both migrations applied to isolated Neon Free pilot with all 1 title, 2 release events, 0 staging runs, 0 staging records, and 0 review tickets preserved. No synthetic test data were inserted into Neon. No scheduled importer, UI reviewer approvals, automated publication or public Worker deployed.

Next gates: real source-to-staging mapping with licensed claim-level validation, checkpoint/retry handling; authenticated reviewer operations and a separately reviewed publication pipeline; 59 additional externally verified records; query/load benchmarking; and read-only API deployment safety review. Keep the PR draft until stage exit.

## Source client and editorial review checkpoint — 2026-11-18

Implemented and CI-verified on isolated draft PR: an explicit, fetch-only Wikidata Q-entity client with descriptive identification, 1-second minimum pacing, max 5 source IDs per call, bounded response size, stop-on-429/503 and Retry-After reporting. This client has ONLY been exercised with synthetic/mock HTTP responses; no live Wikimedia fetch or automatic staging occurred.

Scoped canonical candidate lookup uses external ID and pg_trgm title/alias candidate queries, not the old 500-title prefix. Tested in disposable PostgreSQL with >500 existing titles, localized-alias collisions and >600 ambiguous candidates (fail closed). Indexed query plan/performance at 10k+ titles is still unmeasured.

Internal stage-only review operations now atomically reject a candidate or qualify a new one for further editorial processing, with fetched snapshot check, required evidence note, audit record, replay protection, concurrency and forced rollback tests. This is NOT an authenticated human reviewer service, NOT an approval for publication, and NOT publicly deployed. Existing alias/identity collisions cannot be qualified using this simple path.

Still outstanding before Stage 01 exit: source entity-to-field mapping + verification, real authorized rate-limited fetching with checkpoint controls, reviewer authentication/RBAC, audit-safe publication process, verified multilingual pilot of ~60 records, recovery/restore certification and API-to-Neon smoke tests. Android UI/APK remains unstarted.
