# Validation Corpus Tranche 12 v0.1

Status: ACCEPTED BY CI

This tranche adds:

- hard cases `VC-0184..VC-0192` in `validation/corpus-tranche-014.jsonl`;
- primary-cohort assignments in `validation/corpus-primary-cohorts-003.csv`;
- semantic bindings in `validation/semantic/bindings-007.jsonl`;
- curated reference states in `validation/semantic/reference-state-005.jsonl`.

Accepted GitHub Actions run: `34844438776`.
Accepted head SHA: `8f59bfb5f3314180a5d5e8590990ac8eb298863b`.

## Purpose

Attack a major remaining weakness in the release model: Indian certification semantics.

The tranche tests a strict separation between:

1. a Work;
2. a language/version presentation;
3. a promo/song/trailer asset;
4. a CBFC certification record;
5. a theatrical or other ReleaseEvent.

A certificate is regulatory metadata attached to the certified presentation or asset. A certificate date is **not** a release date. A later certificate is **not** permission to erase earlier certification history.

## Hard cases

### `VC-0184` — They Call Him OG language-scoped feature certifications

The Telugu, Hindi and Kannada feature presentations have separate CBFC records. Identical rating/length values do not justify collapsing the language-scoped certification records.

### `VC-0185` — They Call Him OG A → UA16+ re-certification

The original Telugu `A` certification and later explicit `A TO UA` / `UA 16+` certification coexist in history. The certified length changes from 154.15 minutes to 143.52 minutes. The later record must not silently overwrite the earlier certificate or its certified length.

### `VC-0186` — They Call Him OG Firestorm song vs feature

The Firestorm song asset has its own certification and short certified duration. Its rating is asset-scoped and must never become the feature film's rating.

### `VC-0187` — Kantara Chapter 1 teaser, trailer and feature

Teaser, trailer and feature certifications are distinct asset/presentation records. A teaser or trailer certificate cannot overwrite the feature certificate even where branding/title lineage is shared.

### `VC-0188` — Kantara Chapter 1 language-specific feature certifications

Hindi, English and Marathi feature presentations retain their own certification dates and certified lengths. The English certified length differs materially and must remain scoped to that presentation.

### `VC-0189` — Kantara Chapter 1 certification date vs theatrical release date

The Hindi feature's CBFC certification date and its theatrical release date are different kinds of facts. Certification chronology cannot be promoted to theatrical release chronology.

### `VC-0190` — Laapataa Ladies later Bengali and Marathi certifications

The 2024 original theatrical release remains the Work's historical theatrical event. Later 2025 Bengali and 2026 Marathi certification records belong to later language presentations and do not rewrite that original release.

### `VC-0191` — Manjummel Boys Kannada certification after original release

The 2025 Kannada certification is a later language-presentation event. It does not change the original Malayalam Work's 2024 theatrical release history.

### `VC-0192` — Kantara Chapter 1 localized trailers with identical metadata

Kannada, Telugu, Tamil, Malayalam and Hindi trailer certifications share date, duration and rating but remain language-scoped trailer assets/certification records. Identical metadata is not identity-merge evidence.

## Evidence profile

The tranche is CBFC-first.

Primary certification evidence comes from the Central Board of Film Certification's indexed film-certificate records and is graded `A` with `source_kind: certification_authority`.

Where a theatrical date was necessary to prove certification-vs-release chronology, an independent publication was retained as corroborating release evidence rather than inferring release from the certificate.

## Model rules locked by this tranche

1. **Certification record ≠ ReleaseEvent.**
2. **Certification date ≠ theatrical release date.**
3. Certification category/rating is scoped to the exact certified presentation or asset.
4. Promo songs, teasers and trailers never determine a feature film's certification category.
5. Later re-certification preserves earlier certificate history; it does not silently overwrite it.
6. Certified length is version/presentation-scoped and historically preserved.
7. Same certificate date, rating or length is not sufficient identity-merge evidence.
8. Language-specific certificates remain distinct claims even when they share an underlying Work.
9. Later dubbed/localized certification dates do not rewrite the original Work's release chronology.
10. Regulatory history and distribution/release history remain independent but linkable timelines.

## Accepted state after tranche

### Corpus

- hard cases: **192/1000**;
- machine-readable current cases: **192/192**;
- hard-case assertions: **445**;
- gold candidates: **144**;
- evidence-upgrade needed: **47**;
- open adjudication: **1**;
- critical risk: **95**;
- high risk: **91**;
- medium risk: **6**.

### Primary quotas

- India identity / multilingual / localization: **23/180**;
- Global Work / Version / relationship: **26/100**;
- Release / territory / certification / availability: **31/120**;
- Series / season / episode / special: **29/140**;
- People / credits / roles / music: **22/100**;
- Organizations / companies / platforms / rightsholders: **12/60**;
- Historical / archive / preservation: **16/100**;
- Upcoming / unreleased / lifecycle: **17/70**;
- Source conflict / canonicalization / provenance: **10/60**;
- Search / transliteration / disambiguation: **6/70**.

### Search

No new search queries are part of the certification manifest itself. The accepted search baseline remains:

- pre-freeze assertions: **275/500**;
- Telugu: **19/60**;
- Tamil: **21/60**;
- Malayalam: **15/50**;
- Kannada: **9/50**;
- Bengali: **12/40**;
- Gujarati: **5/20**;
- Punjabi: **8/20**;
- Devanagari combined: **36/80**.

### Semantic execution

All nine new hard cases were bound at creation time and included in a curated reference state.

- runtime-ready assertions: **161/445**;
- assertions needing bindings: **280/445**;
- manual/specialized: **4/445**;
- binding-overlay cases: **55**;
- explicit overlay bindings: **138**;
- reference cases: **44**;
- reference assertions: **118**;
- reference PASS: **118**;
- reference failures: **0**.

Reference PASS remains reference-oracle consistency only, not a production-engine result.

## Validation result

GitHub Actions run `34844438776` completed successfully across:

- manifest schema validation;
- quota audit;
- multilingual search manifest validation;
- search-floor audit;
- semantic preflight;
- executable reference semantics.

## Next measured gaps

The release/certification cohort improved from **22/120 → 31/120**, but remains incomplete. Next work should avoid repeating only certification variations and instead broaden into:

1. territory-specific theatrical and platform release events;
2. certifications across more regional industries and older titles;
3. conflicts between certification metadata and external catalog metadata;
4. historical/archive cases beyond restorations;
5. India identity/multilingual cases;
6. Kannada/Malayalam/Telugu/Tamil/Bengali search depth;
7. organization/rightsholder and source-conflict coverage.

New critical cases should continue to receive semantic bindings and reference states at creation time whenever the evidence supports deterministic expectations.
