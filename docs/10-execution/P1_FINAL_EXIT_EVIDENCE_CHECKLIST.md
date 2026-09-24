# Recommendation Metadata Foundation P1 — Final Exit Evidence Checklist

**Status:** PREPARED / USE ONLY AFTER ALL V3 PRODUCTION OPERATIONS COMPLETE  
**Prepared:** 2026-09-22  
**Checkpoint updated:** 2026-09-24  
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
- reviewed artifact: `recommendation-metadata-materialization-v3-repartitioned`

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
| 4 | 39,785 | **next** |
| 5 | 46,591 | pending |
| 6 | 39,371 | pending |
| 7 | 41,117 | pending |
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
- writer artifact name, ID, and ZIP SHA-256
- exact pre-state and post-state
- post-write global integrity/provenance counters

Any `partial`, `overfilled`, unknown guard ownership, wrong executable fingerprint, or failed post-state blocks P1 exit.

---

## Completed evidence prefix

### Reviewed source cleanup — 2026-09-20 UTC

- controller: **`35490594774`**
- cleanup writer: **`35490618771`**
- deleted exactly:
  - `movies / wd-Q3049630`
  - `series_titles / series-wd-Q3049630`
  - `catalogue_titles / wd-Q3146368`
- retained canonical: `series_titles / series-wd-Q3146368`
- recaptured projection: **16,380 = 6,562 Movie + 9,818 Series**
- cross-type collisions: **0**
- artifact ID: **`10598937124`**
- artifact ZIP SHA-256: **`152dda1963c2f2967b9a904ccc5e497aa4cacefa830deba1b6643bc7d1cb65d6`**

### V3 top-up — 2026-09-21 UTC

- controller: **`35563283332`**
- guard: **`35563283332:topup`**
- writer: **`35563331648`**
- reviewed estimate: **15,531**
- actual D1 rows written: **14,985**
- exact slice: **250 titles / 317 title-genres / 1,695 title-credits**
- artifact ID: **`10622768410`**
- artifact SHA-256: **`f72d0d6b2df334045977a6f758e57303674e775379586dbf91c0f8870bb13952`**
- post-state: **complete**

### Physical shard 1 — 2026-09-22 UTC

- controller: **`35689533994`**
- guard: **`35689533994:1`**
- writer: **`35689574657`**
- reviewed estimate: **39,575**
- actual D1 rows written: **37,791**
- executable SHA-256: **`07245500dd8a64fffe5f8d607a187c2cf918f97611696daa5442324ef8fce977`**
- exact slice: **1,030 titles / 969 title-genres / 4,156 title-credits**
- artifact ID: **`10677492933`**
- artifact SHA-256: **`9968b81b7c12347be42797ca9a35eae5eb391869fc2b565bbe79394cb3f2d4d3`**
- post-state: **complete**

Read-only status snapshot run **`35692983180`** independently confirmed the contiguous prefix `topup,1`, operation `2` next, and P1 exit not ready.

### Physical shard 2 — 2026-09-23 UTC

- background-write coordinator: **`35819061430`** — success
- controller: **`35820142892`**
- controller run number: **10**
- controller event: **schedule**
- guard: **`35820142892:2`**
- writer: **`35820184949`**
- writer run number: **3**
- reviewed estimate: **41,741**
- actual D1 rows written: **39,259**
- executable SHA-256: **`8b167ee10e42ddba4903e0f7b4e424ec29d7ec24d375d2193446f5b85ecce36c`**
- writer artifact: `recommendation-metadata-production-write-v3-write_operation-2`
- artifact ID: **`10733260919`**
- artifact SHA-256: **`81e726460eaba92d6590173fa2fb2b6762e2995addabf37b54a199391fd62deb`**
- pre-state: **not_started**
- post-state: **complete**

Shard 2 exact slice:

- recommendation titles: **1,005 / 1,005**
- title-genres: **1,007 / 1,007**
- title-credits: **4,432 / 4,432**

Production totals after shard 2:

- recommendation titles: **4,029**
- genres: **342**
- people: **13,595**
- title-genres: **3,934**
- title-credits: **17,214**

Post-write integrity/provenance counters: **0 / 0 / 0 / 0**.

Controller artifact:

- artifact ID: **`10732554725`**
- artifact SHA-256: **`4f3942d74d018e3a009e52b3e7563498e227896eea55db1685fa3b6a45f70f9e`**

Sep23 read-only snapshot run **`35823982162`** independently confirmed `topup,1,2` complete, operation `3` exactly `not_started`, production totals unchanged from writer post-state, health violations **0**, and P1 exit-ready false.

- snapshot artifact ID: **`10735015860`**
- snapshot artifact SHA-256: **`a6f5a2410ad8e10591bfd16c6c3003b0aec8f7d09f719eed08fbc12b2870695d`**

### Physical shard 3 — 2026-09-24 UTC

- background-write coordinator: **`35956376942`** — success
- controller: **`35958174447`**
- controller run number: **11**
- controller event: **schedule**
- controller head SHA: **`fd278159e71fbe3501af84831c9fa6bdb234815a`**
- guard: **`35958174447:3`**
- reviewed estimate: **49,159**
- shard 3 pre-state: **not_started**
- controller artifact: `p1-quota-safe-daily-resume-v3-35958174447`
- controller artifact ID: **`10790902399`**
- controller artifact SHA-256: **`eb4f0b4ff5e604034ebf7a9137897be7b86a23ea098c6560734661549df24493`**

Writer evidence:

- writer: **`35958228439`**
- writer run number: **4**
- event: `workflow_dispatch`
- mode: `write_operation`
- operation: **`3`**
- guard: **`35958174447:3`**
- result: **success**
- actual D1 rows written: **45,683**
- executed D1 queries: **12,550**
- D1 rows read: **13,562**
- executable SHA-256: **`c0aa44243de94f3d37c89ef854da68ff415c4253781e7f739bf001e5e4589c39`**
- writer artifact: `recommendation-metadata-production-write-v3-write_operation-3`
- artifact ID: **`10791162083`**
- artifact SHA-256: **`80175efcdb856167d3d79970277a7ee17dff50a5abfbef5ea502e6706b3569f5`**
- post-state: **complete**

Shard 3 exact slice:

- recommendation titles: **1,056 / 1,056**
- title-genres: **1,041 / 1,041**
- title-credits: **5,384 / 5,384**

Production totals after shard 3:

- recommendation titles: **5,085**
- genres: **374**
- people: **16,894**
- title-genres: **4,975**
- title-credits: **22,598**

Post-write integrity/provenance counters:

- orphan title-genres: **0**
- orphan title-credits: **0**
- invalid genre provenance: **0**
- invalid credit provenance: **0**

The writer revalidated the live corrected projection **16,380 / 6,562 / 9,818**, cross-type collisions **0**, source cleanup, exact guard ownership, immutable artifact/projection/graph/executable fingerprints, and exact `not_started -> complete` transition.

A post-shard-3 Sep24 read-only status snapshot had **not been observed when this checkpoint was recorded**. Later snapshot evidence may be appended separately; it is corroboration, not a replacement for the writer evidence.

---

## Gate A — all operations complete

Required final operation states:

- `topup`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `9`, `10`, `11`, `12`, `13`, `14`, `15` = `complete`
- completed operations = **15 / 15**
- operation state = `complete`
- next operation = none
- no complete operation after an incomplete gap
- no partial state
- no overfilled state

Successful workflow count alone is insufficient; operation-state classification must prove exact completion.

---

## Gate B — quota-guard audit

Verify:

1. each mutation date has at most one guard row
2. every guard uses the corrected projection SHA
3. every recommendation write guard binds exact controller + operation
4. Sep20 cleanup guard remains preserved
5. Sep21 top-up guard remains preserved
6. Sep22 shard-1 guard remains preserved
7. Sep23 shard-2 guard **`35820142892:2`** remains preserved
8. Sep24 shard-3 guard **`35958174447:3`** remains preserved
9. no guard was reset, deleted, or reused to force another same-day mutation
10. failed historical Sep19 reservation remains historical and unchanged
11. no full-shard 0 or 8 V3 operation exists
12. no unrecognized operation token exists

Guard history is audit evidence and must not be cleaned up before P1 closes.

---

## Gate C — reviewed source identity

Required final source state:

- `Q3049630` absent from Movie and Series recommendation identity
- no `movies / wd-Q3049630`
- no `series_titles / series-wd-Q3049630`
- no `catalogue_titles / wd-Q3146368`
- canonical `series_titles / series-wd-Q3146368` retained
- live recommendation projection exactly **16,380 / 6,562 / 9,818**
- cross-type collisions = **0**

Any drift blocks P1 exit.

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

Every title/genre/person foreign reference must resolve.

---

## Gate F — provenance validity

Required final counters:

- invalid genre provenance = **0**
- invalid credit provenance = **0**

Locked canonical relationships remain:

- genre from Wikidata `P136`
- director from Wikidata `P57`
- Series creator from Wikidata `P170`
- cast from Wikidata `P161`

No inferred relationship may enter the canonical P1 graph.

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

Run against the final intended P1 state.

Required:

- **S0 = 0**
- **S1 = 0**

Preserve workflow/run ID, head SHA, execution timestamp, artifact identity/digest, and any non-blocking lower-severity observations.

---

## Gate I — final read-only status snapshot

After all writes and final graph/quality checks, required snapshot semantics are:

- source cleanup = complete
- completed operations = **15 / 15**
- operation state = complete
- next operation = none
- no unsafe state
- final graph verification = successful
- Catalogue Quality S0/S1 clean where surfaced
- P1 exit-ready = true

Snapshot is corroboration, not a replacement for the exact graph verifier.

---

## Gate J — final verification artifact

Expected artifact name:

`recommendation-metadata-production-write-v3-verify_final-final`

Before controller retirement verify that it:

- belongs to the correct final verification run
- is successful and read-only
- references the corrected graph/projection fingerprints
- is not a stale older artifact

Record run ID, artifact ID, ZIP SHA-256, verified graph SHA, and projection SHA.

---

## Gate K — controller retirement

The daily P1 controller retires only after successful final verification evidence exists.

Verify:

- it did not retire after the last write alone
- final verification was read-only
- final verification artifact was observed
- retirement completed as designed
- no future scheduled recommendation mutation can continue accidentally

---

## Gate L — frozen background mutator handoff

Before resuming any frozen mutating workflow:

1. P1 must be COMPLETE under this checklist
2. review each frozen workflow definition against the post-P1 strategy
3. do not blindly re-enable obsolete writers
4. keep the obsolete 14,115-title / 8-shard recommendation path retired
5. ensure resumed catalogue mutation cannot silently invalidate P2/P3 assumptions
6. record exactly what was resumed and what remains disabled

P1 completion does not imply every historical mutator should be re-enabled.

---

## Gate M — migration ownership handoff

P1 owns:

- `0021_recommendation_metadata_foundation.sql`
- `0022_recommendation_materialization_daily_guard.sql`

Before a later phase adds a migration:

- verify actual `main` migration ordering
- confirm P1 exit is recorded
- rebase dormant/research migration numbering
- never merge an old branch solely because it once used `0023`

The first post-P1 migration number is assigned from actual current `main`.

---

## Next-operation rehearsal — physical shard 4

Read-only/offline immutable-artifact preflight:

- titles: **1,003**
- title-genres: **975**
- title-credits: **4,202**
- genre upserts: **184**
- people upserts: **3,826**
- data statements: **10,190**
- reviewed estimate: **39,785 rows**
- executable SHA-256: **`41596755c34154128f3a147817e54e6d6e1fba2df3a6eb1e80edbe003c67467e`**
- materialization SHA-256: **`60bdea1bed4530c2c646e38210c7a6e62fb0bf9654f91fd82796eac9c365d6e7`**

This rehearsal cannot authorize a write. The live controller/writer gates remain mandatory on the next fresh UTC day.

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

### Final status snapshot

- run:
- artifact:
- completed operations:
- next operation:
- exit-ready:

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

As of **2026-09-24 UTC**:

- source cleanup ✅
- topup ✅
- physical shard 1 ✅
- physical shard 2 ✅
- physical shard 3 ✅
- physical shard 4 is next
- completed recommendation operations: **4 / 15**
- remaining recommendation operations: **11**
- next reviewed write estimate: **39,785 rows**
- production totals: **5,085 titles / 374 genres / 16,894 people / 4,975 title-genres / 22,598 title-credits**
- current integrity/provenance counters: **0 / 0 / 0 / 0**
- Sep24 guard: **`35958174447:3`**
- P1 exit-ready: **false**

This checkpoint is informational. The authoritative live state remains `RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md` plus the read-only P1 production status workflow when a post-write snapshot exists.
