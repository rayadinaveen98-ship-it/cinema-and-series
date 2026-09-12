# Search Engine Specification — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Search is a derived retrieval system over canonical Cinema and Series data. It must make multilingual world cinema discoverable without becoming another source of truth.

## Core principle

**PostgreSQL/canonical entities remain authoritative. Search indexes are disposable and rebuildable.**

## V1 search goals

A user should reliably find a Work/Person/Series through:
- exact title/name;
- native-script title/name;
- official localized title;
- common transliteration/romanization;
- alternate title;
- credited-as name;
- reasonable spelling variation;
- year/language/type qualifiers;
- people/company relationships.

Search must be excellent for Indian scripts and Latin-script queries for Indian cinema.

## Searchable entity types

P0/P1:
- Works: films, series, episodes, specials;
- Persons;
- Organizations/companies;
- Franchises;
- Seasons where directly named;

P2/later:
- Characters;
- genres/themes;
- festivals/archives;
- soundtrack tracks;
- complex natural-language semantic queries.

## Search document

Build a denormalized SearchDocument projection containing only searchable/public canonical fields.

Conceptual fields:
- CAS entity ID/type;
- preferred display name/title by locales;
- original names;
- localized names;
- transliterations;
- alternate names;
- generated search aliases;
- year/date signals;
- work kind;
- languages/scripts;
- countries;
- principal people/companies;
- franchise/series context;
- popularity/quality signals only if later approved;
- identity confidence/visibility state;
- update version.

SearchDocument is rebuildable from canonical data.

## Normalization pipeline

For indexing/query matching, derive normalized forms without modifying canonical strings:

1. Unicode normalization;
2. locale-appropriate case folding;
3. whitespace normalization;
4. punctuation normalization variants;
5. diacritic-insensitive variant;
6. script detection;
7. approved transliteration variants;
8. numeric/roman-numeral variants where useful;
9. tokenization by script/language;
10. phonetic/fuzzy features where validated.

Do not blindly strip all punctuation because punctuation can be semantically meaningful in titles.

## India-specific query behavior

Examples of required outcome classes:
- Telugu script query -> matching Telugu Work first;
- Latin romanization -> same Work discoverable;
- common spelling variation -> correct Work in top results;
- dubbed Hindi title -> same Work/Version discoverable without hiding original identity;
- actor initials/stage name -> correct Person;
- same title from multiple years -> disambiguate using year, language, poster/metadata and ranking.

## Ranking signals

### High-priority lexical signals
1. exact canonical/localized title match;
2. exact original/native title match;
3. exact official alias match;
4. exact known romanization/transliteration;
5. prefix/title-token match;
6. fuzzy title match;
7. related principal Person/Organization match.

### Context signals
- requested locale/language;
- explicit year query;
- explicit media type;
- user's territory for display relevance, not truth;
- series/episode context.

### Quality signals
May include:
- entity canonical confidence;
- metadata completeness;
- verified release status;

Do not let popularity bury an exact match to an obscure historical film.

### Popularity signals
P2. If introduced, popularity is a tie-breaker/intent signal, not the dominant default for exact search.

## Query parsing

V1 should support simple recognized qualifiers:
- title terms;
- person/company names;
- four-digit year;
- language;
- media type.

Examples:
- `Drishyam 2013 Malayalam`
- `Sukumar Telugu films`
- `RRR 2022`

Full natural-language knowledge queries such as "Telugu thrillers after 2018 shot by X" can initially use structured filters/facets and later add a query-planning layer.

## Filters/facets

V1/P1 filters:
- media type;
- release year/range;
- original language;
- production country;
- genre;
- release status/upcoming/released;

P2:
- people/crew role;
- company;
- certification;
- runtime range;
- franchise;
- streaming availability;
- release territory.

## Transliteration search

Generated transliterations belong only to index/search aliases unless separately sourced as official Names.

Search can index multiple transliteration systems/variants where benchmark data proves value.

Avoid generating enormous combinatorial alias sets. Prefer a normalized query-time/index-time transliteration strategy behind a tested library/engine selected during technical validation.

## Fuzzy matching

V1 initial technology direction:
- PostgreSQL full-text/searchable projection;
- `pg_trgm` trigram similarity;
- normalized alias table/search vector;
- language/script-aware preprocessing.

Move to a dedicated search engine only when benchmarks demonstrate PostgreSQL cannot satisfy quality/latency/scale.

Candidate future engines can be evaluated later; no provider should be locked before requirements/benchmarks.

## Search vs Identity Resolution

They can share normalization/candidate-generation components but have different risk thresholds.

### Consumer search
Favor recall: showing several plausible results is okay.

### Identity auto-merge
Favor extreme precision: uncertain matches must go to review.

Never reuse consumer search similarity score directly as an auto-merge decision.

## Episode search

Search should support:
- episode title;
- Series title + episode title;
- season/episode numbering;
- alternate provider numbering as secondary lookup.

Result UI must clearly indicate Series/Season context.

## Person search

Index:
- canonical professional name;
- native names;
- stage/alternate names;
- credited-as forms;
- transliterations.

Ranking can use principal filmography relevance, but exact rare names should remain discoverable.

## Search visibility states

Not every candidate entity belongs in public search.

Possible states:
- PUBLIC_CANONICAL
- PUBLIC_UNVERIFIED_LABELLED — use sparingly/policy-defined
- ADMIN_REVIEW_ONLY
- MERGED_REDIRECT
- HIDDEN_INVALID

Weak future-project Leads remain admin-only until promotion threshold.

## Redirect behavior

When entities merge:
- old CAS ID remains redirect/tombstone;
- search removes duplicate public result;
- old names/external IDs can still resolve to survivor;
- redirect history remains audit-able.

## Freshness

Index updates should be event-driven from canonical projection changes.

Targets to define during implementation benchmarking:
- title/name corrections: near-real-time;
- new upcoming titles: near-real-time after canonical approval;
- release/status changes: minutes/hours;
- bulk historical imports: asynchronous batch.

No user should see stale search results for long after an identity merge or title correction.

## Result explainability

Search UI can show why result is identifiable without exposing rank math:
- title;
- original/native title when useful;
- year;
- media type;
- language/country;
- principal people;
- poster if rights-approved.

For same-title collisions, year/language/director are primary disambiguators.

## Search quality benchmark

Create a labeled query corpus with:
- exact titles;
- misspellings;
- transliterations;
- native scripts;
- old/alternate titles;
- same-name collisions;
- people with initials/stage names;
- series/episode queries;
- obscure historical titles;
- English/international localized titles.

Measure:
- Top-1 success;
- Top-3 success;
- Top-10 recall;
- zero-result rate;
- wrong-entity rate;
- latency p50/p95/p99 by corpus class.

Scores must be segmented by language/script. A high global score cannot hide poor Telugu/Tamil/etc. search.

## Adversarial query examples required

- one common title shared by 10 films;
- title with punctuation only difference;
- Telugu title typed in English letters;
- Tamil name with multiple romanizations;
- Hindi title in Devanagari and Latin;
- Japanese original vs English international title;
- actor known primarily by mononym;
- two actors with same name;
- movie known under old working title;
- episode with same title as series;
- typo within short 3–4 character title;
- numeric title (`96`, `24`, etc.) where year parsing can misfire.

## API behavior

Search endpoint should return CAS IDs and current projections, not provider records.

Conceptual request:
```text
/search?q=...&type=work&language=te&year=...
```

Conceptual response includes:
- entity ID/type;
- display title/name;
- original title;
- year;
- media type;
- localized context;
- lightweight disambiguation fields;
- rights-approved thumbnail reference.

Detailed entity data comes from canonical entity endpoints.

## Privacy/personalization

Core search ranking must work without personal profiling.

Later personalization can alter discovery/ranking as a separate layer, but exact search correctness remains deterministic enough to test independently.

## Failure behavior

If dedicated search projection is unavailable:
- API can fall back to constrained PostgreSQL canonical lookup for basic title/ID search where practical;
- canonical data remains available;
- search outage never corrupts data.

## Lock criteria

Move to LOCKED only when:
- multilingual query corpus exists;
- Indian-script/transliteration quality targets are defined;
- Postgres prototype meets initial quality/latency thresholds or dedicated-engine need is proven;
- search/identity thresholds are explicitly separated;
- redirect/merge behavior is tested;
- public visibility rules prevent weak Leads from leaking into normal search.
