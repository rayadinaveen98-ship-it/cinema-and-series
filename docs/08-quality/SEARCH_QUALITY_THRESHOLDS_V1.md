# Search Quality Thresholds — Cinema and Series V1

**Status: LOCKED TARGETS / EXECUTION PENDING**  
**Date: 2026-09-14**

## Purpose

This document freezes the measurable search-quality targets that Cinema and Series V1 must satisfy before public launch. The thresholds are deliberately segmented by query class and script so a strong global average cannot hide poor Indian-language search.

These targets govern the first Postgres FTS + `pg_trgm` implementation. If that implementation cannot meet them after reasonable tuning at representative catalogue size, a dedicated search engine may be introduced behind the existing SearchDocument abstraction.

# 1. Benchmark design

The search benchmark must contain at least **2,000 labeled queries** before launch, generated from the validation corpus plus additional search-specific cases.

Minimum query composition:
- 300 exact canonical/display-title queries;
- 250 native-script exact-title queries;
- 350 Latin-script transliteration/romanization queries for Indian titles/names;
- 200 sourced alternate/localized/working-title queries;
- 200 realistic typo/spelling-variation queries;
- 200 same-title/same-name collision queries;
- 150 Person/credited-as/stage-name queries;
- 100 Series/Episode/Special queries;
- 100 obscure historical/archival title queries;
- 150 mixed qualifier queries using year/language/type/person context.

Queries may belong to several secondary analysis tags, but each has one primary class.

# 2. Mandatory language/script floors

The benchmark must include meaningful native-script and Latin-transliteration coverage for at least:
- Telugu (`Telugu` script + Latin);
- Tamil (`Tamil` + Latin);
- Malayalam (`Malayalam` + Latin);
- Kannada (`Kannada` + Latin);
- Hindi/Marathi (`Devanagari` + Latin);
- Bengali (`Bengali` + Latin).

Additional India languages/scripts are strongly encouraged and count toward the India benchmark, but the six groups above are V1 minimums.

No priority language/script segment may contain fewer than **75 labeled queries** by launch, and at least 30 of those must test Latin transliteration/romanization where applicable.

# 3. Correctness targets

## 3.1 Exact title/name queries

For a query that exactly matches a unique current canonical title/name or exact sourced alias:
- **Top-1 success >= 99.5%** overall;
- **Top-1 success >= 99.0%** in every priority script segment;
- **Top-3 success >= 99.8%** overall;
- zero-result rate <= 0.1%.

An exact obscure/historical title must not be buried merely because a more popular title has similar tokens.

## 3.2 Native-script queries

For an exact or normalized native-script title/name query:
- **Top-1 >= 99.0%** per priority script;
- **Top-3 >= 99.5%** per priority script;
- Unicode normalization differences must not cause a known target to disappear.

## 3.3 Latin transliteration / romanization

For labeled common Latin spellings of Indian native-script titles/names:
- **Top-1 >= 92%** per priority language group;
- **Top-3 >= 97%** per priority language group;
- **Top-10 >= 99%** per priority language group;
- zero-result rate <= 1%.

A transliteration target may rank below another plausible exact Latin title, but the intended entity must remain highly discoverable.

## 3.4 Alternate/localized/working titles

For a sourced title alias that is valid for the entity:
- Top-1 >= 97%;
- Top-3 >= 99%;
- redirects from historical/working title must resolve to the current CAS entity without creating a duplicate public result.

Generated search aliases do not become official Name records.

## 3.5 Typo/spelling variation

For realistic one-edit/two-edit or spacing/punctuation variants:
- Top-1 >= 88%;
- Top-3 >= 95%;
- Top-10 >= 98%;
- no unrelated high-popularity title may consistently dominate a much closer lexical match.

Short titles of 1–4 characters are scored separately because aggressive fuzzy matching is unsafe.

## 3.6 Same-title / same-name collisions

When the query is ambiguous and no disambiguating context is supplied:
- all plausible gold entities expected by the case must appear in Top-10 >= 98% of cases;
- UI payload must expose year/language/type/principal-person context sufficient to distinguish them;
- popularity may rank plausible entities but must not hide exact-title historical works.

When the user supplies a decisive qualifier such as year + language/type:
- **Top-1 >= 99%**.

## 3.7 Person aliases / credited-as names

For sourced stage names, credited-as names and native-script aliases:
- Top-1 >= 97%;
- Top-3 >= 99%;
- same-name collision queries must not be auto-resolved as one Person identity.

# 4. Wrong-entity safety

Search is recall-oriented, but exact-match behavior still has safety requirements.

For a known-target query:
- intended entity absent from Top-10: **critical search miss**;
- exact unique title/name query returning an unrelated entity at Top-1: **high-severity regression**;
- a search result must never trigger or imply an identity merge.

Search rank scores are prohibited as direct inputs to automatic entity merge decisions.

# 5. Latency targets

Measured at the API/search-service boundary, excluding end-user mobile network latency, on a representative production-like dataset and warm steady-state environment:
- p50 <= 75 ms;
- p95 <= 250 ms;
- p99 <= 500 ms;
for ordinary first-page title/person search.

Cold-start, bulk-reindex and pathological admin queries are reported separately and do not dilute these measurements.

If Postgres cannot meet both quality and latency targets after indexes/query plans are reasonably tuned, the search-escalation ADR may select a dedicated search engine. Canonical PostgreSQL remains authoritative regardless.

# 6. Freshness targets

After a committed canonical change and successful outbox processing:
- high-priority title/name correction visible in search p95 <= 2 minutes;
- approved new upcoming Work visible p95 <= 5 minutes;
- identity merge removes duplicate public result and creates redirect p95 <= 5 minutes;
- batch archival imports may index asynchronously but must expose queue/progress state.

Search projection failures must never roll back canonical truth.

# 7. Required adversarial groups

The benchmark must explicitly include:
- `Baahubali/Bahubali`-style Romanization variance;
- native-script and Latin queries for the same Indian Work;
- titles differing only in punctuation/spacing;
- numeric titles (`96`, `24`, etc.);
- same title across multiple Indian languages/years;
- dub/localized title resolving to original Work/Version context;
- working title resolving after final-title change;
- mononyms and initials;
- two people with identical or near-identical professional names;
- episode title identical to Series title;
- historical title with little/no popularity signal;
- English international title vs original-language title;
- query containing a four-digit number that is title content rather than year where applicable.

# 8. Regression gate

Every change to normalization, transliteration, ranking, SearchDocument generation or merge/redirect handling reruns the labeled benchmark.

Block release when:
- any priority script falls below its threshold;
- exact-title Top-1 regresses below target;
- known-target Top-10 misses increase materially;
- p95 latency exceeds target in representative tests without an approved exception;
- merged redirects/search visibility violate identity rules.

Global average improvements do not excuse a regression in Telugu, Tamil, Malayalam, Kannada, Devanagari or Bengali segments.

# 9. Freeze consequence

The numeric targets are now LOCKED. **Passing them remains an implementation/validation gate, not a Research Foundation assumption.**

`OD-Q04` may therefore move from OPEN to `LOCKED TARGET / EXECUTION PENDING`.
