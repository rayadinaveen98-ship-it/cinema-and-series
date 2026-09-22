# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — SHARD 1 COMPLETE  
**Date:** 2026-09-22  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. The corrected V3 orchestration is merged to `main`, the reviewed source-identity cleanup completed on **2026-09-20 UTC**, the V3 `topup` completed on **2026-09-21 UTC**, and **physical shard 1 completed successfully on 2026-09-22 UTC** through the permanent scheduled controller.

The next eligible production recommendation operation is **physical shard 2**, reviewed at a conservative **41,741 D1 rows written**.

The corrected frozen recommendation projection remains exactly:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**
- cross-type collisions after reviewed cleanup: **0**

This fingerprint supersedes the obsolete 14,115-title / 8-shard production-population contract.

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Reviewed media-identity corrections — COMPLETE

Durable registry: `data/quality/media_identity_corrections.json`  
Consumer: `scripts/media_identity_corrections.py`

Reviewed identities:

- **`Q3049630` — Eko Eko Azarak**: non-audiovisual manga-series identity; excluded from Movie and Series recommendation projection.
- **`Q3146368` — Shattered City: The Halifax Explosion**: reviewed miniseries identity; canonicalized to **Series**.

Unknown or unreviewed Movie/Series collisions remain hard failures.

### Production cleanup evidence — 2026-09-20

Controller run **`35490594774`** reserved the UTC quota day for operation `cleanup` and dispatched cleanup run **`35490618771`**.

Deleted exactly:

- `movies / wd-Q3049630`
- `series_titles / series-wd-Q3049630`
- `catalogue_titles / wd-Q3146368`

Retained canonical row:

- `series_titles / series-wd-Q3146368`

Post-cleanup projection remained exactly **16,380 = 6,562 Movie + 9,818 Series**, projection SHA unchanged, cross-type collision count **0**.

## Schema and quota guard

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the single-row-per-UTC-day D1 write reservation. Its legacy `shard_index` range remains `0..7`; V3 uses it as a guard slot while binding the exact operation in `workflow_run_id` as `<controller-run-id>:<operation>`.

P1 owns migrations **0021** and **0022**. Do not add `0023+` to `main` until P1 closes unless the roadmap is explicitly revised.

## Immutable materialization evidence

### Parent materialization

- run: **`35252106776`**
- analysis commit: **`0e319f86a4a9c7ca085de93bb5b3246606b7d6d0`**
- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- parent projection SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**
- genre relationships: **13,689**
- credit relationships: **58,069**
- production mutation: **false**

Exact lineage to corrected projection:

- unchanged reusable identities: **14,114**
- newly added identities: **2,266**
- removed identities: **1**
- removed QID: **`Q3049630` only**
- changed common entries: **0**

### Delta materialization — COMPLETE

Workflow: `P1 Rebaseline Materialization V2`  
Run: **`35421562708`**  
Production mutation: **false**

Evidence:

- candidate titles: **2,266 / 2,266**
- missing title entities: **0**
- skipped relationships because of missing labels: **0**
- unusable claims: **5**
- reviewed top-up cost estimate: **15,531 D1 rows written**

### Authoritative V3 materialization — COMPLETE / READ-ONLY

Workflow: `P1 Repartition Materialization V3`  
Run: **`35428784454`**  
Analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**  
Artifact: `recommendation-metadata-materialization-v3-repartitioned`

Authoritative normalized graph:

- recommendation titles: **16,380**
- distinct genres: **612**
- distinct people: **37,964**
- title-genre relationships: **16,489**
- title-credit relationships: **70,551**
- global graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**

`scripts/verify_p1_v3_production.py` reconstructs the normalized production graph and requires exact graph SHA equality; counts alone are insufficient.

## V3 quota-safe production plan

Parent shard 0 already present in production corresponds exactly to physical modulo-16 partitions **0 and 8**, so those inherited rows are not rewritten.

Locked operation order:

`topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`

| Operation | Reviewed estimated D1 rows | State |
|---|---:|---|
| top-up | 15,531 | **COMPLETE 2026-09-21** |
| physical 1 | 39,575 | **COMPLETE 2026-09-22** |
| physical 2 | 41,741 | **NEXT** |
| physical 3 | 49,159 | pending |
| physical 4 | 39,785 | pending |
| physical 5 | 46,591 | pending |
| physical 6 | 39,371 | pending |
| physical 7 | 41,117 | pending |
| physical 9 | 40,831 | pending |
| physical 10 | 36,946 | pending |
| physical 11 | 40,223 | pending |
| physical 12 | 39,166 | pending |
| physical 13 | 47,836 | pending |
| physical 14 | 41,466 | pending |
| physical 15 | 42,118 | pending |

Largest reviewed operation is **49,159 rows**, below the P1 conservative **80,000 rows/UTC-day** ceiling.

## 2026-09-21 top-up production evidence — COMPLETE

Because the scheduled workflow had not yet appeared during the normal morning window, the existing guarded one-time bridge was refreshed to dispatch the canonical controller. The bridge itself did not write recommendation data and was removed again after the successful operation.

### Canonical controller and writer

- guarded bridge run: **`35563274667`**
- canonical controller run: **`35563283332`**
- guard token: **`35563283332:topup`**
- V3 writer run: **`35563331648`**
- actual D1 rows written: **14,985**
- reviewed estimate: **15,531**
- writer artifact ID: **`10622768410`**
- writer artifact SHA-256: **`f72d0d6b2df334045977a6f758e57303674e775379586dbf91c0f8870bb13952`**

Top-up exact slice:

- recommendation titles added: **250**
- genre input upserts: **80**
- people input upserts: **1,620**
- title-genre links: **317**
- title-credit links: **1,695**

Production totals after top-up:

- recommendation titles: **1,994**
- genres: **251**
- people: **7,595**
- title-genre relationships: **1,958**
- title-credit relationships: **8,626**

Integrity after write remained clean: zero orphan title-genre relationships, zero orphan title-credit relationships, zero invalid genre provenance and zero invalid credit provenance.

Delayed scheduled controller run **`35563394971`** later found the existing guard `35563283332:topup`, emitted `P1_V3_DAILY_WRITE_ALREADY_USED`, and skipped every mutation step. This proved one-mutation-per-UTC-day race safety.

## 2026-09-22 physical shard 1 production evidence — COMPLETE

Physical shard 1 was executed entirely by the **permanent scheduled P1 path**. No temporary/manual bridge was used.

### Background-write freeze

- workflow: `P1 Background Write Coordinator`
- run: **`35687988196`**
- event: `schedule`
- result: **success**
- `main` head at execution: **`92c16a282be1cbd85ecde4c2ee2f465c72f7806b`**

Catalogue-mutating background growth remained frozen before the P1 write.

### Canonical quota-safe controller

- workflow: `P1 Quota-Safe Daily Resume`
- run: **`35689533994`**
- run number: **9**
- event: **`schedule`**
- result: **success**
- selected operation: **physical shard `1`**
- reviewed estimated cost: **39,575 rows**
- guard UTC date: **2026-09-22**
- exact guard token: **`35689533994:1`**
- cleanup state: **complete**
- `topup` state: **complete**
- shard 1 pre-state: **not_started**

The controller restored and verified the immutable V3 artifact, validated the locked projection and graph fingerprints, bound the established production D1 database, confirmed a fresh UTC quota window, proved the first incomplete operation was shard 1, validated the reviewed cost against the 80,000-row ceiling, reserved the day and dispatched exactly one writer.

### V3 writer

- workflow: `Recommendation Metadata Production Write V3`
- run: **`35689574657`**
- event: `workflow_dispatch`
- result: **success**
- operation: **`1`**
- guard token: **`35689533994:1`**
- reviewed estimate: **39,575 rows**
- actual D1 rows written: **37,791**
- executable SHA-256: **`07245500dd8a64fffe5f8d607a187c2cf918f97611696daa5442324ef8fce977`**
- writer artifact: `recommendation-metadata-production-write-v3-write_operation-1`
- artifact ID: **`10677492933`**
- artifact ZIP SHA-256: **`9968b81b7c12347be42797ca9a35eae5eb391869fc2b565bbe79394cb3f2d4d3`**

Before mutation, the writer revalidated the immutable V3 analysis lineage, exact artifact/projection/graph/executable fingerprints, source cleanup state, live corrected projection **16,380 / 6,562 / 9,818**, zero cross-type collisions, exact guard ownership and shard 1 state exactly `not_started`.

Shard 1 exact reviewed slice and post-write result:

- recommendation titles: **1,030 / 1,030**
- title-genre relationships: **969 / 969**
- title-credit relationships: **4,156 / 4,156**
- post-state: **complete**

### Production totals after shard 1

- recommendation titles: **3,024**
- genres: **303**
- people: **10,632**
- title-genre relationships: **2,927**
- title-credit relationships: **12,782**

Integrity after shard 1:

- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

The final full-graph verifier and final Catalogue Quality exit gate were intentionally not run by the writer because the production population is still incomplete.

### Independent read-only observability corroboration

`P1 Production Status Snapshot` run **`35692983180`** completed successfully after the shard 1 writer without any D1 mutation.

It independently observed:

- completed operations: **2 / 15** (`topup`, `1`)
- overall operation state: **`in_progress`**
- next operation: **`2`**
- next reviewed cost: **41,741 rows**
- source cleanup state: **`complete`**
- P1 exit ready: **false**
- `topup`: **complete**
- shard `1`: **complete**
- shard `2`: **not_started**

Snapshot artifact:

- artifact: `p1-production-status-35692983180`
- artifact ID: **`10679491944`**
- artifact ZIP SHA-256: **`41c3aa624325a123063468d443fb78098fabc5a45863187ab1513fb34e1ac34d`**

This read-only snapshot matches the writer post-state exactly and confirms the operation prefix is safe and contiguous.

## Production orchestration safety

PR **#32** merged the corrected 16,380-title V3 orchestration into `main`.

PR **#34** made the background-write freeze coordinator idempotent. Catalogue-mutating growth workflows remain frozen during P1.

PR **#37** added the P1 observability/status surface.

PR **#39** changed the shared Cloudflare D1 bootstrap to fail closed if the established production database is missing; database creation now requires explicit opt-in.

PR **#41** recorded the Sep21 `topup` evidence.

PR **#42** removed the temporary Sep21 one-time bridge. The permanent scheduled controller is again the only normal production-population path.

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

The daily controller is scheduled at **00:25 UTC**, but GitHub scheduled workflows may start later. Safety depends on the UTC guard row, not on exact scheduler timing.

## Remaining P1 gates

1. reviewed media-identity corrections ✅
2. stale catalogue/background write freeze ✅
3. 2,266-identity delta materialization ✅
4. exact 16,380-title V3 graph assembly/attestation ✅
5. quota-safe physical write plan ✅
6. V3 orchestration review/merge ✅
7. reviewed source cleanup ✅
8. **V3 top-up ✅**
9. **physical shard 1 ✅**
10. physical shards **2–7 and 9–15** ⏳ — **13 operations remain**
11. final exact production graph verification ⏳
12. Catalogue Quality V1 **S0 = 0 / S1 = 0** ⏳
13. final production evidence + mark P1 COMPLETE ⏳

## Next operation

On the next fresh UTC quota day, the controller should observe:

- `topup` = complete
- physical shard `1` = complete
- physical shard `2` = not_started

It should then reserve the new UTC day for **physical shard 2**, whose reviewed conservative cost is **41,741 D1 rows written**.

Do not reset, delete or reuse the 2026-09-20, 2026-09-21 or 2026-09-22 quota-guard rows.

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the normalized production graph exactly matches V3 graph SHA `9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`, referential/provenance checks pass, reviewed source cleanup remains exact, and post-write Catalogue Quality is **S0 = 0 / S1 = 0**.

P2 production implementation does not begin from a partial P1 materialization.
