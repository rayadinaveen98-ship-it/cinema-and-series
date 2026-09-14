# Semantic Binding Migration 05 v0.1

## Accepted CI
GitHub Actions run `34849362339` is GREEN.

## Scope
`validation/semantic/bindings-014.jsonl` migrates **11 cases / 28 assertions** spanning preservation, unfinished/cancelled lifecycle and certification history.

Gold/reference-enabled cases:
- VC-0065 The Other Side of the Wind long production lifecycle
- VC-0066 Napoleon restoration/reconstruction
- VC-0068 Kummatty restoration
- VC-0069 Thamp restoration without surviving original camera negative
- VC-0070 Ishanou restoration/presentation history
- VC-0076 Udta Punjab certification/court history

Binding-only evidence-upgrade cases:
- VC-0071 Batgirl
- VC-0072 Scoob! Holiday Haunt
- VC-0073 Time Machine unfinished film
- VC-0074 Marudhanayagam halted/revival claims
- VC-0075 Paanch unreleased/certification history

VC-0067 Apu Trilogy was deliberately deferred: its existing `different_identity` assertion expects three Works, while the current evaluator is pairwise. It should not receive a partial oracle that pretends to verify all three.

## Metrics
Before:
- runtime-ready: 275
- needs binding: 202
- reference cases: 82
- reference assertions: 210 PASS

After:
- runtime-ready: **303 / 481**
- needs binding: **174**
- manual/specialized: **4**
- reference cases: **88**
- reference assertions: **227 / 227 PASS**

## Cumulative migration effect
From the initial semantic baseline:
- runtime-ready: **197 -> 303** (+106)
- binding debt: **280 -> 174** (-106)
- reference cases: **56 -> 88** (+32)
- reference assertions: **154 -> 227 PASS** (+73)

No corpus assertions or evidence statuses were weakened or removed.
