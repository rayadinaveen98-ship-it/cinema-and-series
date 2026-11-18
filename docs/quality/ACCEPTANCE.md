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
