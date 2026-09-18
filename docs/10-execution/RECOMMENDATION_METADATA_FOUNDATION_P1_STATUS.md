# Recommendation Metadata Foundation P1 — Execution Status

**Status:** READY FOR GUARDED, RESUMABLE PRODUCTION WRITE  
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

The permanent production gate is stricter than a count check. It validates the reviewed analysis run and commit, restores the immutable evidence artifact, verifies the analyzed SHA-256, and recaptures the live projection immediately before each write. Pure append-only catalogue growth may continue only when all analyzed entries remain byte-for-byte compatible; removed or changed analyzed entries hard-stop the write.

## Production write gate

`.github/workflows/recommendation-metadata-production-write-v1.yml` is the only authorized recommendation-metadata mutation path.

Safety behavior:

1. workflow dispatch only
2. `main` branch only
3. explicit `apply_production_write=true` required
4. reviewed run ID, analysis commit, candidate counts, relation counts, and projection SHA-256 are locked
5. reviewed materialization commit must remain an ancestor of the production write commit
6. materialization artifact must be complete and read-only
7. requested shard must be one of `0..7` and must carry the reviewed fingerprint
8. SQL is allow-listed to P1 insert statements only
9. current production projection is recaptured before every write
10. removed/changed analyzed catalogue entries hard-stop the write; safe append-only growth is reported separately
11. migration `0021` is applied idempotently before shard writes
12. exactly one reviewed shard is written per production dispatch
13. writes are idempotent and resumable
14. referential-integrity and provenance checks run after every shard
15. final verification requires exactly **14,115 titles**, **13,689 title-genre relations**, and **58,069 title-credit relations**
16. final Catalogue Quality V1 must retain **S0 = 0** and **S1 = 0**

Single-shard dispatch is deliberate. The current normalized P1 dataset exceeds a single Workers Free-plan daily write budget when table/index writes are considered, so production population must remain bounded rather than attempting one giant mutation.

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
- generated SQL is transaction wrapped and projection-fingerprint bound

The P1 audit/materializer/projection tests and full Fast V1 App CI are green on the active branch.

## Migration numbering rule

The active Recommendation Metadata Foundation owns migration number **0021**.

A dormant `feature/series-native-title-enrichment-v1` branch also contains an unmerged `0021_series_native_title_provenance.sql`. That branch must be rebased/renumbered to **0022 or later** before any future merge. Recommendation P1 keeps `0021` because it is the locked active product phase and merges first.

## Remaining P1 gates

1. merge P1 with commit ancestry preserved; do **not** squash the reviewed analysis lineage
2. allow the normal production deploy path to apply migration `0021`
3. execute reviewed metadata shards through the guarded production-write workflow, bounded by D1 quota
4. run `verify_final`
5. require exact normalized relationship counts and zero orphan/provenance violations
6. require Catalogue Quality V1 **S0 = 0 / S1 = 0**
7. record final production counts and close P1

## P1 exit rule

Phase P2/onboarding logic does not begin merely because the schema exists. P1 exits only after the reviewed recommendation metadata is present in production, referential/provenance checks pass, and post-write catalogue quality remains clean.
