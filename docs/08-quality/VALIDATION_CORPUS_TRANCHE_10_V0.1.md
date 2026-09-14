# Validation Corpus Tranche 10 v0.1

Status: ACCEPTED BY CI

This tranche adds `VC-0166..VC-0172`, search queries `SQ-0214..SQ-0250`, semantic bindings in `validation/semantic/bindings-005.jsonl`, and curated reference states in `validation/semantic/reference-state-003.jsonl`.

Latest accepted validation run: GitHub Actions `34842678713`.

## Purpose

Attack three measured deficits without padding the corpus:

1. India identity / multilingual / localization;
2. South-language native-script and collision-aware search;
3. executable semantic coverage for high-risk merge/split cases.

## Hard cases

### `VC-0166` — U Turn 2016 vs 2018

The 2016 Kannada `U Turn` and 2018 Telugu-Tamil `U Turn` are separate Works. The later Work is related to the earlier source Work; the shared title must not trigger an identity merge.

### `VC-0167` — U Turn 2018 multilingual identity

Telugu and Tamil are original-language realizations of one 2018 Work. Language multiplicity alone must not produce one Work per language.

### `VC-0168` — 47 Rojulu / 47 Natkal

The Telugu and Tamil title/language forms belong to one 1981 multilingual Work. Native titles and language realizations remain queryable without duplicating the Work.

### `VC-0169` — Kushi 2000 vs 2001

The Tamil 2000 and Telugu 2001 films remain distinct Works despite near-identical titles and the same director. Unqualified `Kushi` is a deliberate search/identity collision requiring disambiguation.

### `VC-0170` — Jaanu vs 96

`Jaanu` and `96` are separate Telugu/Tamil Works connected by source relationship. The relationship must not be represented as shared identity.

### `VC-0171` — Drishyam vs Papanasam

The 2013 Malayalam `Drishyam` and 2015 Tamil `Papanasam` are separate derivative Works. Cross-language lineage is not a dub/version relationship.

### `VC-0172` — Bangalore Days vs Bangalore Naatkal

Title-family similarity does not collapse the 2014 Malayalam and 2016 Tamil Works. Search should surface disambiguation rather than silently choosing identity equivalence.

## Search tranche

`SQ-0214..SQ-0250` adds 37 assertions across Kannada, Telugu, Tamil and Malayalam.

The tranche intentionally includes:

- native-script exact queries;
- Latin labels and sourced aliases;
- language/year-qualified queries;
- same-title collisions for `U Turn` and `Kushi`;
- multilingual one-Work retrieval for `47 Rojulu / 47 Natkal`;
- derivative/remake-family retrieval for `Jaanu / 96`, `Drishyam / Papanasam`, and `Bangalore Days / Bangalore Naatkal`.

Generated qualified strings remain search-only benchmark inputs and are never promoted to canonical display Names without source evidence.

## Semantic execution

All seven new hard cases have explicit semantic bindings. This avoids increasing semantic debt while expanding the corpus.

The seven cases are also represented in `reference-state-003.jsonl` and execute under `reference_graph_v0.1`.

Latest semantic state after this tranche:

- total hard-case assertions: **385**;
- runtime-ready: **101/385**;
- still needing bindings: **280/385**;
- manual/specialized: **4/385**;
- binding-overlay cases: **35**;
- explicit overlay bindings: **78**;
- reference cases: **24**;
- reference assertions executed: **58**;
- reference PASS: **58**;
- reference failures: **0**.

Reference PASS remains an oracle-consistency result, not a production-engine result.

## Accepted corpus/search state

After this tranche:

- hard cases: **172/1000**;
- machine-readable current cases: **172/172**;
- hard-case assertions: **385**;
- gold candidates: **124**;
- evidence-upgrade needed: **47**;
- open adjudication: **1**;
- pre-freeze search assertions: **250/500**.

Primary cohort movement:

- India identity / multilingual / localization: **16 -> 23 / 180**.

Search-floor movement from the previous accepted state:

- Telugu: **11 -> 18 / 60**;
- Tamil: **11 -> 21 / 60**;
- Malayalam: **8 -> 12 / 50**;
- Kannada: **7 -> 9 / 50**;
- Devanagari combined remains **29/80**;
- total search assertions: **213 -> 250 / 500**.

## Evidence quality note

The new hard cases are strong modeling tests, but much of this tranche uses Wikidata/open-dataset evidence at grade B. This is sufficient for the current evidence-backed validation layer, but critical cases should continue to receive first-party, archive, legal-record, certification, distributor, or independently corroborated evidence upgrades where available before final gold freeze.

Do not downgrade or remove a hard case merely because stronger evidence is still being sought.

## Model lessons locked by this tranche

1. Same title is never sufficient merge evidence.
2. Same director is never sufficient merge evidence.
3. Multiple original languages can belong to one Work.
4. Cross-language remake/derivative lineage normally creates separate Works, not language Versions of one Work.
5. Native-title search must resolve to canonical identity without turning localized strings into duplicate Works.
6. Ambiguous unqualified queries should expose disambiguation rather than encourage identity collapse.
7. New critical cases should be semantically bound at creation time whenever feasible.

## Next measured gap

The next corpus expansion should prioritize **India release / territory / certification / version history**, currently only **15/120**, followed closely by **historical/archive/preservation**, currently **12/100**.

Prefer authoritative sources such as certification records, NFDC/NFAI and preservation institutions, festival archives, distributors, studios and streaming first-party announcements. Release dates must remain event-scoped, and certification, festival premiere, theatrical release, re-release/restoration and streaming events must never overwrite one another.
