# Semantic Binding Migration 08 v0.1 — Zero Binding Debt

Status: **ACCEPTED**  
Accepted CI run: `34851691542`  
Accepted revision: `2ca3dbc756d3447659d6e1534e7988305bc92152`

## Purpose

Close the remaining legacy semantic-binding debt without deleting assertions, weakening expected behavior, promoting weak evidence, or forcing multi-object cases through a pairwise evaluator.

## Starting point

After Migration 07:

- hard-case assertions: **481**
- runtime-ready: **368**
- needs explicit binding: **109**
- manual/specialized: **4**
- reference cases: **111**
- reference assertions: **274 / 274 PASS**

## Migration work

### 1. Regional/adjudicated gold migration

A gold-only regional block added explicit bindings and independent reference fixtures for aliases, same-title collisions, adaptation boundaries, certification/release chronology, organization roles and official upcoming-release precision.

Resulting checkpoint:

- runtime-ready: **414**
- binding debt: **63**
- reference cases: **131**
- reference assertions: **320 / 320 PASS**

### 2. Remaining evidence-upgrade bindings

`validation/semantic/bindings-018.jsonl` supplied machine bindings for **21 evidence-upgrade cases / 44 assertions**.

This changed executability only. It did **not** change case evidence status and did not add gold/reference PASS fixtures.

Resulting checkpoint:

- runtime-ready: **458**
- binding debt: **19**
- debt concentrated in **8 gold cases**

### 3. Set-aware semantic contract v0.3

The final 19 assertions could not honestly be tested by selecting one representative object from a multi-object expectation. The semantic contract was therefore extended instead of approximated.

New optional additive binding fields:

- `subject_refs`
- `object_refs`

The singular `subject_ref` / `object_ref` anchors remain required where the operator contract requires them.

Set-aware behavior now includes:

- all-entity equality for scoped `same_identity`;
- all-entity distinctness for `different_identity`;
- complete subject/object relationship-set evaluation;
- per-subject field, guard, claim, search and review checks.

A partially satisfied set fails.

### 4. Final eight gold cases

`bindings-019.jsonl` and `reference-state-016.jsonl` close the remaining gold debt for:

- WarnerMedia + Discovery → Warner Bros. Discovery;
- Viacom18 + Star India → JioStar;
- JioCinema + Disney+ Hotstar → JioHotstar history;
- Kill Bill Vol. 1 / Vol. 2 / The Whole Bloody Affair;
- The Disappearance of Eleanor Rigby: Him / Her / Them;
- The Apu Trilogy restoration identities and provenance;
- Love, Death & Robots provider Volume semantics;
- the corpus-wide source-conflict preservation invariant.

## Accepted result

GitHub Actions run `34851691542` is green.

Semantic preflight:

- cases: **204**
- assertions: **481**
- binding overlays: **196**
- overlay bindings: **454**
- set-aware assertions: **10**
- runtime-ready: **477**
- manual/specialized: **4**
- needs binding: **0**
- semantic debt cases: **0**
- semantic debt assertions: **0**

Reference benchmark:

- reference cases: **139**
- reference assertions: **339**
- result: **339 / 339 PASS**
- adapter: `reference_graph_v0.2`

## Interpretation

`477 runtime-ready` means every non-custom hard-case assertion now has sufficient machine bindings for a future runtime adapter. It does **not** mean a production Identity/Release/Canonicalization/Search engine has passed those assertions.

The remaining four `custom` assertions are intentionally classified as `manual_or_specialized`; they require explicitly named specialized evaluators and are not binding debt.

Reference PASS remains curated-oracle consistency, not production-engine correctness.

## Next priority

Semantic binding migration is no longer a Research Foundation blocker.

The highest remaining pre-freeze validation gaps are now:

1. multilingual search growth from **331 → >=500**, including every language/script floor;
2. hard-case corpus breadth from **204 → ~1,000** under locked cohort quotas;
3. evidence upgrades/adjudication for non-gold cases;
4. eventual execution against real implementation adapters after the V1 freeze authorizes implementation.
