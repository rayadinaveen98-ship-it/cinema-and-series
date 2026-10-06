# Recommendation Metadata Foundation P1 — Execution Status

**Status:** FINAL VERIFICATION PASSED — CONTROLLER RETIREMENT PENDING  
**Date:** 2026-10-06  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active, but the full corrected production population is now complete and the final read-only verification has passed.

- source cleanup — **2026-09-20 UTC**
- topup — **2026-09-21 UTC**
- physical shards 1–7, 9–15 — **2026-09-22 through 2026-10-05 UTC**
- completed recommendation operations: **15 / 15**
- remaining recommendation operations: **0**
- production totals: **16,380 titles / 612 genres / 37,964 people / 16,489 title-genres / 70,551 title-credits**
- current integrity/provenance counters: **0 / 0 / 0 / 0**
- exact corrected projection: **16,380 = 6,562 Movie + 9,818 Series**
- projection SHA-256: **f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6**
- normalized production graph SHA-256: **9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78**
- final verification run: **37424321924**
- final verification mode: **verify_final / final**
- final verification artifact: **recommendation-metadata-production-write-v3-verify_final-final**
- final verification artifact ID: **11394510831**
- final verification artifact digest: **sha256:2300a514b88829d99f8334af213472457ee930a425946ac052c7e9ab5081374f**
- Catalogue Quality V1: **S0 = 0 / S1 = 0**
- final graph verification: **passed with production_mutation=false**
- controller retirement: **pending**

No further recommendation metadata mutation is authorized. P1 is **not yet declared COMPLETE** because the permanent controller must still observe the successful final-verification artifact and retire the daily resume workflow, after which the post-P1 handoff can be recorded.

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
| physical 9 | 40,831 | **COMPLETE 2026-09-29** |
| physical 10 | 36,946 | **COMPLETE 2026-09-30** |
| physical 11 | 40,223 | **COMPLETE 2026-10-01** |
| physical 12 | 39,166 | **NEXT** |
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
| 2026-09-29 | 9 | `36528199977` / `36528199977:9` | `36528269733` | 40,831 | **36,389** | 981 / 1,009 / 4,314 | 10,208 / 500 / 27,603 / 10,192 / 44,562 |
| 2026-09-30 | 10 | `36674647947` / `36674647947:10` | `36674715781` | 36,946 | **33,074** | 991 / 962 / 3,778 | 11,199 / 525 / 29,388 / 11,154 / 48,340 |
| 2026-10-01 | 11 | `36823178729` / `36823178729:11` | `36823254704` | 40,223 | **35,727** | 1,077 / 1,053 / 4,167 | 12,276 / 540 / 31,147 / 12,207 / 52,507 |

Every completed writer above ended with exact operation state `complete` and zero orphan/provenance violations.

### Selected immutable executable evidence for recent operations

- shard 4 executable SHA-256: **`41596755c34154128f3a147817e54e6d6e1fba2df3a6eb1e80edbe003c67467e`**
- shard 5 executable SHA-256: **`0b72bdc6c5bd4c45464c1df4850187fa203b274f5063ea555e76ab4eaf79379d`**
- shard 6 executable SHA-256: **`650962f1330f73839cdac79e0e7316d468d58d7e679b890c3368f9a4f449c3c0`**
- shard 7 executable SHA-256: **`faa5e20950c3c5e74959e93c1fb53d3ff962d3c9fae0a173bfa40a066d590a8d`**
- shard 9 executable SHA-256: **`8484dcd0a32752ada05df5ceb64c9212872da2913977c5f081d3fe25dec3512a`**
- shard 10 executable SHA-256: **`39661b7d1319bbfd5e8131303b8f5bae3ce8fe136f99a83dc9bc7cc2172d6840`**
- shard 11 executable SHA-256: **`a3775ac4ca0a3283044f9a8216589a5b0dd436f9e98aeb3d9f903eba87599a3d`**

Recent writer artifacts:

- shard 4 artifact ID **`10848045964`**, ZIP SHA-256 **`bc90af78c7f20deeae698c7b534ce1f83f1e27d8740e5939d1299e7a1fb78344`**
- shard 5 artifact ID **`10898702252`**, ZIP SHA-256 **`197aec78e8b5c3bf8a16c1716aa978a115f18359117db4118eeff25b5db39c0e`**
- shard 6 artifact ID **`10924621403`**, ZIP SHA-256 **`2f86451c30dc90a2cc61f0af11034251b3c915a46ceb2b7e88faa1d1345b1a2a`**
- shard 7 artifact ID **`10952912804`**, ZIP SHA-256 **`e4ac6ca849692361a3445ce5335410e26383a0f279aa1e339678c52b94e6b338`**
- shard 9 artifact ID **`11015557260`**, ZIP SHA-256 **`683e0098de18b52572dda5b6e7cd1e5a8312d4ca3126671934bbd03edd96ac79`**
- shard 10 artifact ID **`11079148837`**, ZIP SHA-256 **`8a93664107215f04d1ac27db5aa5c53955e1b9db7e847c5f0b7c92f79fa8a06a`**
- shard 11 artifact ID **`11143299196`**, ZIP SHA-256 **`7482abd57a4e29971946ba7a297ec5c34d2a02d6047dfcc292438d95a9a0a32f`**

### 2026-10-01 shard-11 production evidence

Controller run **`36823178729`** reserved the UTC mutation day for operation `11`, and writer run **`36823254704`** verified:

- quota-guard owner: **`36823178729:11`**
- guard date: **2026-10-01 UTC**
- guard shard index: **3**
- live projection: **16,380 = 6,562 Movie + 9,818 Series**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- reviewed estimated rows: **40,223**
- actual D1 rows written: **35,727**
- exact completed slice: **1,077 / 1,053 / 4,167**
- post totals: **12,276 / 540 / 31,147 / 12,207 / 52,507**
- orphan title-genre relationships: **0**
- orphan title-credit relationships: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**
- artifact ID: **`11143299196`**
- artifact ZIP SHA-256: **`7482abd57a4e29971946ba7a297ec5c34d2a02d6047dfcc292438d95a9a0a32f`**

### 2026-09-30 shard-10 production evidence

Controller run **`36674647947`** reserved the UTC mutation day for operation `10`, and writer run **`36674715781`** verified:

- quota-guard owner: **`36674647947:10`**
- reviewed estimated rows: **36,946**
- actual D1 rows written: **33,074**
- exact completed slice: **991 / 962 / 3,778**
- post totals: **11,199 / 525 / 29,388 / 11,154 / 48,340**
- integrity/provenance violations: **0**
- artifact ID: **`11079148837`**

### 2026-09-29 shard-9 production evidence

Controller run **`36528199977`** reserved the UTC mutation day for operation `9`, and writer run **`36528269733`** verified:

- quota-guard owner: **`36528199977:9`**
- reviewed estimated rows: **40,831**
- actual D1 rows written: **36,389**
- exact completed slice: **981 / 1,009 / 4,314**
- post totals: **10,208 / 500 / 27,603 / 10,192 / 44,562**
- integrity/provenance violations: **0**
- artifact ID: **`11015557260`**

### Historical read-only snapshot evidence

Workflow run **`36300254259`** independently confirmed the state immediately before shard 7:

- source cleanup: **complete**
- completed prefix: `topup,1,2,3,4,5,6`
- completed operations: **7 / 15**
- shard 7: **not_started**
- shard 7 expected slice: **1,045 titles / 1,119 title-genres / 4,286 title-credits**
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
16. physical shard 9 ✅
17. physical shard 10 ✅
18. physical shard 11 ✅
19. physical shard 12 ✅
20. physical shard 13 ✅
21. physical shard 14 ✅
22. physical shard 15 ✅
23. final exact production graph verification ✅ — run **37424321924**
24. Catalogue Quality V1 **S0 = 0 / S1 = 0** ✅ — run **37424321924**
25. final production verification artifact/evidence preserved ✅ — artifact **11394510831**
26. mark P1 COMPLETE / retire P1 controller ⏳

## Final population checkpoint — 2026-10-05 UTC

The scheduled V3 writers completed the final three physical operations without bypassing the daily guard:

| Operation | Controller / guard | Writer | Reviewed | Actual D1 rows | Artifact |
|---|---|---|---:|---:|---|
| 13 | `37099854552:13` | `37099902617` | 47,836 | **41,768** | `11266145036` / `865a0ff699937c11b92e3000d1154d039b2d506aa73b5d4fd1a96cd764b8b29b` |
| 14 | `37181634385:14` | `37181690483` | 41,466 | **36,370** | `11294419178` / `c89d640c8e89a2aeaa5f56ab320ccd39eae7c612a2a22a6547bd9081ba6edcfc` |
| 15 | `37269736740:15` | `37269800819` | 42,118 | **37,002** | `11327634324` / `151e045055cb63cbaf048e8ec39f3e8a83c7bc3e4a48ef94e44c91e7dbbc088f` |

The 2026-10-05 read-only snapshot `37274482671` independently reports:

- completed operations: **15 / 15**
- overall operation state: `operations_complete`
- exit gate: `ready_for_final_verification`
- final verification eligible: **true**
- next operation: `complete`
- P1 exit-ready: **true**
- source cleanup: complete
- production counts: **16,380 / 612 / 37,964 / 16,489 / 70,551**
- orphan/provenance violations: **0 / 0 / 0 / 0**
- exact projection SHA: `f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`

The population is complete, but this checkpoint does **not** declare P1 complete. The exact production graph verifier, Catalogue Quality V1 S0/S1 gate, deterministic completion attestation, final verification artifact, and controller retirement remain mandatory.

## Final verification checkpoint — 2026-10-06 UTC

The permanent P1 controller run **37424224029** detected next_operation=complete and dispatched the final read-only verifier as **run 37424321924** with mode=verify_final and operation=final. No recommendation write was performed by this verification run.

Verified evidence:

- immutable V3 artifact attestation SHA-256: **8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986**
- corrected projection SHA-256: **f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6**
- production graph SHA-256: **9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78**
- production counts: **16,380 / 612 / 37,964 / 16,489 / 70,551**
- orphan title-genres: **0**
- orphan title-credits: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**
- Catalogue Quality V1: **S0 = 0 / S1 = 0**
- final evidence artifact ID: **11394510831**
- final evidence artifact digest: **sha256:2300a514b88829d99f8334af213472457ee930a425946ac052c7e9ab5081374f**

The verifier explicitly reports production_mutation=false. The daily controller remains intentionally unretired until it observes this artifact on a controller run and disables itself. Do not perform any further P1 recommendation mutation.

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the normalized production graph exactly matches V3 graph SHA `9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`, referential/provenance checks pass, reviewed source cleanup remains exact, and post-write Catalogue Quality is **S0 = 0 / S1 = 0**.

The deterministic P1 completion attestation may be emitted only after those final verification gates pass. P2 production implementation does not begin from a partial P1 materialization.
