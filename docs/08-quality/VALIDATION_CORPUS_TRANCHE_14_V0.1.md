# Validation Corpus Tranche 14 v0.1

Status: ACCEPTED BY CI

This tranche adds:

- hard cases `VC-0199..VC-0204` in `validation/corpus-tranche-016.jsonl`;
- primary-cohort assignments in `validation/corpus-primary-cohorts-005.csv`;
- semantic bindings in `validation/semantic/bindings-009.jsonl`;
- curated reference states in `validation/semantic/reference-state-007.jsonl`;
- search assertions `SQ-0296..SQ-0304` in `validation/search/queries-011.jsonl`.

Accepted GitHub Actions run: `34846171238`.
Accepted head SHA: `ae9527f1c82bfa36caba5debc98c29706cbc3cdf`.

## Purpose

Attack three related failure modes that can silently corrupt a cinema database:

1. one Work legitimately carrying different official title forms across markets/source contexts;
2. one fact such as a maturity rating legitimately differing by territory instead of having one global scalar value;
3. short or ambiguous search strings matching multiple legitimate Works and therefore requiring disambiguation rather than forced rank-1 certainty.

## Hard cases

### `VC-0199` — Laapataa Ladies / Lost Ladies

Netflix uses **Laapataa Ladies** while the official international-facing film site uses **Lost Ladies** for the same Kiran Rao film with matching cast, story and release context.

Expected model: one durable Work, multiple title forms with source/market provenance.

### `VC-0200` — Kantara Chapter 1 official title variants

The same Hombale first-party trailer uses `Kantara Chapter 1` in the video title and `Kantara: A Legend - Chapter 1` in the official description.

Expected model: one Work, multiple first-party title forms; title provenance is preserved rather than choosing one and deleting the other.

### `VC-0201` — They Call Him OG maturity ratings by Netflix territory/context

Netflix surfaces different maturity labels for the same title in different contexts: India `A`, generic English `TV-MA`, Singapore `M18`, and Korea English `19+`.

Expected model: territory/context-scoped rating claims. A single global maturity-rating field is forbidden when evidence is jurisdiction-specific.

### `VC-0202` — bare `OG` search collision

`They Call Him OG` and `O.G.` are separate Works. Bare `OG` must expose ambiguity, while a qualified query such as `OG 2025 Pawan Kalyan` should resolve the Indian 2025 Work.

### `VC-0203` — bare `Kantara` search collision

The 2022 `Kantara` and 2025 `Kantara Chapter 1` are distinct Works in the same franchise/lineage. Search must not collapse them.

### `VC-0204` — Lost Ladies / Laapataa Ladies search convergence

Both official title forms must resolve one Work without creating a duplicate record.

## Search assertions

`SQ-0296..SQ-0304` add nine assertions covering:

- first-party title aliases;
- official short/full title forms;
- qualified collision resolution;
- bare collision disambiguation for `Kantara` and `OG`.

The initial CI attempt correctly rejected `SQ-0301` because bare `Kantara` was marked `same_title_collision` while also requiring the 2022 Work at rank 1. That contradicts the benchmark rule that genuinely ambiguous queries must not force one candidate to monopolize rank 1.

Failed run: `34846071409`.

The schema/validator was not weakened. `SQ-0301` was corrected to require the target within rank 10 while requiring visible disambiguation. Repair commit: `ae9527f1c82bfa36caba5debc98c29706cbc3cdf`.

The repaired full pipeline passed in run `34846171238`.

## Model/search rules locked by this tranche

1. Canonical identity is not the same thing as display-title choice.
2. Multiple first-party title forms can coexist on one Work with provenance and market/context scope.
3. A market title or international title must not create a duplicate Work by default.
4. Territory-specific maturity labels must remain scoped claims, not flattened into one global rating.
5. Search aliases are projections onto canonical entities; they are not independent entities.
6. Bare ambiguous queries may return multiple legitimate top candidates.
7. A `same_title_collision` benchmark must never require one arbitrary candidate at rank 1.
8. Qualified queries may restore rank-1 expectations when year/person/language/context disambiguates the target.
9. Similar franchise titles do not justify identity merging.
10. Search ambiguity and canonical identity decisions must remain auditable separately.

## Accepted state after tranche

### Corpus

- hard cases: **204/1000**;
- machine-readable current cases: **204/204**;
- hard-case assertions: **481**;
- gold candidates: **156**;
- evidence-upgrade needed: **47**;
- open adjudication: **1**;
- critical risk: **107**;
- high risk: **91**;
- medium risk: **6**.

### Primary cohorts

- India identity / multilingual / localization: **24/180**;
- Global Work / Version / relationship: **26/100**;
- Release / territory / certification / availability: **37/120**;
- Series / season / episode / special: **29/140**;
- People / credits / roles / music: **22/100**;
- Organizations / companies / platforms / rightsholders: **12/60**;
- Historical / archive / preservation: **16/100**;
- Upcoming / unreleased / lifecycle: **17/70**;
- Source conflict / canonicalization / provenance: **12/60**;
- Search / transliteration / disambiguation: **9/70**.

### Search

- total pre-freeze search assertions: **304/500**;
- Telugu: **25/60**;
- Tamil: **25/60**;
- Malayalam: **19/50**;
- Kannada: **15/50**;
- Bengali: **12/40**;
- Gujarati: **5/20**;
- Punjabi: **8/20**;
- Devanagari combined: **36/80**.

### Semantic execution

- runtime-ready assertions: **197/481**;
- assertions needing bindings: **280/481**;
- manual/specialized: **4/481**;
- binding-overlay cases: **67**;
- explicit overlay bindings: **174**;
- reference cases: **56**;
- reference assertions: **154**;
- reference PASS: **154**;
- reference failures: **0**.

Reference PASS means consistency with the curated reference graph, not production-engine correctness.

## Next measured priorities

1. Continue native-script search-floor growth without trivial query padding.
2. Raise India identity/multilingual/localization beyond **24/180** using real multilingual/dub/remake/title-history cases.
3. Raise source-conflict/canonicalization beyond **12/60** with cross-source dates, runtimes, credits and title conflicts.
4. Raise organizations/rightsholders beyond **12/60**.
5. Broaden historical/archive cases beyond restoration-heavy examples.
6. Migrate the remaining **280** legacy assertions to explicit bindings, prioritizing critical identity/release/canonicalization semantics.
