# Semantic Binding Migration 03 v0.1

## Accepted CI
GitHub Actions run `34848773154` is GREEN.

## Scope
`validation/semantic/bindings-012.jsonl` adds runtime bindings for:
- VC-0036 Money Heist Part 5 provider installment/volume semantics
- VC-0037 Manifest NBC -> Netflix continuation
- VC-0038 Lucifer Fox -> Netflix continuation
- VC-0039 Cobra Kai YouTube -> Netflix continuation
- VC-0040 The Expanse Syfy -> Prime continuation

Total migrated: **5 cases / 11 assertions**.

Only VC-0037 received a new reference fixture (`reference-state-010.jsonl`). VC-0038..0040 remain `evidence_upgrade_needed`. VC-0036 is gold but its current generic `preserves_claims` evaluator does not express the provider-label semantic precisely enough to justify manufacturing a reference PASS, so it is executable but intentionally not reference-promoted.

## Metrics
Before:
- runtime-ready: 239
- needs binding: 238
- reference cases: 69
- reference assertions: 182 PASS

After:
- runtime-ready: **250**
- needs binding: **227**
- reference cases: **70**
- reference assertions: **185 PASS**

## Rule
A gold case is not automatically forced into the reference oracle when the generic operator would under-test or distort its intended semantics. Structural executability and oracle adequacy are separate gates.
