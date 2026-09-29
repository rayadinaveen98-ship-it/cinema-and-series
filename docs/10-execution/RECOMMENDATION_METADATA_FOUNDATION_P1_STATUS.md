# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — SHARD 7 COMPLETE  
**Date:** 2026-09-29  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. The corrected V3 production path has now completed:

- reviewed source cleanup — **2026-09-20 UTC**
- `topup` — **2026-09-21 UTC**
- physical shard 1 — **2026-09-22 UTC**
- physical shard 2 — **2026-09-23 UTC**
- physical shard 3 — **2026-09-24 UTC**
- physical shard 4 — **2026-09-25 UTC**
- physical shard 5 — **2026-09-26 UTC**
- physical shard 6 — **2026-09-27 UTC**
- physical shard 7 — **2026-09-28 UTC**

The next eligible production recommendation operation is **physical shard 9**, reviewed at a conservative **40,831 D1 rows written**.

Completed recommendation operations: **8 / 15** (`topup`, `1`, `2`, `3`, `4`, `5`, `6`, `7`).  
Remaining recommendation operations: **7** (`9`, `10`, `11`, `12`, `13`, `14`, `15`).

Current production totals after shard 7:

- recommendation titles: **9,227**
- genres: **479**
- people: **25,689**
- title-genre relationships: **9,183**
- title-credit relationships: **40,248**

Current integrity/provenance counters:

- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

The shard-7 writer re-captured the corrected live projection at exactly **16,380 = 6,562 Movie + 9,818 Series**, with the locked projection SHA unchanged, and finished with exact operation state `complete`. P1 is **not complete**; final verification remains ineligible until all remaining production operations complete.

## Corrected frozen projection

The authoritative recommendation projection remains exactly:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**
- cross-type collisions after reviewed cleanup: **0**

This fingerprint supersedes the **obsolete 14,115-title / 8-shard** production-population contract.

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 canonical recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Reviewed media-identity corrections — COMPLETE

Durable registry: `data/quality/media_identity_corrections.json`  
Consumer: `scripts/media_identity_corrections.py`

- `Q3049630` — excluded as non-audiovisual manga-series identity.
- `Q3146368` — canonicalized to **Series** after review.

Unknown or unreviewed Movie/Series collisions remain hard failures.

### Production cleanup evidence — 2026-09-20

- controller: **`35490594774`**
- cleanup writer: **`35490618771`**
- deleted exactly:
  - `movies / wd-Q3049630`
  - `series_titles / series-wd-Q3049630`
  - `catalogue_titles / wd-Q3146368`
- retained canonical row: `series_titles / series-wd-Q3146368`
- post-cleanup projection: **16,380 = 6,562 Movie + 9,818 Series**
- cross-type collisions: **0**
- artifact ID: **`10598937124`**
- artifact ZIP SHA-256: **`152dda1963c2f2967b9a904ccc5e497aa4cacefa830deba1b6643bc7d1cb65d6`**

## Schema and quota guard

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the one-row-per-UTC-day production mutation reservation. V3 binds the exact operation in `workflow_run_id` as `<controller-run-id>:<operation>`.

P1 owns migrations **0021** and **0022**. Do not add `0023+` to `main` until P1 closes unless the roadmap is explicitly revised.

Historical guard rows are audit evidence and must not be reset, deleted, or reused.

## Immutable materialization evidence

### Parent materialization

- run: **`35252106776`**
- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- parent projection SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**
- genre relationships: **13,689**
- credit relationships: **58,069**

Exact lineage to corrected projection:

- unchanged reusable identities: **14,114**
- newly added identities: **2,266**
- removed identities: **1**
- removed QID: **`Q3049630` only**
- changed common entries: **0**

### Delta materialization — COMPLETE / READ-ONLY

- workflow: `P1 Rebaseline Materialization V2`
- run: **`35421562708`**
- candidates: **2,266 / 2,266**
- missing title entities: **0**
- skipped relationships because of missing labels: **0**
- unusable claims: **5**

### Authoritative V3 materialization — COMPLETE / READ-ONLY

- workflow: `P1 Repartition Materialization V3`
- run: **`35428784454`**
- analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**
- artifact: `recommendation-metadata-materialization-v3-repartitioned`
- artifact ID: **`10579264534`**
- downloaded artifact ZIP SHA-256: **`059b989bd4e8dae069039f74c7415ddaa3070c9217ac8b6e428b9992f6545bc5`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**

Authoritative normalized graph:

- recommendation titles: **16,380**
- distinct genres: **612**
- distinct people: **37,964**
- title-genre relationships: **16,489**
- title-credit relationships: **70,551**
- global graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**

`scripts/verify_p1_v3_production.py` reconstructs the normalized production graph and requires exact graph SHA equality; matching counts alone are insufficient.

## V3 quota-safe production plan

Parent shard 0 already present in production corresponds exactly to physical modulo-16 partitions **0 and 8**, so those inherited rows are not rewritten.

Locked operation order:

`topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`

| Operation | Reviewed estimated D1 rows | State |
|---|---:|---|
| top-up | 15,531 | **COMPLETE 2026-09-21** |
| physical 1 | 39,575 | **COMPLETE 2026-09-22** |
| physical 2 | 41,741 | **COMPLETE 2026-09-23** |
| physical 3 | 49,159 | **COMPLETE 2026-09-24** |
| physical 4 | 39,785 | **COMPLETE 2026-09-25** |
| physical 5 | 46,591 | **COMPLETE 2026-09-26** |
| physical 6 | 39,371 | **COMPLETE 2026-09-27** |
| physical 7 | 41,117 | **COMPLETE 2026-09-28** |
| physical 9 | 40,831 | **NEXT** |
| physical 10 | 36,946 | pending |
| physical 11 | 40,223 | pending |
| physical 12 | 39,166 | pending |
| physical 13 | 47,836 | pending |
| physical 14 | 41,466 | pending |
| physical 15 | 42,118 | pending |

Largest reviewed operation is **49,159 rows**, below the P1 conservative **80,000 rows/UTC-day** ceiling.

## Completed production evidence

| UTC date | Operation | Controller / guard | Writer | Reviewed | Actual D1 rows | Exact title / genre-link / credit-link slice | Post totals (titles / genres / people / genre-links / credits) |
|---|---|---|---|---:|---:|---|---|
| 2026-09-21 | topup | `35563283332` / `35563283332:topup` | `35563331648` | 15,531 | **14,985** | 250 / 317 / 1,695 | 1,994 / 251 / 7,595 / 1,958 / 8,626 |
| 2026-09-22 | 1 | `35689533994` / `35689533994:1` | `35689574657` | 39,575 | **37,791** | 1,030 / 969 / 4,156 | 3,024 / 303 / 10,632 / 2,927 / 12,782 |
| 2026-09-23 | 2 | `35820142892` / `35820142892:2` | `35820184949` | 41,741 | **39,259** | 1,005 / 1,007 / 4,432 | 4,029 / 342 / 13,595 / 3,934 / 17,214 |
| 2026-09-24 | 3 | `35958174447` / `35958174447:3` | `35958228439` | 49,159 | **45,683** | 1,056 / 1,041 / 5,384 | 5,085 / 374 / 16,894 / 4,975 / 22,598 |
| 2026-09-25 | 4 | `36097101466` / `36097101466:4` | `36097154585` | 39,785 | **36,529** | 1,003 / 975 / 4,202 | 6,088 / 406 / 19,244 / 5,950 / 26,800 |
| 2026-09-26 | 5 | `36219922803` / `36219922803:5` | `36219954490` | 46,591 | **42,223** | 1,060 / 1,085 / 5,037 | 7,148 / 427 / 21,776 / 7,035 / 31,837 |
| 2026-09-27 | 6 | `36297206014` / `36297206014:6` | `36297241170` | 39,371 | **35,501** | 1,034 / 1,029 / 4,125 | 8,182 / 452 / 23,728 / 8,064 / 35,962 |
| 2026-09-28 | 7 | `36382476536` / `36382476536:7` | `36382531719` | 41,117 | **36,875** | 1,045 / 1,119 / 4,286 | 9,227 / 479 / 25,689 / 9,183 / 40,248 |

Every completed writer above ended with exact operation state `complete` and zero orphan/provenance violations.

### Selected immutable executable evidence for recent operations

- shard 4 executable SHA-256: **`41596755c34154128f3a147817e54e6d6e1fba2df3a6eb1e80edbe003c67467e`**
- shard 5 executable SHA-256: **`0b72bdc6c5bd4c45464c1df4850187fa203b274f5063ea555e76ab4eaf79379d`**
- shard 6 executable SHA-256: **`650962f1330f73839cdac79e0e7316d468d58d7e679b890c3368f9a4f449c3c0`**
- shard 7 executable SHA-256: **`faa5e20950c3c5e74959e93c1fb53d3ff962d3c9fae0a173bfa40a066d590a8d`**

Recent writer artifacts:

- shard 4 artifact ID **`10848045964`**, ZIP SHA-256 **`bc90af78c7f20deeae698c7b534ce1f83f1e27d8740e5939d1299e7a1fb78344`**
- shard 5 artifact ID **`10898702252`**, ZIP SHA-256 **`197aec78e8b5c3bf8a16c1716aa978a115f18359117db4118eeff25b5db39c0e`**
- shard 6 artifact ID **`10924621403`**, ZIP SHA-256 **`2f86451c30dc90a2cc61f0af11034251b3c915a46ceb2b7e88faa1d1345b1a2a`**
- shard 7 artifact ID **`10952912804`**, ZIP SHA-256 **`e4ac6ca849692361a3445ce5335410e26383a0f279aa1e339678c52b94e6b338`**

### 2026-09-28 shard-7 production evidence

Controller run **`36382476536`** reserved the UTC mutation day for operation `7`, and writer run **`36382531719`** verified:

- quota-guard owner: **`36382476536:7`**
- live projection: **16,380 = 6,562 Movie + 9,818 Series**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- reviewed estimated rows: **41,117**
- actual D1 rows written: **36,875**
- pre-state: **0 / 0 / 0** title / title-genre / title-credit rows
- exact completed slice: **1,045 / 1,119 / 4,286**
- post totals: **9,227 / 479 / 25,689 / 9,183 / 40,248**
- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**
- artifact ID: **`10952912804`**
- artifact ZIP SHA-256: **`e4ac6ca849692361a3445ce5335410e26383a0f279aa1e339678c52b94e6b338`**

### 2026-09-27 independent read-only snapshot

Workflow run **`36300254259`** independently confirmed the state immediately before shard 7:

- source cleanup: **complete**
- completed prefix: `topup,1,2,3,4,5,6`
- completed operations: **7 / 15**
- shard 7: **not_started**
- shard 7 current slice: **0 titles / 0 title-genres / 0 title-credits**
- shard 7 expected slice: **1,045 titles / 1,119 title-genres / 4,286 title-credits**
- next operation: **7**
- next reviewed estimate: **41,117 rows**
- current UTC guard: **`36297206014:6`**
- production totals: **8,182 / 452 / 23,728 / 8,064 / 35,962**
- health violations: **0**
- P1 exit-ready: **false**
- snapshot artifact ID: **`10925114272`**
- snapshot artifact ZIP SHA-256: **`aff4345b93a818ba7149b649289c72be445c24ce5fab5e4919ce1e54a15d036f`**

## Production orchestration safety

The V3 writer requires:

1. `main` + explicit production authorization,
2. immutable reviewed V3 analysis run,
3. exact artifact/projection/graph/executable fingerprints,
4. reviewed source cleanup complete,
5. exact live projection before every write,
6. operation-bound daily guard ownership,
7. exact `not_started -> complete` state transition,
8. zero orphan/provenance violations,
9. final exact normalized graph match,
10. final Catalogue Quality V1 **S0 = 0 / S1 = 0**.

The controller schedule may be delayed by GitHub. Safety depends on the UTC guard row, not exact scheduler timing.

## Remaining P1 gates

1. reviewed media-identity corrections ✅
2. stale catalogue/background write freeze ✅
3. 2,266-identity delta materialization ✅
4. exact 16,380-title V3 graph assembly/attestation ✅
5. quota-safe physical write plan ✅
6. V3 orchestration review/merge ✅
7. reviewed source cleanup ✅
8. V3 top-up ✅
9. physical shard 1 ✅
10. physical shard 2 ✅
11. physical shard 3 ✅
12. physical shard 4 ✅
13. physical shard 5 ✅
14. physical shard 6 ✅
15. physical shard 7 ✅
16. physical shards **9–15** ⏳ — **7 operations remain**
17. final exact production graph verification ⏳
18. Catalogue Quality V1 **S0 = 0 / S1 = 0** ⏳
19. final production evidence + mark P1 COMPLETE ⏳

## Next operation

On the next fresh, unreserved UTC quota day, the controller must observe:

- `topup`, `1`, `2`, `3`, `4`, `5`, `6`, `7` = complete
- physical shard `9` = `not_started`

It should then reserve that UTC day for **physical shard 9**, reviewed at **40,831 D1 rows written**.

Do not reset, delete, or reuse historical quota-guard rows, and do not bypass the permanent controller if GitHub's scheduled execution is delayed.

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the normalized production graph exactly matches V3 graph SHA `9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`, referential/provenance checks pass, reviewed source cleanup remains exact, and post-write Catalogue Quality is **S0 = 0 / S1 = 0**.

P2 production implementation does not begin from a partial P1 materialization.
