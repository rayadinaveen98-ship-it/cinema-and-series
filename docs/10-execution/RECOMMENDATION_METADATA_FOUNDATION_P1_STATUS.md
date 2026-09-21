# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — TOP-UP COMPLETE  
**Date:** 2026-09-21  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. The corrected V3 orchestration is merged to `main`, the reviewed source-identity cleanup completed on **2026-09-20 UTC**, and the first corrected V3 recommendation operation — **`topup`** — completed successfully on **2026-09-21 UTC**.

The next eligible production recommendation operation is **physical shard 1**, reviewed at a conservative **39,575 D1 rows written**.

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
| physical 1 | 39,575 | **NEXT** |
| physical 2 | 41,741 | pending |
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

Because the scheduled workflow had not yet appeared during the normal morning window, the existing guarded one-time bridge was refreshed to dispatch the canonical controller. The bridge itself did not write recommendation data.

### Bridge

- workflow: `P1 Run Today Once`
- run: **`35563274667`**
- trigger commit: **`cb76f824a9c6e67d02da7b97192f3e3df646e8f5`**
- result: **success**

### Canonical quota-safe controller

- workflow: `P1 Quota-Safe Daily Resume`
- run: **`35563283332`**
- result: **success**
- selected operation: **`topup`**
- reviewed estimated cost: **15,531 rows**
- guard token: **`35563283332:topup`**
- guard UTC date: **2026-09-21**
- cleanup state before planning: **complete**
- top-up pre-state: **not_started**

The controller verified the immutable V3 artifact, exact projection/graph fingerprints, existing production D1 binding, fresh UTC quota window and operation cost before reserving the day and dispatching the writer.

### V3 writer

- workflow: `Recommendation Metadata Production Write V3`
- run: **`35563331648`**
- result: **success**
- operation: **`topup`**
- actual D1 rows written: **14,985**
- reviewed estimate: **15,531**
- writer artifact: `recommendation-metadata-production-write-v3-write_operation-topup`
- artifact ID: **`10622768410`**
- artifact ZIP SHA-256: **`f72d0d6b2df334045977a6f758e57303674e775379586dbf91c0f8870bb13952`**

The writer revalidated, before mutation:

1. explicit production authorization,
2. immutable V3 analysis run `35428784454`,
3. analysis-commit ancestry,
4. exact artifact attestation SHA,
5. exact projection and graph SHA,
6. exact selected executable SHA,
7. reviewed source cleanup exact state,
8. live corrected projection **16,380 / 6,562 / 9,818**, collision count **0**,
9. exact daily guard ownership `35563283332:topup`,
10. top-up state exactly `not_started`.

After import, the top-up slice verified exactly complete:

- recommendation titles added: **250**
- genre input upserts: **80**
- people input upserts: **1,620**
- title-genre links: **317**
- title-credit links: **1,695**

### Production totals after top-up

- recommendation titles: **1,994**
- genres: **251**
- people: **7,595**
- title-genre relationships: **1,958**
- title-credit relationships: **8,626**

Integrity after write:

- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

### Delayed scheduled-run race safety — PROVEN

GitHub later emitted the scheduled controller after the manual guarded controller had already reserved the day:

- delayed scheduled controller run: **`35563394971`**
- event: `schedule`
- result: **success**

It read the existing daily guard row:

- UTC date: `2026-09-21`
- projection SHA: corrected V3 projection
- `workflow_run_id`: **`35563283332:topup`**

The controller printed `P1_V3_DAILY_WRITE_ALREADY_USED` and skipped cleanup state discovery, operation discovery, quota reservation, writer dispatch and final-verification dispatch. This proves the one-mutation-per-UTC-day guard works even when the manual guarded resume and a delayed scheduled run overlap.

No second P1 production mutation is permitted on 2026-09-21.

## Production orchestration safety

PR **#32** merged the corrected 16,380-title V3 orchestration into `main`.

PR **#34** made the background-write freeze coordinator idempotent. Catalogue-mutating growth workflows remain frozen during P1.

PR **#37** added the P1 observability/status surface.

PR **#39** changed the shared Cloudflare D1 bootstrap to fail closed if the established production database is missing; database creation now requires explicit opt-in. The normal production deploy subsequently passed using the existing D1 database.

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
9. physical shards **1–7 and 9–15** ⏳ — **14 operations remain**
10. final exact production graph verification ⏳
11. Catalogue Quality V1 **S0 = 0 / S1 = 0** ⏳
12. final production evidence + mark P1 COMPLETE ⏳

## Next operation

On the next fresh UTC quota day, the controller should observe:

- `topup` = complete
- physical shard `1` = not_started

It should then reserve the new UTC day for **physical shard 1**, whose reviewed conservative cost is **39,575 D1 rows written**.

Do not reset, delete or reuse the 2026-09-21 guard row.

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the normalized production graph exactly matches V3 graph SHA `9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`, referential/provenance checks pass, reviewed source cleanup remains exact, and post-write Catalogue Quality is **S0 = 0 / S1 = 0**.

P2 production implementation does not begin from a partial P1 materialization.
