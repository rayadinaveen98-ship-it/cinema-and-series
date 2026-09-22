# Recommendation Metadata Foundation P1 — Final Exit Evidence Checklist

**Status:** PREPARED / USE ONLY AFTER ALL V3 PRODUCTION OPERATIONS COMPLETE  
**Prepared:** 2026-09-22  
**Active phase:** P1 — Recommendation Metadata Foundation  
**Authoritative status:** `docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md`

## Purpose

Make P1 closure deterministic and auditable.

This document does not mark P1 complete. It defines the evidence that must exist before the status may change to COMPLETE and before P2 production implementation begins.

No item may be waived because headline counts happen to look correct. P1 closes only when identity, graph, provenance, quality, quota lineage and operational handoff all pass together.

---

## Frozen reviewed target

The final production recommendation graph must equal the immutable reviewed V3 materialization exactly.

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

Counts alone are not sufficient. The production normalized graph must reproduce the exact reviewed graph SHA.

---

## Locked production operation sequence

Final evidence must account for every operation in this exact order:

`topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`

Expected conservative write costs:

| Operation | Reviewed max-cost estimate |
|---|---:|
| topup | 15,531 |
| 1 | 39,575 |
| 2 | 41,741 |
| 3 | 49,159 |
| 4 | 39,785 |
| 5 | 46,591 |
| 6 | 39,371 |
| 7 | 41,117 |
| 9 | 40,831 |
| 10 | 36,946 |
| 11 | 40,223 |
| 12 | 39,166 |
| 13 | 47,836 |
| 14 | 41,466 |
| 15 | 42,118 |

Physical partitions 0 and 8 are inherited from the reviewed parent shard-0 materialization and must not be rewritten as full V3 physical-shard operations.

The final evidence table must record for every operation:

- UTC quota date
- controller run ID
- exact guard token `<controller-run-id>:<operation>`
- writer run ID
- writer conclusion
- reviewed estimated write cost
- actual reported D1 rows written
- selected executable SHA when applicable
- writer artifact name
- artifact ID
- artifact ZIP SHA-256
- exact pre-state
- exact post-state
- post-write global integrity counters

Any operation with `partial`, `overfilled`, unknown guard ownership, wrong executable fingerprint or failed post-state blocks P1 exit.

---

## Already-completed evidence prefix

This section is historical evidence only and must remain consistent with the authoritative P1 status document.

### Reviewed source cleanup — 2026-09-20 UTC

- controller: **`35490594774`**
- cleanup writer: **`35490618771`**
- cleanup operation owned the day
- deleted exactly:
  - `movies / wd-Q3049630`
  - `series_titles / series-wd-Q3049630`
  - `catalogue_titles / wd-Q3146368`
- retained canonical:
  - `series_titles / series-wd-Q3146368`
- recaptured projection: **16,380 = 6,562 Movie + 9,818 Series**
- cross-type collisions: **0**

The final exit run must confirm this canonical source state is still exact.

### V3 top-up — 2026-09-21 UTC

- controller: **`35563283332`**
- guard: **`35563283332:topup`**
- writer: **`35563331648`**
- reviewed estimate: **15,531**
- actual D1 rows written: **14,985**
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
- artifact ID: **`10677492933`**
- artifact SHA-256: **`9968b81b7c12347be42797ca9a35eae5eb391869fc2b565bbe79394cb3f2d4d3`**
- post-state: **complete**

Read-only status snapshot run **`35692983180`** independently confirmed a contiguous complete prefix of `topup,1`, with operation `2` next and P1 exit not ready.

---

## Gate A — all operations complete

Required final state:

- `topup` = `complete`
- `1` = `complete`
- `2` = `complete`
- `3` = `complete`
- `4` = `complete`
- `5` = `complete`
- `6` = `complete`
- `7` = `complete`
- `9` = `complete`
- `10` = `complete`
- `11` = `complete`
- `12` = `complete`
- `13` = `complete`
- `14` = `complete`
- `15` = `complete`

Required observability result:

- completed operations = **15 / 15**
- operation state = complete
- next operation = none
- no complete operation after an incomplete gap
- no partial state
- no overfilled state

A count of 15 successful workflow runs is not enough; operation-state classification must prove exact completion.

---

## Gate B — quota-guard audit

The daily guard history must be consistent with one P1 production mutation per UTC date.

Verify:

1. each mutation date has at most one guard row
2. each guard uses the corrected projection SHA
3. each recommendation write guard is bound to the exact controller/operation token
4. Sep20 cleanup guard remains preserved
5. Sep21 top-up guard remains preserved
6. Sep22 shard-1 guard remains preserved
7. no guard was reset/deleted/reused to force another same-day mutation
8. failed historical Sep19 reservation remains historical and is not rewritten
9. no full-shard 0 or 8 V3 operation exists
10. no unrecognized operation token exists

Guard history is audit evidence. Do not clean it up merely to make the table look smaller before P1 closes.

---

## Gate C — reviewed source-identity state

Final production source state must still reflect the reviewed corrections.

Required:

- `Q3049630` absent from Movie recommendation identity
- `Q3049630` absent from Series recommendation identity
- no noncanonical `movies / wd-Q3049630`
- no noncanonical `series_titles / series-wd-Q3049630`
- no noncanonical `catalogue_titles / wd-Q3146368`
- canonical `series_titles / series-wd-Q3146368` retained
- live recommendation projection still exactly 16,380 / 6,562 / 9,818
- cross-type collisions = 0

Any drift blocks final graph verification and P1 exit.

---

## Gate D — exact production graph verification

Run the existing graph verifier against production after all operations complete:

`scripts/verify_p1_v3_production.py`

Required proof:

- normalized production materialization reconstructed successfully
- graph SHA exactly equals:
  **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- exact reviewed projection SHA remains:
  **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- verifier emits its explicit success marker
- final verification workflow concludes `success`

Do not substitute matching row counts for graph-hash equality.

---

## Gate E — referential integrity

Required final counters:

- orphan `title_genres`: **0**
- orphan `title_credits`: **0**

Also verify:

- every `title_genres.title_id` resolves to a recommendation title
- every `title_genres.genre_id` resolves to a genre
- every `title_credits.title_id` resolves to a recommendation title
- every `title_credits.person_id` resolves to a person

Any orphan blocks P1 exit regardless of graph headline counts.

---

## Gate F — provenance validity

Required final counters:

- invalid genre provenance: **0**
- invalid credit provenance: **0**

The locked source relationship rules remain:

- genre from explicit Wikidata `P136`
- director from explicit Wikidata `P57`
- Series creator from explicit Wikidata `P170`
- cast from explicit Wikidata `P161`

No inferred/guessed relationship may be normalized into the final P1 canonical graph.

---

## Gate G — exact final counts

After exact graph verification, record production counts from the same final state:

- recommendation titles = **16,380**
- genres = **612**
- people = **37,964**
- title-genres = **16,489**
- title-credits = **70,551**

If counts differ, P1 is not complete.

If counts match but graph SHA differs, P1 is also not complete.

---

## Gate H — Catalogue Quality V1

Run the production Catalogue Quality V1 gate only against the final intended P1 state.

Required:

- **S0 = 0**
- **S1 = 0**

Record:

- workflow/run ID
- commit/head SHA
- execution timestamp
- artifact name/ID
- artifact SHA-256 if available
- S0 count
- S1 count
- any lower-severity observations that do not block exit

Do not reinterpret a remaining S0/S1 issue as non-blocking solely to close the phase.

---

## Gate I — final read-only status snapshot

After all writes and final graph/quality checks, run/read the P1 production status snapshot.

Required snapshot semantics:

- source cleanup = complete
- completed operations = 15 / 15
- operation state = complete
- next operation = none
- no unsafe operation state
- final graph verification = successful
- Catalogue Quality S0/S1 = clean where surfaced
- P1 exit-ready = true

Record snapshot artifact identity and digest.

The snapshot is corroboration, not a replacement for the exact graph verifier.

---

## Gate J — final verification artifact

The permanent controller is configured around final verification evidence named:

`recommendation-metadata-production-write-v3-verify_final-final`

Before controller retirement, verify:

- final verification workflow actually completed successfully
- artifact exists under the expected name
- artifact belongs to the correct final production verification run
- artifact is not an older stale success from a different graph/projection
- artifact references the corrected V3 graph/projection fingerprints

Record:

- verification run ID
- verification artifact ID
- artifact ZIP SHA-256
- verified production graph SHA
- verified projection SHA

---

## Gate K — controller retirement

The daily P1 resume controller must retire only after successful final verification evidence exists.

Verify:

- it did not retire early after the last write alone
- final verification was read-only
- successful final verification artifact was observed
- retirement action completed as designed
- no future scheduled recommendation mutation can continue accidentally after P1 completion

If retirement requires an explicit workflow-state change, preserve its run/evidence.

---

## Gate L — frozen background mutators handoff

During P1, catalogue-mutating workflows were intentionally frozen to protect projection stability and quota ownership.

Before resuming any of them after P1:

1. P1 must be fully COMPLETE under this checklist
2. identify exactly which workflows were frozen
3. verify their current definitions still match the intended post-P1 catalogue-growth strategy
4. do not blindly re-enable obsolete writers
5. preserve the old 14,115-title / 8-shard recommendation writer as obsolete/frozen
6. ensure resumed catalogue mutation cannot silently invalidate P2/P3 assumptions
7. record the coordinator/resume evidence

P1 completion does not automatically mean every historical mutator should be re-enabled.

---

## Gate M — migration ownership handoff

P1 currently owns migrations:

- `0021_recommendation_metadata_foundation.sql`
- `0022_recommendation_materialization_daily_guard.sql`

Before P2/P3 or another phase adds a new migration:

- verify `main` migration ordering
- confirm P1 exit is recorded
- rebase any dormant/research migration numbering against current `main`
- never merge a stale branch merely because it once used `0023`

The first post-P1 migration number is assigned from actual current `main`, not from an old planning document.

---

## Final evidence record template

Fill this section only when closure is genuinely ready.

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

- corrected 16,380-title projection is still exact
- all V3 operations complete
- exact production graph SHA equals reviewed V3 graph SHA
- source identity corrections remain exact
- referential integrity clean
- provenance clean
- Catalogue Quality V1 S0 = 0 / S1 = 0
- final verification artifact preserved
- P1 controller safely retired
- post-P1 mutation/migration handoff recorded

Until then, wording must remain **PRODUCTION POPULATION IN PROGRESS**.

---

## Current checkpoint at preparation time

As of **2026-09-22 UTC**:

- source cleanup ✅
- topup ✅
- physical shard 1 ✅
- physical shard 2 is next
- completed recommendation operations: **2 / 15**
- remaining recommendation operations: **13**
- next reviewed write estimate: **41,741 rows**
- P1 exit-ready: **false**

This checkpoint is informational. The authoritative live state remains `RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md` and the read-only P1 production status snapshot.
