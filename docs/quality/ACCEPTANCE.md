# Foundation quality and release gates

## Synthetic domain tests

- Reject impossible dates (including non-leap 29 February and 31 April).
- On This Day includes verified ORIGINAL premieres only, excludes regional premieres and OTT.
- Match by identical source external ID; alias similarity must not silently merge.
- Preserve distinction between original language and localized title.
- Recommendations use explicit language/genre preferences and deterministic ties.
- Missing or stale provider verification is not presented as live availability.
- Invalid staged records are quarantined, never published.

## Later database integration requirements

- Idempotent imports verified by running the same batch twice.
- Duplicate external source keys rejected under concurrency.
- Transaction rollback on partial import failure.
- Index selectivity and pagination at 60/1k/10k records.
- Different territories and releases remain independent.
- Audit field provenance and corrections.
- Migration round trip in disposable PostgreSQL; never production database for testing.

## Later mobile and API requirements

- Onboarding: language selections, genres, restart persistence, revised preferences.
- Home/discover/search/date/details: success, empty, loading, slow and offline cases.
- 60 FPS target on representative midrange Android; measured, not presumed.
- TalkBack, dynamic text, contrast, reduced motion and large tap areas.
- Physical APK install, first launch, crash-free navigation and state restore.
- No hidden paid resources or credentials in the APK.

## Evidence classification

PROPOSED / APPROVED / IMPLEMENTED / TESTED / BLOCKED / RELEASED are separate labels. A green unit test does not certify a deployed Worker, actual metadata or Android experience.


## Verified implementation checkpoint — 2026-11-18

- GitHub foundation CI domain tests, TypeScript compiler and disposable PostgreSQL migration + synthetic integrity checks: success.
- Isolated Neon Free pilot created; 0001+0002 migrations executed; 18 tables verified.
- One real, source-linked RRR sample inserted; seed rerun held counts at 1 title, 2 events, 1 unverified offer, 2 sources, 6 field provenance records.
- Live pilot historical SQL returns original premiere March 25, 2022 and not the May 20 OTT premiere.
- Not tested: API build/deployment, Drizzle adapter, 60-title pilot, schema rollback, ingestion at scale, visual UI, native APK or physical Android acceptance.

## 2026-11-18 discovery and preflight checks

- API validates 4 KB JSON recommendation bodies, language and genre syntax/limits, unknown fields, content type and return limits. No user identity is collected.
- Similar-title endpoint rejects malformed IDs and source titles missing from published catalogue; relevance ranking excludes self and staged titles.
- Domain tests prove deterministic ranking, strict calendar cutoff before current year, invalid leap dates, duplicate prevention and OTT exclusion.
- Ingestion preflight checks canonical source host/ID pair, release dates, media type conflicts and duplicate source rows; every valid record still needs review.
- CI contains four green jobs: domain-tests, api-contract, disposable-postgres and ingestion-preflight. No cloud Worker-to-Neon runtime check yet.

## Reviewer and source client regression gate — 2026-11-18

- Source adapter tests inject fake HTTP responses: Q-ID validation, rate-limited pacing, 429/503 stop behavior, response-body size/type validation, identity mismatch and descriptive user-agent policy.
- Scoped title-candidate query tests include >500 existing titles, localized-alias collision, and >600 ambiguous candidates safely failing without partial transaction.
- Review tests: rejected stage cannot be qualified; fetched source snapshot required for new candidate; ambiguous-alias qualification blocked; concurrent decisions cannot both succeed; forced transaction exception rolls back all review changes and audit; stage quality validation never changes published title tables.
- Not certified: trusted reviewer authentication or source fetch itself, human fact-review decisions, real-to-live API performance, publication or physical Android use.

## Source-field evaluation negative-case gate — 2026-11-18

- Reject unsupported year/month precision, impossible calendar dates, and non-Gregorian P577 data as exact days.
- Preserve multiple day-precision P577 values as an ambiguity requiring review.
- Never infer verified original theatrical premiere from P577, or current streaming availability from a source statement.
- Never map P364/P136 Q-identifiers directly into normalized language and genre codes.
- Quarantine source-submitted `verified` release events during preflight.
- Editorial review audit records field comparison without promoting publication status or storing unbounded raw payloads.
- Production certification requires human/editor identity, direct evidence checks and live remote integration tests.

## Multilingual catalogue pilot gate — 2026-11-18

- Six deterministic, individually source-linked historical films now seeded alongside existing RRR.
- Disposable PostgreSQL applies RRR seed and six-film seed twice; automated assertions demand 6 additional film IDs, 5 original language codes, 6 unique original premiere dates/events, 14 additional source pointers, 18 new field-provenance rows, 6 audit records and ZERO new streaming offers.
- Neon Free pilot seed replay left all counts unchanged; historical release type and country are not converted from later dub or OTT releases.
- Not complete: 53 further title records to reach approximately 60, broader film/series and international languages, on-device API integration, artwork license policy, genre comprehensiveness and production review flows.


## International film and series pilot — 2026-11-18

- Four international films use original-premiere events with sourced first local commercial theatrical dates; two original series use the separate series_debuts table, provider='netflix' and no implied current streaming availability.
- CI migration 0005 is additive; existing release_events constraints remain unchanged. Idempotency tests apply curated international seed twice and check all identifiers/aliases, 4 film dates, 2 first-season dates, five new original languages, 12 source references, 18 field provenances, 3 authoritative external IDs and zero current offers.
- Real Neon Free pilot replay confirmed 13 titles (11 movie/2 series), 10 original languages, 11 original theatrical premiere events, 2 series debuts and unchanged existing RRR records.
- NOT CERTIFIED: live Hono Worker-to-Neon details query, 10k-record load testing, automated operational ingest, authenticated review, Android UI/APK/physical test, and full ~60-title catalogue.
