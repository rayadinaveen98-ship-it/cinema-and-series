# Recommendation Metadata Foundation P1 — Final Exit Evidence Checklist

**Status:** PREPARED / USE ONLY AFTER ALL V3 PRODUCTION OPERATIONS COMPLETE  
**Prepared:** 2026-09-22  
**Checkpoint updated:** 2026-09-27  
**Active phase:** P1 — Recommendation Metadata Foundation  
**Authoritative status:** `docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md`

## Purpose

Make P1 closure deterministic and auditable.

This document does **not** mark P1 complete. It defines the evidence that must exist before the authoritative status may change to COMPLETE and before P2 production implementation begins.

No gate may be waived because headline counts look correct. P1 closes only when identity, graph, provenance, quality, quota lineage, final verification, and operational handoff all pass together.

---

## Frozen reviewed target

### Projection target

- recommendation candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- cross-type collisions: **0**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**

### Graph target

- `recommendation_titles`: **16,380**
- distinct `genres`: **612**
- distinct `people`: **37,964**
- `title_genres`: **16,489**
- `title_credits`: **70,551**
- normalized graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**
- immutable V3 materialization run: **`35428784454`**
- V3 analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**

Counts alone are insufficient. Final production must reproduce the exact reviewed normalized graph SHA.

---

## Locked production operation sequence

`topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`

| Operation | Reviewed max-cost estimate | Current state |
|---|---:|---|
| topup | 15,531 | **complete 2026-09-21** |
| 1 | 39,575 | **complete 2026-09-22** |
| 2 | 41,741 | **complete 2026-09-23** |
| 3 | 49,159 | **complete 2026-09-24** |
| 4 | 39,785 | **complete 2026-09-25** |
| 5 | 46,591 | **complete 2026-09-26** |
| 6 | 39,371 | **complete 2026-09-27** |
| 7 | 41,117 | **next** |
| 9 | 40,831 | pending |
| 10 | 36,946 | pending |
| 11 | 40,223 | pending |
| 12 | 39,166 | pending |
| 13 | 47,836 | pending |
| 14 | 41,466 | pending |
| 15 | 42,118 | pending |

Physical partitions 0 and 8 are inherited from reviewed parent shard 0 and must not be rewritten as full V3 operations.

For every operation, final evidence must record:

- UTC quota date
- controller run ID
- exact guard token `<controller-run-id>:<operation>`
- writer run ID and conclusion
- reviewed estimated write cost
- actual D1 rows written
- selected executable SHA when applicable
- writer artifact ID/digest
- exact pre-state and post-state
- post-write global integrity/provenance counters

Any `partial`, `overfilled`, unknown guard ownership, wrong executable fingerprint, or failed post-state blocks P1 exit.

---

## Completed evidence prefix

### Reviewed source cleanup — 2026-09-20 UTC

- controller: **`35490594774`**
- cleanup writer: **`35490618771`**
- deleted exactly three noncanonical rows
- retained canonical `series_titles / series-wd-Q3146368`
- recaptured projection: **16,380 = 6,562 Movie + 9,818 Series**
- cross-type collisions: **0**
- artifact ID: **`10598937124`**
- artifact ZIP SHA-256: **`152dda1963c2f2967b9a904ccc5e497aa4cacefa830deba1b6643bc7d1cb65d6`**

### Recommendation production operations — 2026-09-21 through 2026-09-27

| UTC date | Operation | Guard | Writer | Reviewed | Actual rows | Post-state |
|---|---|---|---|---:|---:|---|
| 2026-09-21 | topup | `35563283332:topup` | `35563331648` | 15,531 | **14,985** | complete |
| 2026-09-22 | 1 | `35689533994:1` | `35689574657` | 39,575 | **37,791** | complete |
| 2026-09-23 | 2 | `35820142892:2` | `35820184949` | 41,741 | **39,259** | complete |
| 2026-09-24 | 3 | `35958174447:3` | `35958228439` | 49,159 | **45,683** | complete |
| 2026-09-25 | 4 | `36097101466:4` | `36097154585` | 39,785 | **36,529** | complete |
| 2026-09-26 | 5 | `36219922803:5` | `36219954490` | 46,591 | **42,223** | complete |
| 2026-09-27 | 6 | `36297206014:6` | `36297241170` | 39,371 | **35,501** | complete |

Exact operation slices:

- topup: **250 titles / 317 title-genres / 1,695 title-credits**
- shard 1: **1,030 / 969 / 4,156**
- shard 2: **1,005 / 1,007 / 4,432**
- shard 3: **1,056 / 1,041 / 5,384**
- shard 4: **1,003 / 975 / 4,202**
- shard 5: **1,060 / 1,085 / 5,037**
- shard 6: **1,034 / 1,029 / 4,125**

Recent immutable executable SHA-256 values:

- shard 4: **`41596755c34154128f3a147817e54e6d6e1fba2df3a6eb1e80edbe003c67467e`**
- shard 5: **`0b72bdc6c5bd4c45464c1df4850187fa203b274f5063ea555e76ab4eaf79379d`**
- shard 6: **`650962f1330f73839cdac79e0e7316d468d58d7e679b890c3368f9a4f449c3c0`**

Recent writer artifacts:

- shard 4: ID **`10848045964`**, ZIP SHA-256 **`bc90af78c7f20deeae698c7b534ce1f83f1e27d8740e5939d1299e7a1fb78344`**
- shard 5: ID **`10898702252`**, ZIP SHA-256 **`197aec78e8b5c3bf8a16c1716aa978a115f18359117db4118eeff25b5db39c0e`**
- shard 6: ID **`10924621403`**, ZIP SHA-256 **`2f86451c30dc90a2cc61f0af11034251b3c915a46ceb2b7e88faa1d1345b1a2a`**

Production totals after shard 6:

- recommendation titles: **8,182**
- genres: **452**
- people: **23,728**
- title-genres: **8,064**
- title-credits: **35,962**

Post-write integrity/provenance counters remain **0 / 0 / 0 / 0**.

### 2026-09-27 independent read-only snapshot

Run **`36300254259`** independently confirmed:

- source cleanup = complete
- completed prefix = `topup,1,2,3,4,5,6`
- completed operations = **7 / 15**
- overall operation state = `in_progress`
- shard 7 = **not_started**
- shard 7 current = **0 titles / 0 title-genres / 0 title-credits**
- shard 7 expected = **1,045 / 1,119 / 4,286**
- next operation = `7`
- next reviewed estimate = **41,117**
- current guard = **`36297206014:6`**
- production totals = **8,182 / 452 / 23,728 / 8,064 / 35,962**
- health violations = **0**
- P1 exit-ready = **false**
- snapshot artifact ID = **`10925114272`**
- snapshot artifact ZIP SHA-256 = **`aff4345b93a818ba7149b649289c72be445c24ce5fab5e4919ce1e54a15d036f`**

---

## Gate A — all operations complete

Required final operation states:

- `topup`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `9`, `10`, `11`, `12`, `13`, `14`, `15` = `complete`
- completed operations = **15 / 15**
- next operation = none
- no complete operation after an incomplete gap
- no partial state
- no overfilled state

**Current:** **7 / 15**, so this gate remains **OPEN**.

---

## Gate B — quota-guard audit

Final verification must prove:

1. each mutation date has at most one guard row
2. every guard uses the corrected projection SHA
3. every recommendation write guard binds exact controller + operation
4. historical cleanup/topup/shard guards remain preserved
5. no guard was reset, deleted, or reused
6. failed Sep19 reservation remains historical and unchanged
7. no full-shard 0 or 8 V3 operation exists
8. no unrecognized operation token exists

Current completed prefix includes preserved guards through **`36297206014:6`**.

---

## Gate C — reviewed source identity

Required final source state:

- `Q3049630` absent from Movie and Series recommendation identity
- canonical `series_titles / series-wd-Q3146368` retained
- live recommendation projection exactly **16,380 / 6,562 / 9,818**
- cross-type collisions = **0**

This state has remained exact through shard 6 but must be reverified at final exit.

---

## Gate D — exact production graph verification

Run `scripts/verify_p1_v3_production.py` only after all write operations complete.

Required:

- production normalized graph reconstructs successfully
- graph SHA exactly equals **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- projection SHA remains **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- verifier emits `P1_V3_PRODUCTION_GRAPH_VERIFIED`
- final verification workflow concludes success

Matching counts without matching graph SHA does not satisfy this gate.

---

## Gate E — referential integrity

Required final counters:

- orphan `title_genres` = **0**
- orphan `title_credits` = **0**

Current checkpoint is clean, but final verification is still required.

---

## Gate F — provenance validity

Required final counters:

- invalid genre provenance = **0**
- invalid credit provenance = **0**

Locked canonical relationships remain:

- genre — `P136`
- director — `P57`
- Series creator — `P170`
- cast — `P161`

---

## Gate G — exact final counts

Required final production counts:

- recommendation titles = **16,380**
- genres = **612**
- people = **37,964**
- title-genres = **16,489**
- title-credits = **70,551**

Counts and exact graph SHA must both match.

---

## Gate H — Catalogue Quality V1

Required final result:

- **S0 = 0**
- **S1 = 0**

Preserve workflow/run ID, head SHA, artifact identity/digest, and observations.

---

## Gate I — final read-only status snapshot

Required after all writes and final graph/quality checks:

- source cleanup = complete
- completed operations = **15 / 15**
- next operation = none
- no unsafe state
- final graph verification successful
- Catalogue Quality clean
- P1 exit-ready = true

Snapshot is corroboration, not a replacement for the exact graph verifier.

---

## Gate J — final verification artifact

Expected artifact:

`recommendation-metadata-production-write-v3-verify_final-final`

Record final verifier run ID, artifact ID, ZIP SHA-256, verified graph SHA, and projection SHA.

---

## Gate K — controller retirement

The daily P1 controller retires only after successful final verification evidence exists.

Verify:

- it did not retire after the last write alone
- final verification was read-only
- final verification artifact was observed
- no future scheduled recommendation mutation can continue accidentally

---

## Gate L — frozen background mutator handoff

Before resuming any frozen mutating workflow:

1. P1 must be COMPLETE under this checklist
2. review each frozen workflow against post-P1 strategy
3. do not blindly re-enable obsolete writers
4. keep obsolete 14,115-title / 8-shard path retired
5. record what was resumed and what remains disabled

---

## Gate M — migration ownership handoff

P1 owns:

- `0021_recommendation_metadata_foundation.sql`
- `0022_recommendation_materialization_daily_guard.sql`

Before a later phase adds a migration:

- verify actual `main` migration ordering
- confirm P1 exit is recorded
- rebase dormant/research migration numbering
- assign the first post-P1 migration from actual current `main`

---

## Next-operation rehearsal — physical shard 7

The 2026-09-27 status probe establishes the exact next slice:

- recommendation titles: **1,045**
- title-genres: **1,119**
- title-credits: **4,286**
- current state: **not_started**
- reviewed estimate: **41,117 rows**

This evidence cannot authorize a same-day write. The live controller/writer gates remain mandatory on the next fresh UTC day.

---

## Final evidence record template

Fill only when closure is genuinely ready.

### Production identity

- final `main` commit:
- final UTC verification date:
- corrected projection SHA:
- reviewed graph SHA:

### Operations

- cleanup evidence:
- topup evidence:
- shard 1 evidence:
- shard 2 evidence:
- shard 3 evidence:
- shard 4 evidence:
- shard 5 evidence:
- shard 6 evidence:
- shard 7 evidence:
- shard 9 evidence:
- shard 10 evidence:
- shard 11 evidence:
- shard 12 evidence:
- shard 13 evidence:
- shard 14 evidence:
- shard 15 evidence:

### Final production graph

- recommendation_titles:
- genres:
- people:
- title_genres:
- title_credits:
- normalized graph SHA:
- orphan title_genres:
- orphan title_credits:
- invalid genre provenance:
- invalid credit provenance:

### Quality

- Catalogue Quality run:
- S0:
- S1:
- quality artifact:
- artifact digest:

### Final verifier

- run:
- artifact:
- artifact ID:
- artifact SHA-256:
- success marker:

### Operational handoff

- controller retirement evidence:
- frozen-mutator review evidence:
- approved workflows resumed:
- workflows intentionally kept disabled:
- post-P1 migration ownership confirmed:

---

## P1 COMPLETE declaration rule

Only after every blocking gate above passes may the authoritative P1 status be changed to COMPLETE.

The completion update must state, at minimum:

- corrected 16,380-title projection remains exact
- all 15 V3 operations complete
- production graph SHA equals reviewed V3 graph SHA
- source identity corrections remain exact
- referential integrity clean
- provenance clean
- Catalogue Quality V1 **S0 = 0 / S1 = 0**
- final verification artifact preserved
- P1 controller safely retired
- post-P1 mutation/migration handoff recorded

Until then, wording remains **PRODUCTION POPULATION IN PROGRESS**.

---

## Current checkpoint

As of **2026-09-27 UTC**:

- source cleanup ✅
- topup ✅
- physical shards 1–6 ✅
- physical shard 7 is next
- completed recommendation operations: **7 / 15**
- remaining recommendation operations: **8**
- next reviewed write estimate: **41,117 rows**
- production totals: **8,182 titles / 452 genres / 23,728 people / 8,064 title-genres / 35,962 title-credits**
- current integrity/provenance counters: **0 / 0 / 0 / 0**
- Sep27 guard: **`36297206014:6`**
- snapshot run: **`36300254259`**
- snapshot artifact ID: **`10925114272`**
- P1 exit-ready: **false**

The Sep27 UTC mutation slot is consumed by shard 6. Do not execute shard 7 until a fresh UTC quota day.