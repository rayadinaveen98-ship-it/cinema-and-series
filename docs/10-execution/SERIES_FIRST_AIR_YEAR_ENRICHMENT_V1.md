# Series First-Air-Year Enrichment V1

**Status: IMPLEMENTATION ACTIVE**  
**Started: 2026-09-17**

## Why this is next

Catalogue Quality V1 after Series Language Enrichment measured:

- total SeriesRun records: **8,034**;
- first-air year known: **7,811 / 8,034 (97.22%)**;
- first-air year unknown: **223**;
- Wikidata identity mapped: **7,921 / 8,034 (98.59%)**;
- S0 Critical: **0**;
- S1 High: **0**.

The missing-year backlog is small, bounded, and high-value because it directly affects chronology, discovery, filtering, and lifecycle validation.

## Source contract

V1 uses only explicit Wikidata **P580 — start time** claims attached to the already-mapped SeriesRun Wikidata entity.

For this slice, P580 is interpreted only as a candidate first-broadcast/start year for the SeriesRun record. The resolver does **not** infer a year from:

- title text;
- Wikipedia category text;
- country or language;
- publication/release properties that are not the locked P580 contract;
- current year, popularity, season data, or lifecycle assumptions.

## Eligibility

A production row is eligible only when:

1. `first_air_year IS NULL`;
2. the row has a valid Wikidata QID;
3. Wikidata exposes a usable non-deprecated P580 time claim.

Rows without usable Wikidata identity remain unresolved and are reported separately.

## Time-resolution policy

A P580 value is usable only when:

- it has at least **year precision**;
- it represents a CE year;
- the year fits the production schema range **1900–2200**.

Resolution behavior:

- one unique usable year → resolve;
- multiple usable claims that all collapse to the same year → resolve;
- one unique usable preferred-rank year → resolve to the preferred year;
- multiple preferred years → ambiguous, no write;
- an unusable preferred claim → no fallback to normal claims;
- multiple distinct normal years → ambiguous, no write;
- missing P580 → no write;
- P580 present but below year precision / invalid → unusable, no write.

The resolver deliberately favors leaving a row unresolved over silently choosing among conflicting dates.

## Provenance

Migration `0020_series_first_air_year_provenance.sql` adds:

- `first_air_year_source`;
- `first_air_year_source_url`.

New V1 writes store:

- `first_air_year_source = 'wikidata:P580'`;
- `first_air_year_source_url = https://www.wikidata.org/wiki/<Series QID>`.

Existing first-air-year values are intentionally **not** backfilled with invented field-level provenance. Those rows predate this field contract, and the exact year-bearing source category cannot always be reconstructed safely after catalogue merges. Their existing record-level `source_category` / `source_url` provenance remains unchanged.

## Write safety

Generated SQL:

- matches canonical row ID;
- matches Wikidata QID;
- requires `first_air_year IS NULL` at write time;
- sets field-level provenance in the same update;
- never overwrites an existing year.

Normal pushes perform **read-only analysis only**. Production writes require an explicit `workflow_dispatch` on `main` with `apply_writes=true`.

A separate operator-request workflow verifies:

- the referenced analysis run succeeded on `main`;
- the analysis head SHA is exact;
- the summary artifact is retained and matches expected totals;
- enrichment-critical code has not changed since analysis;
- the request partitions the snapshot exactly;

before it dispatches the guarded production-write workflow.

## Quota / API resilience

The current backlog is bounded to at most **500** unresolved rows, comfortably above the measured 223-row backlog.

The workflow:

1. runs dedicated unit tests;
2. captures one stable production snapshot;
3. treats Cloudflare D1 daily row-read quota exhaustion as a clean defer on analysis runs but a hard stop in write mode;
4. queries Wikidata in small paced batches;
5. retries HTTP 429 plus HTTP-200 MediaWiki `maxlag` / `ratelimited` errors;
6. never converts API errors into fake missing-metadata findings;
7. separates resolved, ambiguous, missing-claim, unusable-time, and missing-identity cases;
8. preserves JSON + generated SQL as artifacts before any production mutation;
9. applies only explicit resolved values;
10. verifies final production coverage and P580 provenance after writes.

## Acceptance

The slice is complete when:

- dedicated tests pass;
- the 223-row production backlog is captured cleanly;
- read-only analysis partitions the snapshot exactly;
- migration applies cleanly;
- production writes do not overwrite existing years;
- every new year has explicit P580 provenance;
- post-write production coverage is measured;
- Catalogue Quality V1 remains **S0=0 / S1=0** after enrichment;
- final measured results are committed to this document.

## Next quality priorities

After first-air-year remediation, the current sequence remains:

1. native/original titles;
2. movie language enrichment;
3. series lifecycle status;
4. artwork coverage;
5. multilingual search benchmarks;
6. resume bounded catalogue growth toward 25K → 50K with quality gates.
