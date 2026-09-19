# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — 16,380-TITLE REBASELINE ACTIVE  
**Date:** 2026-09-19  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 is still active. Production population began from an earlier reviewed 14,115-title projection, but catalogue growth before the write freeze made that projection obsolete before shard 1 could be applied. Safety gates stopped the stale write before recommendation metadata mutation.

The corrected frozen production projection is now:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- suppressed exact/year movie overlaps: **375**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative read-only projection run: **`35421313646`**

This fingerprint supersedes the previous 14,115-title production-population fingerprint for all future P1 writes.

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Reviewed media-identity corrections

The 2026-09-19 production recapture surfaced two Movie/Series QID collisions. The write gate failed closed before mutation and both identities were verified directly against Wikidata in read-only run **`35420861375`**.

- **`Q3049630` — Eko Eko Azarak**: explicit `P31=Q21198342` (`manga series`). This is non-audiovisual for this product and is excluded from both Movie and Series recommendation identities.
- **`Q3146368` — Shattered City: The Halifax Explosion**: explicit `P31=Q1259759` (`miniseries`) plus `Q98701476` (`television film broadcast in two parts`). Under the reviewed deterministic precedence rule it canonicalizes to **Series**.

The durable registry is `data/quality/media_identity_corrections.json`, consumed by `scripts/media_identity_corrections.py`. Recommendation projection building applies reviewed corrections before cross-type collision detection. Unknown/unreviewed collisions still hard-fail.

The correction implementation passed the full test suite, catalogue audit, typecheck and build and was merged through PR **#31** (`df52e0679456b07f5e8779294901c18c88d9685e`).

## Schema

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the UTC-day D1 write reservation used by guarded production population.

Exact-date `movies` rows take precedence over duplicate QIDs in `catalogue_titles`. Generic Movie/Series same-QID collisions remain hard failures unless an explicit reviewed correction is present.

## Historical source-yield audits — COMPLETE

Global source-yield audit run **`35204375729`** was read-only and established that explicit Wikidata metadata coverage was sufficient to proceed. Its then-current 12,264-title analysis projection had:

- Movies recommendation-ready: **70.30% (3,053 / 4,343)**
- Series recommendation-ready: **35.00% (2,772 / 7,921)**
- explicit `P136`: **11,960**
- explicit `P57`: **5,386**
- explicit Series `P170`: **1,312**
- explicit `P161`: **42,689**
- missing title entities: **0**

India cohort audit run **`35204143430`** was also read-only and row-for-row attested to the same canonical snapshot used by that audit after removing the cohort-only language field. These audits are source-yield evidence; their old projection fingerprints are not current production-write locks.

## Immutable parent materialization — PRESERVED AS REVIEWED EVIDENCE

The first complete reviewed materialization remains valuable immutable evidence:

- run: **`35252106776`**
- analysis commit: **`0e319f86a4a9c7ca085de93bb5b3246606b7d6d0`**
- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- parent SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**
- emitted genre relationships: **13,689**
- emitted credit relationships: **58,069**
- missing title entities: **0**
- production mutation: **false**

This parent artifact is no longer sufficient by itself for production, but its unchanged title evidence is reusable after exact manifest lineage verification.

## Rebaseline lineage — VERIFIED

The parent 14,115-title manifest was compared entry-for-entry against the corrected 16,380-title manifest.

Exact result:

- unchanged entries safe to inherit: **14,114**
- newly added identities requiring fresh materialization: **2,266**
- removed identities: **1**
- removed QIDs: **`Q3049630` only**
- changed common entries: **0**

The same result was independently enforced inside `P1 Rebaseline Materialization V2` prepare job. A common entry changing any manifest field would hard-fail rather than silently reuse parent evidence.

Therefore P1 does **not** re-query Wikidata for all 16,380 titles. It preserves the 14,114 byte-equivalent reviewed parent identities and materializes only the 2,266-title delta.

## Delta materialization — ACTIVE

Workflow: `P1 Rebaseline Materialization V2`  
Run: **`35421562708`**  
Branch event SHA: **`0c53cbbe7195bff137a497b9bb3ec28f040378f6`**  
Production mutation: **false**

The delta is partitioned by QID modulo 8 and runs sequentially with bounded retries to remain polite to Wikidata.

Checkpoint recorded on 2026-09-19:

| Delta shard | New titles | Genre rels | Credit rels | Missing title entities | Missing-label rels | State |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 250 | 317 | 1,695 | 0 | 0 | **complete** |
| 1 | 278 | 333 | 1,403 | 0 | 0 | **complete** |
| 2 | 279 expected | — | — | — | — | running |
| 3 | 292 expected | — | — | — | — | queued |
| 4 | 292 expected | — | — | — | — | queued |
| 5 | 297 expected | — | — | — | — | queued |
| 6 | 276 expected | — | — | — | — | queued |
| 7 | 302 expected | — | — | — | — | queued |

Completed delta shards 0 and 1 both had **zero unusable claims**, **zero missing title entities**, and **zero skipped relationships from unresolved labels** at this checkpoint.

Delta shard 0's exact D1 top-up cost model is **15,531 rows written**. That top-up is important because the parent shard-0 data already exists in production and must not be wastefully rewritten.

## Existing production recommendation state — PRESERVED

The only recommendation materialization currently present in production is the original reviewed parent shard 0:

- production writer run: **`35323383185`**
- parent logical shard: **0 / 7**
- recommendation titles: **1,744**
- genres: **235**
- people: **6,184**
- title-genre relations: **1,641**
- title-credit relations: **6,931**
- D1 rows written: **65,299**
- orphan genre relations: **0**
- orphan credit relations: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

No stale shard-1 recommendation metadata was written on 2026-09-19. The collision gate stopped the attempt before mutation.

Because parent shard 0 is QID modulo 8 = 0, it corresponds exactly to physical modulo-16 partitions **0 and 8**. Those inherited rows will be preserved. Only the new delta identities belonging to that parent shard need a top-up.

## Quota-safe V3 repartition — IMPLEMENTED, FINAL ARTIFACT PENDING

The old 8-shard production plan is retired for future writes. Before the rebaseline, parent shards 3 and 5 already had estimated costs of **76,087** and **76,905** D1 rows written. Adding the new catalogue delta could push an 8-way shard over the conservative **80,000 rows/day** P1 ceiling.

`scripts/repartition_recommendation_materialization.py` therefore reconstructs the exact reviewed current materialization and repartitions it into **16 physical shards** by numeric QID modulo 16 without re-querying Wikidata.

The repartitioner hard-fails on:

- conflicting duplicate entity rows
- missing/extra title identities
- cross-shard title overlap
- orphan title relationships
- genre/person entity closure mismatch
- projection coverage mismatch
- unreviewed removal lineage

Parent-only cost observations for the 16 physical partitions are approximately **31k–43k rows written each**, leaving material headroom for the delta.

The intended production shape is:

- preserve inherited parent data already present for physical partitions **0 and 8**
- apply a delta-only top-up for those identities
- write full reviewed physical shards **1–7 and 9–15**, one quota-safe shard per eligible UTC day
- require every final physical shard plan to remain **≤80,000 estimated D1 rows written**

Manual assembly workflow: `.github/workflows/p1-repartition-materialization-v3.yml`.

It may run only after all eight delta artifacts exist. It will validate exact lineage, require all 2,266 delta titles, require zero missing title entities and zero missing-label relationship skips, build all 16 physical reviewed shards, calculate exact D1 write costs, enforce the 80k ceiling, calculate the existing-shard-0 top-up cost, and preserve one authoritative V3 artifact.

## D1 write-cost model

`scripts/prepare_d1_reviewed_import.py` uses the migration `0021` table/index layout:

- `recommendation_titles`: **4** D1 rows written per logical insert
- `genres`: **4**
- `people`: **4**
- `title_genres`: **3**
- `title_credits`: **4**

The model matched the observed parent shard-0 import exactly at **65,299** rows written.

Cloudflare Free daily rows-written allowance is treated as 100,000, while P1 enforces a stricter internal ceiling of **80,000** for one production population action per UTC quota day.

## Automation freeze during rebaseline

Catalogue mutation workflows remain paused by `.github/workflows/p1-background-write-coordinator.yml` while P1 is incomplete.

The obsolete 14,115-title / 8-shard `.github/workflows/p1-quota-safe-daily-resume.yml` schedule was explicitly frozen through PR **#33**, merged as **`0633f7d8fa400e1ad1805a2e0ed93e31fab8ac47`**. It is manual-only and cannot acquire a quota lock or dispatch the stale writer.

The old `Recommendation Metadata Production Write V2` remains locked to the parent fingerprint and must not be used for the new baseline. A V3 writer/controller will be enabled only after the authoritative V3 rebaseline artifact exists and its exact write-cost plan is reviewed.

## Production-write requirements for V3

The replacement production writer/controller must enforce all of the following:

1. `main` only for mutation
2. explicit mutation authorization
3. immutable successful V3 analysis run + artifact provenance
4. exact current projection SHA-256 **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`** recaptured immediately before every write
5. exact 16,380-title candidate identity contract
6. no unreviewed cross-type collisions
7. title-scoped shard status check: complete / not-started / unsafe partial / unsafe overfilled
8. ≤80,000 deterministic estimated D1 rows written for the selected action
9. exactly one production population action per eligible UTC quota day
10. verified ownership of the UTC-day quota guard
11. D1-compatible derivative must preserve every reviewed data statement
12. idempotent inserts/upserts only
13. post-write orphan and provenance checks after every action
14. special top-up path for the already-present parent shard-0 identities; do not rewrite inherited physical 0/8 rows
15. final exact title/relationship counts must come from the V3 artifact, not obsolete parent constants
16. final Catalogue Quality V1 must retain **S0 = 0 / S1 = 0**

## Migration numbering rule

P1 owns:

- **0021** — recommendation metadata foundation
- **0022** — recommendation materialization UTC-day guard

Do not add migration `0023+` to `main` until P1 closes unless the P1 plan is explicitly revised. The dormant Series native-title branch must be rebased and renumbered before any future merge.

## Remaining P1 gates

1. ~~apply recommendation schema and validate parent shard-0 production write~~ ✅
2. ~~detect and review live media-identity collisions before stale shard-1 write~~ ✅
3. ~~lock deterministic media-identity corrections~~ ✅
4. ~~freeze catalogue mutation and obsolete daily resume paths~~ ✅
5. complete all **2,266** delta materialization titles — **in progress**
6. run V3 16-way repartition assembly and require exact lineage/coverage/write costs
7. lock and merge V3 reviewed artifact + production orchestration
8. top up existing parent shard-0 identities safely
9. populate remaining physical shards one quota-safe UTC day at a time
10. run final integrity/provenance verification
11. require Catalogue Quality V1 **S0 = 0 / S1 = 0**
12. record final normalized counts and mark P1 COMPLETE

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, referential/provenance checks pass, and post-write catalogue quality remains clean. P2/onboarding work does not begin merely because the schema or partial materialization exists.
