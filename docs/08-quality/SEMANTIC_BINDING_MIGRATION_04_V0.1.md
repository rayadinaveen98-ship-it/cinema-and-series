# Semantic Binding Migration 04 v0.1

## Accepted CI
GitHub Actions run `34849087455` is GREEN.

## Scope
`validation/semantic/bindings-013.jsonl` and `reference-state-011.jsonl` migrate **12 gold cases / 25 assertions**:

- VC-0041 Clone Wars multiple episode-order schemes
- VC-0042 Navarasa anthology/component scope
- VC-0043 Lust Stories anthology/component scope
- VC-0044 Ajeeb Daastaans anthology/component scope
- VC-0047 Fruits Basket 2001 vs 2019 adaptation identity
- VC-0049 Evangelion TV vs Rebuild Work/franchise distinction
- VC-0050 One Piece anime vs Netflix live-action adaptation identity
- VC-0051 Once Upon a Deadpool as a Version of Deadpool 2
- VC-0052 Brazil director/studio cuts
- VC-0055 MGM acquisition without historical-credit rewrite
- VC-0058 James Bond temporal rights-control history
- VC-0060 multilingual alias search without duplicate Work creation

## Explicit deferral
VC-0054, VC-0056 and VC-0057 were not included even though they are gold. Their current single-object generic relationship assertion cannot fully verify multi-predecessor/platform-integration semantics. They remain debt until the binding/evaluator contract can test them without under-specifying the expected behavior.

## Metrics
Before:
- runtime-ready: 250
- needs binding: 227
- reference cases: 70
- reference assertions: 185 PASS

After:
- runtime-ready: **275 / 481**
- needs binding: **202**
- reference cases: **82**
- reference assertions: **210 / 210 PASS**
- manual/specialized: **4**

## Cumulative effect from start of semantic migration work
- runtime-ready: **197 -> 275** (+78)
- binding debt: **280 -> 202** (-78)
- reference cases: **56 -> 82** (+26)
- reference assertions: **154 -> 210 PASS** (+56)

No corpus assertions, evidence labels or case statuses were changed to achieve these counts.
