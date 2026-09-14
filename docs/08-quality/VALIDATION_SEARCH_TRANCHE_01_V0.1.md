# Validation Search Tranche 01 v0.1

Status: ACCEPTED BY CI

This tranche adds `SQ-0276..SQ-0295` in `validation/search/queries-010.jsonl`.

Accepted GitHub Actions run: `34845036793`.
Accepted head SHA: `5daaf53f48f05b09d595b8098a493e840b5208ef`.

## Purpose

Raise the weakest South-language search floors using sourced title statements and Wikimedia/Wikidata sitelinks already connected to high-value validation cases. The tranche intentionally avoids typo/transliteration padding.

## Covered Works

### Kantara: Chapter 1 — Wikidata Q122021056

Adds Kannada, Malayalam, Tamil and Telugu script retrieval using sourced Wikipedia sitelinks, plus qualified year/language queries.

### Manjummel Boys — Wikidata Q124636001

Adds the Malayalam native title statement plus Kannada, Tamil and Telugu sitelink forms, with qualified year/language queries.

### Laapataa Ladies — Wikidata Q124714626

Adds sourced Kannada and Telugu sitelink title forms plus qualified local-script queries.

## Query composition

- 20 total new assertions;
- sourced local-script aliases/title statements: 10;
- generated qualified queries grounded in sourced identity/year/language facts: 10;
- no typo variants;
- no generated transliteration variants;
- no unsourced alias claims.

## Accepted search state

- total pre-freeze search assertions: **295/500**;
- Telugu: **25/60**;
- Tamil: **25/60**;
- Malayalam: **19/50**;
- Kannada: **15/50**;
- Bengali: **12/40**;
- Gujarati: **5/20**;
- Punjabi: **8/20**;
- Devanagari combined: **36/80**.

Changes from the prior accepted baseline:

- Telugu **19 → 25**;
- Tamil **21 → 25**;
- Malayalam **15 → 19**;
- Kannada **9 → 15**;
- overall **275 → 295**.

## Corpus/semantic state

This is a search-only expansion. Hard-case and semantic-reference counts remain unchanged:

- hard cases: **192**;
- hard-case assertions: **445**;
- runtime-ready assertions: **161**;
- reference cases: **44**;
- reference assertions: **118**;
- reference PASS: **118**.

## Guardrails

1. A Wikipedia sitelink title is treated as a sourced search alias, not automatically promoted into the canonical Name table.
2. Generated qualified queries remain search-only truth.
3. Search floor progress must not be achieved by adding trivial spelling noise.
4. Localized retrieval must resolve to the underlying canonical Work while preserving original-language metadata.
5. Cross-language search evidence does not imply that every localized title is an official theatrical release title.

## Next work

1. continue South-language search growth using strong sourced forms;
2. broaden territory-specific theatrical and platform ReleaseEvents;
3. keep certification, theatrical, festival and OTT events semantically distinct;
4. bind new critical release cases at creation and promote only deterministic evidence into reference states.
