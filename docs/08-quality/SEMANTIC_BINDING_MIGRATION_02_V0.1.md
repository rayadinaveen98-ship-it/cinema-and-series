# Semantic Binding Migration 02 v0.1

## Purpose
Convert a second high-value legacy slice into executable semantic assertions while keeping evidence, case status and expected outcomes unchanged.

## Accepted CI
GitHub Actions run `34848425921` passed the full validation pipeline.

## Migration scope
`validation/semantic/bindings-011.jsonl` binds 10 already-gold cases / 22 assertions:

- VC-0021 Baahubali multilingual production and dub identity
- VC-0023 Pushpa 2 language-market manifestations
- VC-0025 Project K -> Kalki 2898 AD title identity/history/search
- VC-0026 Thalapathy 69 -> Jana Nayagan title identity/history
- VC-0029 Kalki release reschedule chronology
- VC-0031 Stranger Things Season 4 split-volume identity
- VC-0032 The Crown Season 6 split-part identity
- VC-0033 Cobra Kai Season 6 three-part identity
- VC-0034 Bridgerton Season 3 split-part identity
- VC-0035 Ozark Season 4 split-part identity

Because all 10 were already `gold_candidate` with deterministic accepted evidence, corresponding fixtures were added in `validation/semantic/reference-state-009.jsonl`.

## Metrics
Before this batch:
- runtime-ready: 217 / 481
- needs binding: 260
- manual/specialized: 4
- reference cases: 59
- reference assertions: 160 / 160 PASS

After this batch:
- runtime-ready: **239 / 481**
- needs binding: **238**
- manual/specialized: **4**
- reference cases: **69**
- reference assertions: **182 / 182 PASS**

## Combined migration effect in this continuation
Starting baseline before Migration 01:
- runtime-ready: 197
- needs binding: 280
- reference cases: 56
- reference assertions: 154 PASS

After Migration 01 + 02:
- runtime-ready: **239** (+42)
- needs binding: **238** (-42)
- reference cases: **69** (+13)
- reference assertions: **182 PASS** (+28)

## Rules reinforced
1. Multilingual simultaneous productions and later dubs share an underlying Work without implying remake relationships.
2. Working/project titles remain historical Names on one durable Work.
3. Superseded release schedules remain auditable claims rather than being deleted.
4. Streaming parts/volumes do not automatically create separate Seasons.
5. Reference-state growth is restricted to adjudicated/gold cases with deterministic accepted evidence.
