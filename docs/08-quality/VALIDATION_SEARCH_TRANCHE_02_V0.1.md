# Validation Search Tranche 02 v0.1

Status: ACCEPTED BY CI

This tranche adds `SQ-0305..SQ-0331` in `validation/search/queries-012.jsonl`.

Accepted GitHub Actions run: `34846834869`.
Accepted head SHA: `4f0a93647cf017daf9152efcdabd306c6cdf608e`.

## Purpose

Raise the weakest Indian-language/script floors with sourced Wikimedia/Wikidata sitelinks rather than generated transliteration or typo padding.

The tranche also broadens search beyond titles by adding native-script person retrieval for major cinema people in Gujarati.

## Composition

27 new sourced queries:

- Gujarati: 6
- Punjabi/Gurmukhi: 4
- Bengali: 6
- Kannada: 6
- Malayalam: 5

Targets include:

- `Baahubali: The Beginning`;
- `Dangal`;
- `12th Fail`;
- `3 Idiots`;
- `Bajrangi Bhaijaan`;
- `PK`;
- Aamir Khan;
- A. R. Rahman;
- Amitabh Bachchan;
- Salman Khan;
- Shah Rukh Khan.

Every query is backed by a source sitelink. No generated transliteration, typo or spelling-variant entries were added in this tranche.

## Accepted search state

Total pre-freeze search assertions: **331/500**.

Language/script floors:

- Telugu: **25/60**;
- Tamil: **25/60**;
- Malayalam: **24/50**;
- Kannada: **21/50**;
- Bengali: **18/40**;
- Gujarati: **11/20**;
- Punjabi: **12/20**;
- Devanagari combined: **36/80**.

Change from the previous accepted state:

- overall **304 → 331**;
- Gujarati **5 → 11**;
- Punjabi **8 → 12**;
- Bengali **12 → 18**;
- Kannada **15 → 21**;
- Malayalam **19 → 24**.

## Validation

GitHub Actions run `34846834869` passed:

- hard-case manifest validation;
- primary-cohort audit;
- multilingual search manifest validation;
- search-floor audit;
- semantic preflight;
- reference semantics.

Because this is search-only expansion, corpus/semantic counts remain:

- hard cases: **204**;
- hard-case assertions: **481**;
- runtime-ready assertions: **197**;
- assertions needing semantic bindings: **280**;
- manual/specialized: **4**;
- reference cases: **56**;
- reference assertions: **154**;
- reference PASS: **154**.

## Guardrails

1. Sitelink text is valid search evidence but is not automatically promoted into canonical Name data.
2. Native-script person aliases are search projections onto canonical Person identity.
3. A search-floor query must exercise a real user retrieval path, not exist solely to increase counts.
4. The search benchmark may use source-backed localized labels even when they are not official theatrical marketing titles; provenance must preserve that distinction.
5. Generated query variants remain separately classified from sourced aliases.

## Next measured work

1. migrate legacy critical assertions into explicit semantic bindings;
2. continue search growth toward 500, especially Devanagari, Telugu, Tamil, Kannada, Malayalam and Bengali;
3. build more identity/source-conflict hard cases behind multilingual search behavior;
4. expand organizations/rightsholders and non-restoration archive cases.
