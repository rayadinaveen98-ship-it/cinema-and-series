# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — SHARD 3 COMPLETE  
**Date:** 2026-09-24  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. The corrected V3 orchestration is merged to `main`, reviewed source cleanup completed on **2026-09-20 UTC**, `topup` completed on **2026-09-21 UTC**, physical shard 1 on **2026-09-22 UTC**, physical shard 2 on **2026-09-23 UTC**, and **physical shard 3 completed successfully on 2026-09-24 UTC** through the permanent scheduled controller.

The next eligible production recommendation operation is **physical shard 4**, reviewed at a conservative **39,785 D1 rows written**.

Completed recommendation operations: **4 / 15** (`topup`, `1`, `2`, `3`).  
Remaining recommendation operations: **11**.

Current production totals after shard 3:

- recommendation titles: **5,085**
- genres: **374**
- people: **16,894**
- title-genre relationships: **4,975**
- title-credit relationships: **22,598**

Current integrity/provenance counters:

- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

P1 exit-ready remains **false**.

## Corrected frozen projection

The authoritative recommendation projection remains exactly:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**
- cross-type collisions after reviewed cleanup: **0**

This fingerprint supersedes the obsolete 14,115-title / 8-shard production-population contract.

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

Reviewed identities:

- **`Q3049630` — Eko Eko Azarak**: non-audiovisual manga-series identity; excluded from Movie and Series recommendation projection.
- **`Q3146368` — Shattered City: The Halifax Explosion**: reviewed miniseries identity; canonicalized to **Series**.

Unknown or unreviewed Movie/Series collisions remain hard failures.

### Production cleanup evidence — 2026-09-20

- controller: **`35490594774`**
- cleanup writer: **`35490618771`**
- guard operation: `cleanup`
- deleted exactly:
  - `movies / wd-Q3049630`
  - `series_titles / series-wd-Q3049630`
  - `catalogue_titles / wd-Q3146368`
- retained canonical row: `series_titles / series-wd-Q3146368`
- post-cleanup projection: **16,380 = 6,562 Movie + 9,818 Series**
- cross-type collisions: **0**
- artifact: `p1-reviewed-source-identity-cleanup-35490618771`
- artifact ID: **`10598937124`**
- artifact ZIP SHA-256: **`152dda1963c2f2967b9a904ccc5e497aa4cacefa830deba1b6643bc7d1cb65d6`**

## Schema and quota guard

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the one-row-per-UTC-day D1 mutation reservation. Its legacy `shard_index` range remains `0..7`; V3 binds the exact operation in `workflow_run_id` as `<controller-run-id>:<operation>`.

P1 owns migrations **0021** and **0022**. Do not add `0023+` to `main` until P1 closes unless the roadmap is explicitly revised.

Historical guard rows are audit evidence and must not be reset, deleted, or reused to force another mutation.

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

Exact lineage to the corrected projection:

- unchanged reusable identities: **14,114**
- newly added identities: **2,266**
- removed identities: **1**
- removed QID: **`Q3049630` only**
- changed common entries: **0**

### Delta materialization — COMPLETE

- workflow: `P1 Rebaseline Materialization V2`
- run: **`35421562708`**
- production mutation: **false**
- candidates: **2,266 / 2,266**
- missing title entities: **0**
- skipped relationships because of missing labels: **0**
- unusable claims: **5**
- reviewed top-up estimate: **15,531 D1 rows**

### Authoritative V3 materialization — COMPLETE / READ-ONLY

- workflow: `P1 Repartition Materialization V3`
- run: **`35428784454`**
- analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**
- artifact: `recommendation-metadata-materialization-v3-repartitioned`
- artifact ID: **`10579264534`**
- downloaded artifact ZIP SHA-256: **`059b989bd4e8dae069039f74c7415ddaa3070c9217ac8b6e428b9992f6545bc5`**

Authoritative normalized graph:

- recommendation titles: **16,380**
- distinct genres: **612**
- distinct people: **37,964**
- title-genre relationships: **16,489**
- title-credit relationships: **70,551**
- global graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**

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
| physical 4 | 39,785 | **NEXT** |
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

## Completed production evidence prefix

### 2026-09-21 — V3 top-up COMPLETE

- guarded bridge run: **`35563274667`**
- controller: **`35563283332`**
- guard: **`35563283332:topup`**
- writer: **`35563331648`**
- reviewed estimate: **15,531**
- actual D1 rows written: **14,985**
- exact slice: **250 titles / 317 title-genres / 1,695 title-credits**
- production totals: **1,994 / 251 / 7,595 / 1,958 / 8,626**
- integrity/provenance violations: **0**
- artifact ID: **`10622768410`**
- artifact ZIP SHA-256: **`f72d0d6b2df334045977a6f758e57303674e775379586dbf91c0f8870bb13952`**

Delayed scheduled controller **`35563394971`** later observed the existing guard and skipped every mutation step, proving same-day race safety.

### 2026-09-22 — physical shard 1 COMPLETE

- background coordinator: **`35687988196`** — success
- controller: **`35689533994`**
- guard: **`35689533994:1`**
- writer: **`35689574657`**
- reviewed estimate: **39,575**
- actual D1 rows written: **37,791**
- executable SHA-256: **`07245500dd8a64fffe5f8d607a187c2cf918f97611696daa5442324ef8fce977`**
- exact slice: **1,030 titles / 969 title-genres / 4,156 title-credits**
- production totals: **3,024 / 303 / 10,632 / 2,927 / 12,782**
- integrity/provenance violations: **0**
- artifact ID: **`10677492933`**
- artifact ZIP SHA-256: **`9968b81b7c12347be42797ca9a35eae5eb391869fc2b565bbe79394cb3f2d4d3`**
- read-only snapshot `35692983180` independently confirmed `topup,1` complete and operation 2 next

### 2026-09-23 — physical shard 2 COMPLETE

- background coordinator: **`35819061430`** — success
- controller: **`35820142892`**
- controller run number: **10**
- controller event: **schedule**
- controller head: **`78005df4a6c9d91aaa1a84938f56c50b07708c12`**
- guard: **`35820142892:2`**
- writer: **`35820184949`**
- writer run number: **3**
- reviewed estimate: **41,741**
- actual D1 rows written: **39,259**
- executed D1 queries: **10,687**
- D1 rows read: **11,110**
- executable SHA-256: **`8b167ee10e42ddba4903e0f7b4e424ec29d7ec24d375d2193446f5b85ecce36c`**
- exact slice: **1,005 titles / 1,007 title-genres / 4,432 title-credits**
- production totals: **4,029 / 342 / 13,595 / 3,934 / 17,214**
- integrity/provenance violations: **0**
- controller artifact ID: **`10732554725`**
- controller artifact ZIP SHA-256: **`4f3942d74d018e3a009e52b3e7563498e227896eea55db1685fa3b6a45f70f9e`**
- writer artifact ID: **`10733260919`**
- writer artifact ZIP SHA-256: **`81e726460eaba92d6590173fa2fb2b6762e2995addabf37b54a199391fd62deb`**

Read-only snapshot run **`35823982162`** later independently confirmed:

- completed prefix: `topup,1,2`
- completed operations: **3 / 15**
- operation 3: **not_started**
- next operation: **3**
- current guard: `35820142892:2`
- production totals: **4,029 / 342 / 13,595 / 3,934 / 17,214**
- health violations: **0**
- exit-ready: **false**
- artifact ID: **`10735015860`**
- artifact ZIP SHA-256: **`a6f5a2410ad8e10591bfd16c6c3003b0aec8f7d09f719eed08fbc12b2870695d`**

### 2026-09-24 — physical shard 3 COMPLETE

Physical shard 3 was executed entirely by the **permanent scheduled P1 path**. No manual or temporary bridge was used.

Background-write freeze:

- workflow: `P1 Background Write Coordinator`
- run: **`35956376942`**
- run number: **12**
- event: `schedule`
- result: **success**
- head SHA: **`fd278159e71fbe3501af84831c9fa6bdb234815a`**

Canonical quota-safe controller:

- workflow: `P1 Quota-Safe Daily Resume`
- run: **`35958174447`**
- run number: **11**
- event: `schedule`
- result: **success**
- head SHA: **`fd278159e71fbe3501af84831c9fa6bdb234815a`**
- selected operation: **physical shard `3`**
- reviewed estimated cost: **49,159 rows**
- guard UTC date: **2026-09-24**
- exact guard token: **`35958174447:3`**
- source cleanup: **complete**
- `topup`, shard 1, shard 2: **complete**
- shard 3 pre-state: **not_started**
- controller artifact: `p1-quota-safe-daily-resume-v3-35958174447`
- artifact ID: **`10790902399`**
- artifact ZIP SHA-256: **`eb4f0b4ff5e604034ebf7a9137897be7b86a23ea098c6560734661549df24493`**

V3 writer:

- workflow: `Recommendation Metadata Production Write V3`
- run: **`35958228439`**
- run number: **4**
- event: `workflow_dispatch`
- result: **success**
- mode: `write_operation`
- operation: **`3`**
- guard: **`35958174447:3`**
- reviewed estimate: **49,159 rows**
- actual D1 rows written: **45,683**
- executed D1 queries: **12,550**
- D1 rows read: **13,562**
- executable SHA-256: **`c0aa44243de94f3d37c89ef854da68ff415c4253781e7f739bf001e5e4589c39`**
- writer artifact: `recommendation-metadata-production-write-v3-write_operation-3`
- artifact ID: **`10791162083`**
- artifact ZIP SHA-256: **`80175efcdb856167d3d79970277a7ee17dff50a5abfbef5ea502e6706b3569f5`**

Before mutation the writer revalidated immutable V3 lineage, exact artifact/projection/graph/executable fingerprints, reviewed source cleanup, live projection **16,380 / 6,562 / 9,818**, cross-type collisions **0**, exact guard ownership, and shard 3 exactly `not_started`.

Shard 3 exact slice and post-state:

- recommendation titles: **1,056 / 1,056**
- title-genre relationships: **1,041 / 1,041**
- title-credit relationships: **5,384 / 5,384**
- post-state: **complete**

Production totals after shard 3:

- recommendation titles: **5,085**
- genres: **374**
- people: **16,894**
- title-genre relationships: **4,975**
- title-credit relationships: **22,598**

Post-write integrity/provenance:

- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

The final full-graph verifier and final Catalogue Quality exit gate were intentionally skipped because production population remains incomplete. This is expected.

A post-shard-3 Sep24 read-only status snapshot had **not been observed at the time this evidence was recorded**. Do not infer or fabricate one; later snapshot evidence may be appended separately.

## Physical shard 4 offline preflight — PASS / READ-ONLY

The next operation was rehearsed directly from the immutable reviewed V3 artifact without Cloudflare credentials, D1 access, or mutation.

- operation: **physical shard 4**
- recommendation titles: **1,003**
- title-genre relationships: **975**
- title-credit relationships: **4,202**
- genre input upserts: **184**
- people input upserts: **3,826**
- data statement count: **10,190**
- executable line count: **10,198**
- reviewed estimated D1 rows: **39,785**
- headroom below 80,000 P1 ceiling: **40,215**
- headroom below 100,000 free daily allowance: **60,215**
- executable SHA-256: **`41596755c34154128f3a147817e54e6d6e1fba2df3a6eb1e80edbe003c67467e`**
- materialization SHA-256: **`60bdea1bed4530c2c646e38210c7a6e62fb0bf9654f91fd82796eac9c365d6e7`**
- cost manifest SHA-256: **`c292705aabd47ed8353f1594f45291d773a9a7d7b855711f128ae5b190da770e`**
- report SHA-256: **`515b8089d39f7ab37921710de17558fa0f734de06b33b07d0f6b486e11f0ce88`**
- reviewed SQL SHA-256: **`d12d0bcb3feb7b00f8648ecb12e6ea6814344617df6b587a7ce87bddbb5f7db9`**

Offline PASS is rehearsal only. The next live writer must still pass the fresh-day guard, live projection, cleanup, operation-state, executable-attestation, integrity, and provenance checks.

## Production orchestration safety

Relevant merged safeguards/evidence:

- PR **#32** — corrected 16,380-title V3 orchestration
- PR **#34** — idempotent background-write freeze coordinator
- PR **#37** — P1 observability/status surface
- PR **#39** — fail-closed existing-production-D1 binding
- PR **#41** — Sep21 top-up evidence
- PR **#42** — removed temporary Sep21 bridge; permanent controller restored as normal path
- PR **#43** — Sep22 shard 1 evidence
- PR **#46** — deterministic final-exit evidence checklist
- PR **#47** — Sep23 shard 2 evidence
- PR **#48** — reusable offline V3 operation preflight
- PR **#49** — Sep23 read-only snapshot corroboration

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

The daily controller is scheduled at **00:25 UTC**, but GitHub scheduled workflows may start later. Safety depends on the UTC guard row, not exact scheduler timing.

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
10. **physical shard 2 ✅**
11. **physical shard 3 ✅**
12. physical shards **4–7 and 9–15** ⏳ — **11 operations remain**
13. final exact production graph verification ⏳
14. Catalogue Quality V1 **S0 = 0 / S1 = 0** ⏳
15. final production evidence + mark P1 COMPLETE ⏳

## Next operation

On the next fresh UTC quota day, the controller must observe:

- `topup` = complete
- physical shard `1` = complete
- physical shard `2` = complete
- physical shard `3` = complete
- physical shard `4` = not_started

It should then reserve the new UTC day for **physical shard 4**, whose reviewed conservative cost is **39,785 D1 rows written**.

Do **not** execute shard 4 on 2026-09-24 UTC. The Sep24 mutation slot is already owned by **`35958174447:3`**.

Do not reset, delete, or reuse the 2026-09-20, 2026-09-21, 2026-09-22, 2026-09-23, or 2026-09-24 quota-guard rows.

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the normalized production graph exactly matches V3 graph SHA `9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`, referential/provenance checks pass, reviewed source cleanup remains exact, and post-write Catalogue Quality is **S0 = 0 / S1 = 0**.

P2 production implementation does not begin from a partial P1 materialization.
