# Validation Corpus Tranche 13 v0.1

Status: ACCEPTED BY CI

This tranche adds:

- hard cases `VC-0193..VC-0198` in `validation/corpus-tranche-015.jsonl`;
- primary-cohort assignments in `validation/corpus-primary-cohorts-004.csv`;
- semantic bindings in `validation/semantic/bindings-008.jsonl`;
- curated reference states in `validation/semantic/reference-state-006.jsonl`.

Accepted GitHub Actions run: `34845493337`.
Accepted head SHA: `a8f823527c60d12f6df922ce64e17599f3a21c38`.

## Purpose

Broaden the ReleaseEvent model beyond certification and restoration history into real distribution chronology. The tranche tests theatrical, dubbed theatrical, festival, streaming-platform and language-staggered platform availability as separate but linkable facts.

The central rule is that later digital availability never becomes permission to erase or replace earlier festival or theatrical history.

## Hard cases

### `VC-0193` — They Call Him OG theatrical vs Netflix

The 25 September 2025 theatrical release and 23 October 2025 Netflix release remain separate ReleaseEvents on one Work lineage.

### `VC-0194` — They Call Him OG multilingual Netflix availability

Netflix exposes Telugu original audio plus Hindi, Tamil, Kannada and Malayalam on one title. Localized audio availability does not create five Works and does not rewrite the original-language identity.

### `VC-0195` — Kantara Chapter 1 theatrical vs Prime Video

The 2 October 2025 theatrical event and 31 October 2025 Prime Video event are distinct distribution events.

### `VC-0196` — Kantara Chapter 1 staggered Prime Video language availability

Kannada/Tamil/Telugu/Malayalam availability begins in the initial 31 October 2025 streaming wave while Hindi becomes available later on 27 November 2025. Platform availability therefore needs language scope and effective dates.

### `VC-0197` — Manjummel Boys Malayalam theatrical, Telugu theatrical and Hotstar

The original Malayalam theatrical release, later Telugu theatrical release and subsequent Hotstar availability remain separate chronology entries. The first-party Hotstar evidence is deliberately modeled as **availability observed by 4 May 2024** rather than overclaiming an independently unverified exact streaming-start timestamp.

### `VC-0198` — Laapataa Ladies / Lost Ladies festival, theatrical and Netflix

TIFF 2023 premiere history, 1 March 2024 India theatrical release and 26 April 2024 Netflix availability are distinct events under one Work lineage.

## Model rules locked by this tranche

1. Theatrical, festival and platform availability are separate event classes/facts.
2. A platform date never overwrites the original theatrical or festival chronology.
3. A dubbed theatrical release may have its own language/territory date without becoming a separate Work.
4. One streaming title with multiple audio tracks remains one Work lineage unless independent creative-identity evidence says otherwise.
5. Platform availability can be language-scoped; different language versions can become available on different dates.
6. Platform availability must be territory-scoped where the source scope is territorial; India evidence must not silently become worldwide availability.
7. A first-party statement saying a title is "now streaming" proves availability by the observation date; it does not automatically prove the exact start instant when that is not separately stated.
8. `effective_from` and `observed_at` semantics must remain distinguishable in ingestion and canonicalization.
9. Streaming-platform changes do not alter original-language identity.
10. Release history is append-and-adjudicate, never destructive overwrite.

## Evidence profile

Evidence uses a mix of:

- first-party Netflix, Mythri Movie Makers, DisneyPlus Hotstar and official film-site material;
- corroborating trade/publication sources for theatrical and platform dates where first-party source material is unavailable or incomplete.

Every new case is a critical-risk gold candidate and was semantically bound at creation.

## Accepted state after tranche

### Corpus

- hard cases: **198/1000**;
- machine-readable current cases: **198/198**;
- hard-case assertions: **463**;
- gold candidates: **150**;
- evidence-upgrade needed: **47**;
- open adjudication: **1**;
- critical risk: **101**;
- high risk: **91**;
- medium risk: **6**.

### Primary quotas

- India identity / multilingual / localization: **23/180**;
- Global Work / Version / relationship: **26/100**;
- Release / territory / certification / availability: **37/120**;
- Series / season / episode / special: **29/140**;
- People / credits / roles / music: **22/100**;
- Organizations / companies / platforms / rightsholders: **12/60**;
- Historical / archive / preservation: **16/100**;
- Upcoming / unreleased / lifecycle: **17/70**;
- Source conflict / canonicalization / provenance: **10/60**;
- Search / transliteration / disambiguation: **6/70**.

### Search

The accepted search baseline from `queries-010.jsonl` remains:

- total: **295/500**;
- Telugu: **25/60**;
- Tamil: **25/60**;
- Malayalam: **19/50**;
- Kannada: **15/50**;
- Bengali: **12/40**;
- Gujarati: **5/20**;
- Punjabi: **8/20**;
- Devanagari combined: **36/80**.

### Semantic execution

- runtime-ready assertions: **179/463**;
- assertions needing bindings: **280/463**;
- manual/specialized: **4/463**;
- binding-overlay cases: **61**;
- explicit overlay bindings: **156**;
- reference cases: **50**;
- reference assertions: **136**;
- reference PASS: **136**;
- reference failures: **0**.

Reference PASS is reference-oracle consistency only, not production-engine correctness.

## Validation result

GitHub Actions run `34845493337` passed:

- hard-case manifest schema validation;
- primary-cohort quota audit;
- multilingual search validation;
- search-floor audit;
- semantic preflight;
- executable reference semantics.

## Next measured gaps

1. India identity/multilingual/localization is still only **23/180**.
2. Search/transliteration/disambiguation hard-case cohort is only **6/70**, even though query assertions are **295/500**.
3. Source conflict/canonicalization/provenance is only **10/60**.
4. Organizations/rightsholders is only **12/60**.
5. Historical/archive/preservation is only **16/100** and remains restoration-heavy.
6. **280 legacy assertions** still need explicit semantic bindings.

The next expansion should prioritize identity/search ambiguity and source-conflict cases rather than continuing to add minor variations of already-covered platform timelines.
