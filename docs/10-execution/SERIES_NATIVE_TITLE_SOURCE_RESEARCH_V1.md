# Series Native / Original Title Source Research V1

**Status: ANALYSIS COMPLETE — NO PRODUCTION WRITE APPROVED**  
**Completed: 2026-09-17**

## Goal

Measure whether explicit Wikidata original/native-title evidence is rich enough to justify a production enrichment pass for `series_titles.native_title` without guessing from English labels, Wikipedia page titles, scripts, countries, or inferred language.

## Production snapshot

The analysis covered every SeriesRun row that currently has a usable Wikidata identity and a missing `native_title`:

- total SeriesRun records: **8,034**
- QID-backed missing-native-title snapshot: **7,921**
- shards: **8**
- production mutation: **none**

## Explicit source contract tested

Only two explicit evidence paths were allowed:

1. Wikidata **P1705 — native label**;
2. Wikidata **P1476 — title**, but only when that exact title statement is explicitly qualified with **P3831 = Q1294573 (original title)**.

The resolver rejected:

- unqualified P1476 values;
- translated/localized titles without explicit original-title role evidence;
- inferred original titles from labels, script, country, language, Wikipedia page titles, or other metadata;
- ambiguous or conflicting explicit values.

## Reliability behavior

Wikidata requests used the existing hardened request policy:

- GET requests;
- paced entity batches;
- HTTP 429 retry with `Retry-After` support;
- HTTP-200 MediaWiki `maxlag` / `ratelimited` detection and bounded retry;
- API failures never converted into fake missing-metadata outcomes.

One shard initially stopped after persistent `maxlag`. Only that shard was retried; the retry succeeded. All eight shard outputs then validated and aggregated successfully.

## Final measured yield

Authoritative analysis run `35193563627` completed with:

- candidates: **7,921**
- safe explicit updates: **28**
- missing explicit claim: **7,893**
- ambiguous: **0**
- explicit-source conflicts: **0**
- unusable explicit values: **0**

Source split for the 28 safe values:

- `wikidata:P1705`: **9**
- `wikidata:P1476+P3831=Q1294573`: **19**

Overall safe yield: **28 / 7,921 = 0.35%**.

## Decision

**Do not perform a production native-title write from this V1 source contract.**

The tested evidence is high-confidence but far too sparse to justify a production enrichment workflow at this stage. Applying only 28 rows would move Series native-title coverage from 0% to roughly 0.35% while adding schema and operational complexity that does not materially improve the product.

The experimental feature branch remains useful as research evidence, but its migration and enrichment implementation should not be promoted to production unless the source strategy changes materially.

## Product implication

Native/original title enrichment should move back into roadmap design rather than remain the immediate execution priority. Before revisiting it, define a broader provenance-safe source strategy, potentially combining additional authoritative sources where licensing, semantics, and attribution are acceptable.

Until then:

- production database remains unchanged by this research slice;
- current `native_title` coverage remains 0%;
- no quality regression was introduced;
- roadmap planning should decide whether native titles are important enough to justify multi-source work relative to higher-value priorities such as movie language coverage, lifecycle status, artwork, search, visible detail-page UX, and catalogue growth.
