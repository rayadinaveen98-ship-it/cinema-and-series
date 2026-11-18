# Cinema & Series roadmap

## Stage 00 — IMPLEMENTED (documents committed; awaiting PR integration)

Product contract, ADR, architecture flowcharts, data policy, free-tier guardrails and acceptance checklist.

## Stage 01 — FOUNDATION IMPLEMENTATION IN PROGRESS

Repository conventions, dependency-free domain tests, TypeScript typecheck, SQL migrations 0001–0005 and disposable PostgreSQL integration passed in CI. Neon Free pilot created in aws-ap-southeast-1 (project plain-violet-46536395; database cinema_pilot), with migrations 0001–0005 applied and a verified 13-title pilot (11 films and 2 series). Reapplying curated seed created no duplicates. Read-only API is implemented, typechecked, request-tested and Worker bundle-checked, but is NOT DEPLOYED and has not performed a live Worker-to-Neon HTTP query. Mobile is not implemented. Personalized recommendations and similar-title reads have passed CI. The stage-only ingestion evaluator also passed strict TypeScript and quarantine tests; no import runs or published changes were made.

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

## Historical pre-staging checkpoint — archived, superseded below

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

## Stage 01 — Field-evidence checkpoint (2026-11-18)

**IMPLEMENTED + TESTED IN DRAFT PR:** Structured, strict Wikidata P577 date observations; rejected incomplete year/month precision and invalid/non-Gregorian dates; multiple-date conflict flags; unresolved Wikidata P364/P136 item IDs; language/genre and title-label comparison; complete no-auto-publish invariant. Source-provided `verification=verified` release events are quarantined before staging. Internal review qualifications now audit this source-field comparison without altering canonical titles, releases or streaming offers.

**NOT CERTIFIED:** Editorial assertion that any P577 represents an original theatrical premiere, verified original-language mapping, existing OTT availability, legal reuse beyond scoped source policy, authenticated reviewer identity, working public API, complete multilingual pilot or Android application. Source client tests are mocked, not live.

**CURRENT GATE:** Field-level source *comparison* is ready for further manual verification; independent fact-check and an authenticated publication workflow remain pending.


## Curated catalogue batch 0002 — VERIFIED ON 2026-11-18

- Scope: Six additional historical films (Jawan, K.G.F: Chapter 2, Kantara, Pushpa: The Rise, Premalu, Jailer) across hi/kn/te/ml/ta original languages. RRR retained separately.
- Exact original theatrical release dates verified against studio/distributor and/or contemporary release reporting; original languages corroborated with production/certification records. Evidence URLs and scope in docs/data/MULTILINGUAL_PILOT_0002.md. No dub, territory-OTT, provider offer, artwork or broader filmography claims were imported.
- Curated SQL: jobs/curated/0002_multilingual_verified.sql; six fixed canonical IDs, additive source references, language tags, one original theatrical premiere each, scoped field_provenance and curation audit. No automatic publisher or remote importer invoked.
- CI: latest source-code run 44249777228, four jobs successful including PostgreSQL apply-twice idempotence/integrity. Neon Free pilot: applied source-reviewed batch, read back and re-applied it once; counts unchanged after replay.
- Verified Neon now has 7 published films, 7 verified original-premiere events, 16 source pointers (2 RRR + 14 new), 24 field-provenance rows, 6 new curation audit rows, 0 import runs, 0 staging records, 0 review tickets, and **zero verified live OTT offers**. RRR was preserved.
- Stage 01 approximately 7/60 manually sourced pilot records (~12%). Remaining: ~53 source-verified multilingual titles, international/series representation, API-on-Neon live integration, verified user workflows, editorial auth, provider rights policy and performance/load certifications. Stage 01 is IN PROGRESS, NOT complete.


## International film + first-series checkpoint — 2026-11-18

**IMPLEMENTED, TESTED, AND SEEDED IN ISOLATED NEON FREE:** batch 0003 adds four sourced theatrical films (Parasite, Spirited Away, The Intouchables, Inception) and two sourced first-season launches (Dark, Squid Game). Original Korean/Japanese titles are preserved in their original scripts, with English search aliases. Sources include Korean Film Council, Studio Ghibli, Unifrance, American Film Institute, The Numbers and Netflix announcements; details in `docs/data/INTERNATIONAL_PILOT_0003.md`.

**Schema:** migration 0005 adds a `series_debuts` table, without dropping or modifying the existing film-release constraint. Film `original_premiere` records remain solely in `release_events`. The title-details API combines them with `series_debuts` using the distinct response kind `series_debut`. The movie anniversary query explicitly requires type=movie and original_premiere. The Netflix first-season launch does NOT create a current streaming offer.

**Evidence:** CI success on source commit `b7aad0077432631d6bae6ed2ab6d066bf92c956e` (runs 44263704068 and 44263714142), including migration and repeated seed plus verification in disposable PostgreSQL. Applied additive migration and seeded batch on isolated Neon Free, then replayed identical seed with unchanged counts. Neon readback: 13 published titles (11 movies, 2 series), 10 original languages, 11 verified film original theatrical release events, 2 verified historical series launch events, 28 source pointers, 42 field-provenance records, 0 verified current streaming offers, 0 ingestion runs/staging/review rows.

**Stage 01 remains IN PROGRESS:** ~13/60 verified title-count pilot, 47 more needed. Still pending independent catalogue source work, live Worker-to-Neon HTTP, performance benchmarking, authenticated editorial review, source policies and user-facing mobile implementation. Stage 02 is NOT started and no APK exists.

## Discovery performance and parity checkpoint — 2026-11-18

**IMPLEMENTED / TESTED**: 10,000 synthetic titles on disposable PostgreSQL 17, inside a transaction ending in ROLLBACK; 13 curated titles unchanged. Refactored title search to indexed canonical+localization candidate UNION and guest recommendation/related-title scoring to grouped language/genre matches. Strict SQL parity regression compares all scoring outputs (including same-type bonus and excluded-source title), ensures RRR alias deduplication, matches Spirited Away to the Japanese original and treats user percent/underscore searches literally. All four CI jobs passed for commit 92ef512fd87e3813b9b8278ce0d05b2e4ef172be.

Observed CI SQL execution times (baseline to optimized): English-alias search 9.393 to 4.706 ms; guest ranking 65.582 to 12.824 ms; browse 0.147 to 0.079 ms; film original-premiere day 0.154 to 0.171 ms. These are individual synthetic SQL measurements, not p95, device timing or an SLA. The direct read-only Neon catalogue queries also returned correct international aliases, Korean-language thrillers, historical movie anniversaries and original-series debuts.

**Not complete**: approximately 47 additional independently sourced titles, a read-only authenticated Hono/Cloudflare Worker-to-Neon HTTP smoke, realistic international user latency, authenticated editorial review, source-rights checks and Android UI/APK. Remain at Stage 01, draft PR, no main merge or public release. See docs/verification/2026-11-18-discovery-scale.md.

## Read-only Hono/Neon HTTP smoke preparation — 2026-11-18

The opt-in runner and synthetic safety tests are implemented. The runner uses real Hono routes + Drizzle/Neon HTTP (without a deployed Worker), validates the scoped reader role, SELECT-only privileges and no private staging access, and checks public catalogue requests. **LIVE HTTP SMOKE NOT TESTED:** cinema_api_reader has now been created with precisely 11 scoped SELECT grants and verified to have no data writes, admin membership, schema CREATE or private review/audit reads. Its password has NOT been activated; no database credential has been issued to GitHub or the test runner. This is separately security-gated. See docs/security/READONLY_NEON_API_SMOKE.md. Stage 01 remains IN PROGRESS and no public Worker/APK exists.

## Reader-authenticated database gate — PASSED, 2026-11-18

Founder confirmed privately saving the Neon-generated password. Reader login identity now accepts scoped SELECT and rejects private `staging_records` SELECT with permission denied. **Security role provisioning prerequisite completed.** Next required milestone is actual Hono/Drizzle neon-http smoke in a trusted local Windows environment using the reader DSN only (never via draft-PR CI). No further catalogue expansion or deployment until this live HTTP test is run and reviewed. Stage 01 remains IN PROGRESS.
