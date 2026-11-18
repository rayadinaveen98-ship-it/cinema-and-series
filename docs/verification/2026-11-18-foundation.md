# Verified foundation checkpoint — 2026-11-18

Repo: rayadinaveen98-ship-it/cinema-and-series
Branch: feature/foundation-architecture-domain-20261118
Review PR: https://github.com/rayadinaveen98-ship-it/cinema-and-series/pull/1

## Implemented
- Stage 00 product contract, architecture decision, frontend/backend/import Mermaid flowcharts.
- Stage 01 pure domain engines: normalization, source-validation, identity, strict Gregorian dates, historical premiere, language/genre recommendations, OTT offer freshness.
- PostgreSQL 0001 and additive 0002 migrations.
- Isolated Neon free pilot: plain-violet-46536395, database cinema_pilot, PostgreSQL 17, Singapore region.

## Verification
- GitHub Actions domain tests/TypeScript and disposable PostgreSQL migration checks were successful (branch CI).
- Neon: 18 tables, pg_trgm extension, 1 source-verified sample title RRR, 2 distinct release events.
- Wikidata Q60424165: canonical external identity/original Telugu language/original premiere.
- ZEE5 official listing: historical digital premiere and drama genre; current playback availability intentionally remains UNVERIFIED.
- Duplicate seed execution left exactly 1 title, 2 release events, 1 unverified offer, 2 source records, 6 provenance links.
- Historical query for March 25 includes RRR; May 20 does not present OTT premiere as original theatrical release.

## Explicitly not delivered
- No published backend API, Cloudflare deployment, Android app, APK, full catalogue, 60-title pilot or real-device test.
- No production backup/restore certification, Drizzle connection or ingestion bot.
- No paid subscription or quota upgrade.

## Risk note
Neon Free and Workers Free impose strict storage/compute/request limits. Google Play registration can require a separate one-time fee (currently USD 25 if no existing developer account); Android sideload testing does not require a Play Store listing. Any monetized launch is a separate approval gate.

## Stage 01 API contract checkpoint

- Read-only Hono/Drizzle API on draft PR #1. Paths: /v1/health, /v1/titles, /v1/titles/:id, /v1/search, /v1/releases/on-this-day, /v1/languages, /v1/genres.
- Successful CI job set on commit 6e996759999d8c77459608acb9afb0c92226d1af: API TypeScript, synthetic HTTP tests, Wrangler dry-run, domain tests/typecheck, and disposable PostgreSQL migration/integrity.
- No real Worker-to-Neon HTTP request has been verified; only the migration and direct Neon SQL proof are verified.
- A placeholder recommendation method was removed rather than returning silently empty recommendations. That API is still pending.


## Discovery and ingestion-safety checkpoint — 2026-11-18

- Implemented POST /v1/recommendations (guest-language/genre scoring, no-store, strict 4 KB JSON body and bounded filters), GET /v1/titles/:id/similar (ranked related titles, never includes source, unpublished excluded).
- Implemented stage-only ingestion preflight: canonical Wikidata Q-IDs only, 40-record maximum, duplicate and ambiguous-ID quarantine, no database writes or publication.
- GitHub Actions push run 44236729306 on d27b95b6173746bd19772f31d4908c109bc30e7b: all four jobs passed: domain-tests, api-contract, ingestion-preflight and disposable-postgres.
- Earlier trial failures were corrected during CI (contract entry omission, fixture tie-order, strict TypeScript test). These are not a production deployment or real database corruption.
- Read-only Neon SQL smoke: language te + genre action scores RRR at 8; similar RRR returns empty while catalogue has one title. Separate from a deployed Worker-to-Neon integration test.
- Pilot unchanged: one published RRR, zero ingestion runs/staging/review rows. No paid upgrades or Android APK.

## Final historical-cutoff gate

- Commit 5963287f9f41503f4aeecf336756f79e94ca6dc0 adds before-current-year restrictions to domain history and Hono/Drizzle SQL query.
- Both GitHub Actions runs 44237255769 and 44237261186 completed successfully for this commit, across the four CI jobs.
- Historical release time zone is UTC for server cutoff; this is documented as a possible refinement near New Year for user-local calendars.
- PR remains draft. The hosted Neon pilot is not changed by this gate.

## Transactional persisted staging — verified 2026-11-18

- Repository commit 7c0bc5b290fe3d0f1dc83aeec2835bbdd57879f8: migrations 0003/0004, stage-only Postgres.js writer, disposable integration tests, and correct JSONB object/array encoding.
- All four CI jobs completed successfully at the latest integration-test run. Staging DB tests cover 8 cases: new candidate+review, idempotent replay, payload mismatch rejection, quarantine, media type conflict, concurrent replay, full transaction rollback and invalid/oversized batch rejection.
- Neon project plain-violet-46536395, database cinema_pilot: migrations 0003 and 0004 applied. Verified new indexed constraints and nullable retrieved_at. No staging runs or review tickets were created in Neon. RRR publication and release counts unchanged (1 / 2).
- Live Neon remote staging transaction and live Worker-to-Neon API were NOT exercised. The staging test proof is on disposable PostgreSQL only.
- Source pointer semantics: retrieved_at=NULL until actual network source retrieval. This avoids fabricated evidence timestamps.

## Source access and review workflow checkpoint

- Feature commit 3cd961f2312571a69655459fcb92b3d68f29fc3f: scoped external-ID/trigram candidate matching; Q-entity fetch-only client with mock API tests; review-decision writer and disposable concurrency/rollback tests.
- Both push and PR CI workflows passed on this head (source client mock tests, 11 persistence tests and 7 reviewer tests plus other existing test suites).
- Published metadata untouched; source client is not connected to a live scheduled importer. A review qualification is **not** publication approval and does not change titles, original releases or streaming offers.
- Existing Neon pilot migrations 0001–0004 preserved; no new migration required. No paid resource or deployment was created.

## Field-evidence and review-audit checkpoint — 2026-11-18

- Commit 729a9fa8e6380599ff95cc04456ec6cd7e80ba0e: added field-evidence module with eight synthetic field-level tests; stage self-verified premiere quarantine test; review-audit integration and assertion in disposable PostgreSQL.
- Corrected a strict TypeScript optional-array fixture error during first CI attempt. Latest corrected CI run 44248197976 succeeded across domain-tests, api-contract, ingestion-preflight and disposable-postgres.
- Source date parsing: P577 time precision 11 only, Gregorian calendar, valid midnight UTC date; P577 never directly implies original theatrical premiere. Multiple exact P577 dates require review.
- P364 and P136 property values are returned as unresolved Wikidata Q-IDs, not automatically mapped to ISO language or controlled genre values.
- No live Wikidata fetch, no Neon staging or title publication, no paid changes, no Worker deployment or APK.

## Multilingual curated seed — source and Neon evidence

- Commit 3e7dd277fdc4ffdd47cf219d31552bb5c4496a6a introduced jobs/curated/0002_multilingual_verified.sql, docs/data/MULTILINGUAL_PILOT_0002.md and packages/db/tests/curated_pilot.integration.sql.
- Production/distributor sources: Red Chillies/YRF (Jawan, Hindi 2023-09-07); Hombale/CBFC (K.G.F: Chapter 2, Kannada 2022-04-14); Hombale and a producer interview (Kantara, Kannada 2022-09-30); Mythri and Indian Express plus Google Play (Pushpa: The Rise, Telugu 2021-12-17); contemporary Malayalam Indian Express and Times of India reporting (Premalu, Malayalam 2024-02-09); Sun Pictures and CBFC (Jailer, Tamil 2023-08-10).
- CI push run 44249777228 passed domain-tests, api-contract, ingestion-preflight and disposable-postgres (curated RRR + six-title seed run twice; integrity test passed).
- Neon pilot was inspected before changes (1 published RRR, two release events, two sources), expanded with six verified historical title seeds, and inspected after an identical replay: 7 published titles, 7 verified original premieres, 16 source pointers, 24 field provenance entries, 6 curation audit rows. Zero import runs, staged records, review tickets and verified current streaming offers. The existing RRR OTT premiere event remains separate from seven original-premiere events.
- A curated published fact record is not proof of current digital playback availability, nor that a live Worker has served it. No paid services, deployed Worker or Android app were created.


## International film and TV source pilot — verified 2026-11-18

- Versioned files: `packages/db/migrations/0005_series_debut_event.sql`, `jobs/curated/0003_international_series_verified.sql`, `packages/db/tests/international_pilot.integration.sql`, `docs/data/INTERNATIONAL_PILOT_0003.md`.
- Initial schema option would replace the release_events CHECK constraint. Rejected for Neon change control; final migration adds an independent series_debuts table and index and leaves existing constraints/rows unchanged. CI passed both push and PR workflows on commit `b7aad0077432631d6bae6ed2ab6d066bf92c956e`.
- Historic theatrical dates checked: Parasite KR 2019-05-30 (Korean Film Council); Spirited Away JP 2001-07-20 (Studio Ghibli); The Intouchables FR 2011-11-02 (Unifrance); Inception US 2010-07-16 (American Film Institute and The Numbers).
- First publicly available TV season launch, **not** theatrical/festival first screening: Dark NETFLIX 2017-12-01 (Netflix official announcement); Squid Game NETFLIX 2021-09-17 (Netflix official announcement).
- Disposable PostgreSQL repeats seed twice, asserts film vs series separation, 4 film premieres, 2 series launches, 12 new source pointers, 18 new field-provenance rows, 6 new audit entries, 4 English aliases and no new streaming offers.
- Neon Free before: 7 titles, 8 total prior release_events including the RRR OTT premiere, 16 source pointers, 0 ingestion runs. After applying migration/batch and after replay: 13 published titles, 10 original languages, 11 verified theatrical film original premieres, 2 separately stored verified series debuts, 28 source pointers, 42 provenance entries, 0 verified streaming offers and 0 staging/review records. Six new curation audit entries stable after replay.
- No destructive database migrations, public Cloudflare Workers, actual Worker-to-Neon request, bulk fetch job, signed APK or paid infrastructure created.

## Credential-gated real API smoke preparation — 2026-11-18

- Code commit 3ea096c81abaff794c5f1e5b1b0eda84d27fe7a8 adds apps/api/smoke/live-neon.mts, safety.ts, synthetic negative guards and dedicated pnpm smoke:neon command. GitHub CI run 44269419424 passed all four existing jobs, including API typecheck, mock HTTP contracts, new guard negatives and bundle dry run.
- Expected smoke behavior if separately approved with a new least-privilege reader: Hono createApp() invokes the actual Drizzle neon-http NeonCatalogueRepository, verifies SELECT-only role and absence of private staging access, then tests real catalogue, cursor, language, Japanese alias, historical movie anniversaries, distinct series launches, guest recommendations, similar and HTTP errors.
- Neon read-only role audit found no cinema_api_reader account (only cinema_owner and platform-admin login roles); no secret was fetched or provisioned. The owner role is not permitted for smoke.
- IMPORTANT: Real Hono-to-Neon HTTP runner has NOT been executed. No deployed Cloudflare Worker, admin-to-reader credential reconfiguration, new role, Neon data changes, app APK or paid tier. The secure role creation and private credential injection remain a separate founder approval gate.
- Scope and exact permissions: docs/security/READONLY_NEON_API_SMOKE.md.

## Reader-only SQL role granted — 2026-11-18

- Founder requested completion of the required security gate before unrelated development. On isolated Neon Free project plain-violet-46536395, branch main, database cinema_pilot, created `cinema_api_reader` via SQL with LOGIN **without a password**, NOINHERIT, no admin/create/replication/bypassRLS rights and no memberships. Did NOT use Neon Console/API administrator-role creation.
- Granted CONNECT to cinema_pilot, USAGE on public, and SELECT on exactly 11 application read-model tables. Checked every public relation: no SELECT on staging_records, review_queue, ingestion_runs, catalogue_audit_log or any non-allowlisted relation. All 11 SELECTs true; all INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER false; CREATE public false.
- The Neon Roles listing reports authentication_method=no_login until user privately activates/resets the password; no password was generated or retrieved. The founder's **manual** next action is Neon Console > Roles > cinema_api_reader > Reset password. No password/connection string is to be pasted into chat.
- Before and after role grant, 13 published titles and 0 staging records; no film rows modified. Real Hono-to-Neon HTTP smoke remains NOT CERTIFIED. All further work paused at this explicit prerequisite.

## Scoped reader password and privilege acceptance — 2026-11-18

- Founder confirmed a new password was generated and safely saved using Neon Console Reset password. No credential was shared in chat, GitHub or tests.
- Independently checked that `cinema_api_reader` is a password-authenticated Neon login, with no superuser/CREATEDB/CREATEROLE/BYPASSRLS flags. A live scoped SQL query made *as that role* returned exactly 13 published titles; a SELECT on private `staging_records` returned `permission denied`. This is actual limited-role database access, **not** a Hono runtime HTTP test.
- Next required action: user runs the opt-in Hono/Neon HTTP smoke locally with an environment-only reader DSN, and shares the sanitized PASS/FAIL labels. CI must not receive the secret and no Worker deployment or APK is authorized. Roadmap remains Stage 01 / live Hono HTTP BLOCKED until smoke is executed.
