# Semantic Binding Migration 01 v0.1

## Purpose
Reduce legacy semantic-binding debt without changing corpus truth, weakening assertions, or promoting uncertain evidence into gold reference truth.

## Accepted CI
GitHub Actions run `34848214003` passed the full validation pipeline.

## Migration scope
`validation/semantic/bindings-010.jsonl` adds explicit runtime bindings for 10 previously unbound legacy cases:

- VC-0001 Raja Harishchandra historical identity
- VC-0002 Alam Ara lost-film identity
- VC-0005 Premam Malayalam vs Telugu remake
- VC-0006 Arjun Reddy vs Kabir Singh
- VC-0007 Varmaa / Adithya Varma lifecycle handling
- VC-0012 The Office UK vs US adaptation identity
- VC-0014 A Star Is Born lineage/search disambiguation
- VC-0017 Blade Runner Final Cut
- VC-0018 Apocalypse Now Final Cut
- VC-0020 fragmentary historical cinema completeness semantics

These overlays make the existing assertions executable. They do not change the evidence status of any case.

## Reference-state policy
Only cases that were already `gold_candidate` and whose expected behavior is deterministic from accepted evidence were added to `reference-state-008.jsonl`:

- VC-0001
- VC-0002
- VC-0020

The evidence-upgrade cases were intentionally **not** given reference-state fixtures. Binding an assertion is not the same as adjudicating its truth.

## Metrics
Before:
- runtime-ready: 197 / 481
- needs binding: 280
- manual/specialized: 4
- reference cases: 56
- reference assertions: 154 / 154 PASS

After:
- runtime-ready: **217 / 481**
- needs binding: **260**
- manual/specialized: **4**
- reference cases: **59**
- reference assertions: **160 / 160 PASS**

## Locked rules reinforced
1. Semantic migration must not change source evidence or case status.
2. `evidence_upgrade_needed` cases may become structurally executable but do not receive gold oracle fixtures until evidence is upgraded/adjudicated.
3. Reference PASS means curated reference-graph consistency only; it is not a production-engine pass.
4. Missing bindings remain explicit validation debt.
5. No assertion may be deleted or weakened to improve readiness counts.
