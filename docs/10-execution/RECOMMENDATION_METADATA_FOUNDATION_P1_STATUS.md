# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — SHARD 0/8 COMPLETE  
**Date:** 2026-09-18  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Shared schema

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

The shared title registry is keyed by stable Wikidata identity. Exact-date `movies` rows take precedence over duplicate QIDs in `catalogue_titles`; Series remains a distinct media type. A QID appearing as both Movie and Series is a hard audit failure.

Migration `0022_recommendation_materialization_daily_guard.sql` adds the production-population UTC-day safety lock. It prevents more than one P1 shard from being authorized in the same D1 Free quota day and seeds the already verified 2026-09-18 shard-0 production write.

## Read-only source-yield audits — COMPLETE

### Global coverage

Workflow: `Recommendation Metadata Foundation V1`  
Run: `35204375729`  
State: **complete / read-only / production mutation false**

Fingerprint-bound audit projection at the time of source-yield analysis:

- Movie QIDs: **4,343**
- Series QIDs: **7,921**
- total candidates: **12,264**
- suppressed duplicate movie projections: **199**
- Movie/Series cross-type identity collisions: **0**
- projection SHA-256: `86da6c202ca5013d595596226a80e9dbe008b25a4a7c6b656c61b7c3a1a17786`

Final coverage:

- Movies genre: **73.96%**
- Movies people: **90.42%**
- Movies recommendation-ready: **70.30% (3,053 / 4,343)**
- Series genre: **53.59%**
- Series people: **48.90%**
- Series recommendation-ready: **35.00% (2,772 / 7,921)**
- explicit `P136` relations observed: **11,960**
- explicit `P57` relations observed: **5,386**
- explicit Series `P170` relations observed: **1,312**
- explicit `P161` relations observed: **42,689**
- missing title entities: **0**
- unusable claims: **35**
- high-fanout cast titles surfaced for review: **42**

The audit established enough explicit metadata yield to proceed with production materialization.

### India-language cohorts

Workflow: `Recommendation Metadata India Cohort Audit`  
Run: `35204143430`  
State: **complete / read-only / production mutation false**

The preserved India snapshot was row-for-row attested to the same global canonical projection after removing the cohort-only `language_name` field.

Recommendation-ready coverage:

- Bengali: **49.06% (78 / 159)**
- Gujarati: **50.00% (6 / 12)**
- Hindi: **42.90% (284 / 662)**
- Kannada: **57.29% (55 / 96)**
- Malayalam: **33.33% (81 / 243)**
- Marathi: **30.36% (17 / 56)**
- Punjabi: **16.67% (2 / 12)**
- Tamil: **65.44% (142 / 217)**
- Telugu: **52.40% (109 / 208)**

These are cohort quality signals, not ranking weights and not inferred metadata.

## Production materialization evidence — COMPLETE

The first monolithic materialization attempt correctly stopped on persistent Wikidata `maxlag`; production was never mutated. The workflow was then rebuilt as a resumable 8-shard process with bounded retries, immutable-snapshot restoration, shard fingerprint binding, and aggregate validation.

Authoritative successful materialization:

- workflow run: **`35252106776`**
- analysis commit: **`0e319f86a4a9c7ca085de93bb5b3246606b7d6d0`**
- all 8 materialization shards: **success**
- aggregate: **success**
- production mutation: **false**

Immutable analyzed projection:

- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- projection SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**

Materialized explicit relationships:

- genre relationships emitted: **13,689**
- credit relationships emitted: **58,069**
- total provenance-backed relationships emitted: **71,758**
- explicit relationships before label filtering: **71,808**
- relationships skipped only because a related entity label was unavailable: **50**
- missing label entities: **49**
- missing title entities: **0**
- unusable claims: **37**

Resolved entity observations across shards:

- genre-label resolutions: **2,072 shard-local observations**
- people-label resolutions: **50,717 shard-local observations**

Those two resolution figures are intentionally not treated as global distinct entity counts because the same genre/person may appear in more than one title shard.

## Current production compatibility — VERIFIED

A fresh production-only fingerprint check was run after materialization to ensure the live catalogue had not drifted before authorizing any write.

Workflow: `P1 Production Fingerprint Check Once`  
Run: **`35320178069`**  
State: **success / read-only**

Current production projection:

- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**

Result: **exact match to the successful reviewed materialization**.

The permanent production gate validates the reviewed analysis run and commit, restores the immutable evidence artifact, verifies the analyzed SHA-256, and recaptures the live projection immediately before each write. Catalogue drift hard-stops the production writer.

## Production population checkpoint — SHARD 0 COMPLETE

Migration `0021` was applied successfully by the normal production deploy. The first guarded V1 write attempt then failed safely because Cloudflare D1 remote SQL-file imports reject explicit SQLite `BEGIN`/`COMMIT` controls. D1 reported that a failed import returns the database to its original state, and no recommendation rows were left behind by that attempt.

The execution layer was corrected without changing any reviewed data statement. `scripts/prepare_d1_reviewed_import.py` removes only:

- `PRAGMA foreign_keys = ON;`
- `BEGIN;`
- `COMMIT;`

The executable derivative preserves every reviewed P1 insert statement byte-for-byte and records both original and executable SHA-256 values.

Successful shard-0 production write:

- workflow: `Recommendation Metadata Production Write V2`
- run: **`35323383185`**
- shard: **0 / 7**
- reviewed projection exact-match gate: **passed**
- data statements executed: **16,735**
- D1 rows written: **65,299**
- recommendation titles after shard: **1,744**
- genres after shard: **235**
- people after shard: **6,184**
- title-genre relations after shard: **1,641**
- title-credit relations after shard: **6,931**
- orphan genre relations: **0**
- orphan credit relations: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

## D1 Free quota-safe shard plan

Cloudflare Workers Free D1 currently allows **100,000 rows written per UTC day** and resets the Free daily quota at **00:00 UTC**. P1 therefore permits exactly one reviewed shard per UTC day.

The deterministic write-cost model is derived from migration `0021`'s table/index layout and matched the observed shard-0 result exactly:

- `recommendation_titles`: 4 D1 rows written per logical statement
- `genres`: 4
- `people`: 4
- `title_genres`: 3
- `title_credits`: 4

Reviewed shard plan:

| Shard | Planned D1 rows written | State |
|---:|---:|---|
| 0 | 65,299 | **production complete** |
| 1 | 65,839 | next |
| 2 | 62,370 | pending |
| 3 | 76,087 | pending |
| 4 | 62,148 | pending |
| 5 | 76,905 | pending |
| 6 | 67,608 | pending |
| 7 | 64,703 | pending |

Largest planned shard: **76,905**, leaving **23,095** rows of Free daily write headroom before unrelated traffic. A separate hard safety ceiling of **80,000 rows/shard** is enforced by the resume controller.

`.github/workflows/p1-quota-safe-daily-resume.yml` runs at **00:25 UTC** on fresh quota days. It:

1. restores the immutable reviewed artifact
2. verifies Cloudflare access and current schema
3. checks the per-UTC-day D1 write lock
4. evaluates each shard as `complete`, `not_started`, or unsafe partial/overfilled
5. chooses only the first untouched shard
6. computes the deterministic rows-written cost
7. refuses any shard above 80,000 rows
8. acquires the UTC-day lock before dispatching a production write
9. dispatches the existing guarded V2 writer for exactly one shard
10. no-ops when the current UTC day already has a P1 write lock

Any partial/overfilled shard state hard-stops automation rather than advancing.

## Production write gate

`.github/workflows/recommendation-metadata-production-write-v2.yml` is the guarded mutation worker. The quota-safe daily controller is the preferred production-population entry point.

Safety behavior:

1. `main` branch only
2. explicit production-write authorization required by V2
3. reviewed run ID, analysis commit, candidate counts, relation counts, and projection SHA-256 are locked
4. reviewed materialization commit must remain an ancestor of the production write commit
5. materialization artifact must be complete and read-only
6. requested shard must be one of `0..7` and carry the reviewed fingerprint
7. reviewed SQL is transformed only by removing D1-incompatible execution controls
8. every data statement is preserved byte-for-byte
9. current production projection is recaptured before every write
10. migration `0021`/`0022` application is idempotent
11. exactly one reviewed shard is dispatched by the daily controller per UTC quota day
12. referential-integrity and provenance checks run after every shard
13. final verification requires exactly **14,115 titles**, **13,689 title-genre relations**, and **58,069 title-credit relations**
14. final Catalogue Quality V1 must retain **S0 = 0** and **S1 = 0**

## Materializer behavior

`scripts/enrich_recommendation_metadata.py`:

- never connects to D1 directly
- never mutates production
- English Wikidata labels preferred; explicit `mul` label accepted as fallback
- unresolved labels skip only the dependent relationship
- Movie `P170` is ignored; Series `P170` is allowed
- relationship SQL is idempotent (`INSERT OR IGNORE`)
- entities use QID-stable IDs
- every relationship retains source property + Wikidata entity URL
- generated reviewed SQL is transaction wrapped and projection-fingerprint bound

`scripts/prepare_d1_reviewed_import.py` validates that reviewed artifact, removes only the D1-incompatible execution controls, preserves every data statement, and computes the schema-derived write-cost estimate.

`scripts/p1_shard_status.py` derives a title-scoped status query directly from each reviewed shard. `complete` is allowed to advance, `not_started` is eligible to write, and any mixed state is unsafe.

## Migration numbering rule

Recommendation Metadata Foundation P1 now owns migrations:

- **0021** — recommendation metadata foundation
- **0022** — recommendation materialization UTC-day guard

A dormant `feature/series-native-title-enrichment-v1` branch contains an unmerged migration previously numbered `0021_series_native_title_provenance.sql`. Before any future merge it must now be rebased/renumbered to **0023 or later**.

## Remaining P1 gates

1. ~~merge P1 with reviewed analysis ancestry preserved~~ ✅
2. ~~apply migration `0021` and verify production schema~~ ✅
3. populate reviewed shards under D1 quota — **in progress; shard 0/8 complete**
4. run `verify_final` after all 8 shards are present
5. require exact normalized relationship counts and zero orphan/provenance violations
6. require Catalogue Quality V1 **S0 = 0 / S1 = 0**
7. record final production counts and close P1

## P1 exit rule

Phase P2/onboarding logic does not begin merely because the schema exists. P1 exits only after all reviewed recommendation metadata is present in production, referential/provenance checks pass, and post-write catalogue quality remains clean.
