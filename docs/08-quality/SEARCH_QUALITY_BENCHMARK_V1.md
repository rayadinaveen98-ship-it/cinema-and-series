# Search Quality Benchmark — Cinema and Series V1

**Status: LOCKED TARGETS / EXECUTION PENDING**  
**Date: 2026-09-14**

## Purpose

Cinema and Series must search Indian and world cinema correctly across native scripts, Roman spellings, alternate titles, aliases and ordinary typos without replacing original names with lossy normalized text.

This document defines the V1 search normalization contract, benchmark corpus and pass thresholds.

# 1. Canonical text preservation

Never rewrite the stored canonical Name into a transliterated or ASCII form.

For every Name preserve:
- original Unicode text;
- language;
- script;
- name type;
- territory/context;
- provenance.

Search uses derived search tokens/documents only.

# 2. Unicode normalization

All stored search-normalized strings and query strings undergo Unicode NFC normalization before matching.

Compatibility/lossy normalization such as NFKC/NFKD may be used only in a separate derived loose-match field when tested, never as the canonical display value.

# 3. Derived search forms

A Name can contribute multiple derived forms:

1. exact NFC native-script form;
2. case-folded Latin form where applicable;
3. punctuation/spacing-normalized form;
4. rights-safe/source-backed aliases;
5. source-backed official transliterations/romanizations;
6. deterministic ICU-style script-to-Latin transliteration token(s) for recall;
7. optional ASCII-folded loose token for Latin matching;
8. trigram/fuzzy representation.

Generated transliteration is tagged `GENERATED_SEARCH_ONLY` and is never presented as an official title unless separately sourced.

# 4. Priority scripts/languages

V1 benchmark must include, at minimum:
- Telugu;
- Tamil;
- Malayalam;
- Kannada;
- Devanagari (Hindi/Marathi and other relevant languages);
- Bengali;
- Gujarati;
- Gurmukhi/Punjabi;
- Latin-script English/international names.

Additional scripts can be supported without changing the model.

# 5. Search ranking layers

Ranking priority is conceptually:

1. exact canonical/preferred title match in query locale/script;
2. exact original/native title;
3. exact sourced alias/localized title;
4. exact sourced transliteration;
5. exact generated normalized/transliterated token;
6. strong prefix match;
7. trigram/fuzzy title match;
8. person/organization/credit relationship relevance;
9. weaker metadata signals.

Popularity must never cause an unrelated blockbuster to outrank an exact obscure-title match.

# 6. PostgreSQL V1 implementation baseline

Initial implementation uses:
- normal B-tree/exact indexes where appropriate;
- PostgreSQL full-text/read projections where useful;
- `pg_trgm` similarity indexes for fuzzy matching;
- derived normalized/transliterated search-document columns/tables;
- optional `unaccent` only for contexts where it is linguistically appropriate, primarily Latin text.

`unaccent` is not a substitute for Indic transliteration.

# 7. Query benchmark classes

Every benchmark query has an expected target CAS entity and acceptable rank.

## Q1 — Native exact
Example pattern: Telugu-script movie title entered exactly.

## Q2 — Romanized common spelling
Example pattern: `Baahubali`, `Bahubali`, `Pushpa`.

## Q3 — Alternate transliteration
Examples include doubled consonants, long-vowel omissions and common English spellings.

## Q4 — Minor typo
One insertion/deletion/substitution/transposition in a sufficiently long title.

## Q5 — Same-title collision
Same title across years/languages/remakes; expected result set must include correct disambiguation signals.

## Q6 — Person search
Native/Latin/stage/credited-as names.

## Q7 — Credit query
Title/person combination or indexed principal role.

## Q8 — Original vs localized title
Search by international English title and original native title must resolve same Work where appropriate.

## Q9 — Dub/remake disambiguation
Roman title should not collapse distinct Works; result metadata must help user choose language/year/version.

## Q10 — Historical title
Sparse artwork/popularity must not suppress exact match.

# 8. Minimum query-set size before V1 freeze

At least **500 search assertions** across the ~1,000-case corpus, including:
- >= 60 Telugu queries;
- >= 60 Tamil queries;
- >= 50 Malayalam queries;
- >= 50 Kannada queries;
- >= 80 Devanagari/Hindi/Marathi queries;
- >= 40 Bengali queries;
- >= 20 Gujarati queries;
- >= 20 Punjabi/Gurmukhi queries;
- >= 120 mixed/global/Latin collision/fuzzy queries.

Queries may overlap language categories where justified but must not be trivially duplicated.

# 9. V1 quality thresholds

## Exact title/native/known alias
- target entity in rank #1: **>= 99%**;
- target entity in top 3: **100% for gold cases**.

## Sourced transliteration/romanization
- target in top 3: **>= 99%**;
- target in top 5: **100% for gold cases**.

## Generated transliteration/common Roman variant
- target in top 5: **>= 97%**;
- target in top 10: **>= 99%**.

## Minor typo/fuzzy title
For titles >= 5 characters after normalization:
- target in top 5: **>= 95%**;
- target in top 10: **>= 98%**.

## Same-title collisions
- no exact-match target may be omitted from the first result page;
- year/language/type disambiguation metadata must be present;
- ranking must not silently merge distinct Works.

## Search-induced identity corruption
**0**. Search matching can suggest candidates but cannot merge identities.

# 10. Latency targets

On the V1 production dataset and ordinary interactive query classes:
- p50 search response <= 150 ms server-side target;
- p95 <= 400 ms server-side target;
- autocomplete p95 <= 250 ms target;
- expensive multi-filter exploration may have a separate <= 750 ms p95 target.

Targets exclude client network/render time and are measured after reasonable warm-up.

# 11. Dedicated search-engine escalation threshold

Remain on PostgreSQL search while all are true:
- quality thresholds above are met;
- p95 ordinary search <= 400 ms under expected V1 concurrency;
- index size/maintenance is operationally reasonable;
- transliteration/ranking needs remain expressible cleanly;
- no critical search feature requires unsupported semantics.

Evaluate a dedicated search engine only if, after query/index tuning and read-projection design, one or more persistently occurs:
- p95 ordinary search > 500 ms at expected production load;
- benchmark recall/ranking target cannot be met cleanly;
- indexing/rebuild time becomes operationally unacceptable;
- catalogue scale/query complexity makes Postgres search materially constrain primary database operations.

A dedicated engine remains a rebuildable projection, never authoritative storage.

# 12. Evaluation discipline

Every failed gold query is classified:
- `FAIL_NORMALIZATION`;
- `FAIL_TRANSLITERATION`;
- `FAIL_ALIAS_DATA`;
- `FAIL_RANKING`;
- `FAIL_FUZZY`;
- `FAIL_IDENTITY`;
- `FAIL_PERFORMANCE`;
- `BLOCKED_MISSING_EVIDENCE`.

Do not delete hard queries to improve the score.

# 13. Search UX requirements

Results should show enough context to distinguish collisions:
- preferred title;
- native/original title where useful;
- year;
- Work type;
- original language;
- status for upcoming/unreleased titles;
- principal creator/cast signal when needed.

The user should never have to infer whether two identical names are a remake, dub, old film or new series solely from poster art.
