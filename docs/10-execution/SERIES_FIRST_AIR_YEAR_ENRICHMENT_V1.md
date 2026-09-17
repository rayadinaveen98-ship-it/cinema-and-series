# Series First-Air-Year Enrichment V1

**Status: COMPLETE — PRODUCTION VERIFIED**  
**Started: 2026-09-17**  
**Completed: 2026-09-17**

## Why this slice was prioritized

Catalogue Quality V1 after Series Language Enrichment measured:

- total SeriesRun records: **8,034**;
- first-air year known: **7,811 / 8,034 (97.22%)**;
- first-air year unknown: **223**;
- Wikidata identity mapped: **7,921 / 8,034 (98.59%)**;
- S0 Critical: **0**;
- S1 High: **0**.

The missing-year backlog was small, bounded, and high-value because it directly affects chronology, discovery, filtering, and lifecycle validation.

## Source contract

V1 uses only explicit Wikidata **P580 — start time** claims attached to the already-mapped SeriesRun Wikidata entity.

For this slice, P580 is interpreted only as a candidate first-broadcast/start year for the SeriesRun record. The resolver does **not** infer a year from:

- title text;
- Wikipedia category text;
- country or language;
- publication/release properties outside the locked P580 contract;
- current year, popularity, season data, or lifecycle assumptions.

## Eligibility and resolution policy

A production row is eligible only when:

1. `first_air_year IS NULL`;
2. the row has a valid Wikidata QID;
3. Wikidata exposes a usable non-deprecated P580 time claim.

A P580 value is usable only when it has at least year precision, represents a CE year, and falls inside the production schema range **1900–2200**.

Resolution behavior:

- one unique usable year → resolve;
- multiple usable claims that all collapse to the same year → resolve;
- one unique usable preferred-rank year → resolve to the preferred year;
- multiple preferred years → ambiguous, no write;
- unusable preferred claim → no fallback to normal claims;
- multiple distinct normal years → ambiguous, no write;
- missing P580 → no write;
- P580 present but below year precision / invalid → unusable, no write;
- missing usable Wikidata identity → no write.

The resolver deliberately favors leaving a row unresolved over silently choosing among conflicting dates.

## Provenance

Migration `0020_series_first_air_year_provenance.sql` adds:

- `first_air_year_source`;
- `first_air_year_source_url`.

New V1 writes store:

- `first_air_year_source = 'wikidata:P580'`;
- `first_air_year_source_url = https://www.wikidata.org/wiki/<Series QID>`.

Existing first-air-year values are intentionally **not** backfilled with invented field-level provenance. Those rows predate this field contract, and the exact year-bearing source category cannot always be reconstructed safely after catalogue merges. Their existing record-level `source_category` / `source_url` provenance remains unchanged.

## Write safety and resilience

Generated SQL matches canonical row ID and Wikidata QID, requires `first_air_year IS NULL` at write time, sets field-level provenance in the same update, and never overwrites an existing year.

Normal pushes perform read-only analysis only. Production writes require an explicit guarded `workflow_dispatch` on `main` with `apply_writes=true`. The operator-request workflow verifies the exact successful analysis run, head SHA, aggregate artifact, snapshot partition, and enrichment-critical code immutability before dispatching writes.

The workflow also treats Cloudflare D1 row-read quota exhaustion as a clean defer during analysis but a hard stop in write mode, uses paced Wikidata batches, retries HTTP 429 and HTTP-200 MediaWiki `maxlag` / `ratelimited` errors, and never converts API failures into fake missing metadata.

## Production results

### Verified read-only analysis

Authoritative `main` analysis run `35186244929` at commit `216ec13bdeb830d4262b3aba90dfd8292fc5105f` completed successfully:

- missing-year snapshot: **223**
- rows with usable Wikidata QID: **219**
- safe explicit P580 updates: **81**
- missing P580: **138**
- missing usable Wikidata identity: **4**
- ambiguous: **0**
- unusable / insufficient-precision time: **0**

The branch dry run and authoritative `main` run produced the same totals.

### Guarded production write

Operator authorization run `35186376253` completed successfully and dispatched the guarded production write only after validating the analysis evidence and unchanged critical code.

Production write run `35186384356` completed successfully:

- migration `0020_series_first_air_year_provenance.sql`: **applied successfully**
- fresh production snapshot: **223**
- live P580 re-evaluation: **81 safe updates**
- D1 update statements executed: **81**
- missing P580: **138**
- missing identity: **4**
- ambiguous: **0**
- unusable time: **0**
- final `verify-write`: **successful**

The branch analysis, authoritative `main` analysis, and live production re-evaluation all matched exactly.

### Post-write production verification

Production verification measured:

- total series: **8,034**
- first-air year known: **7,892 / 8,034 (98.23%)**
- first-air year unknown: **142**
- new `wikidata:P580` field-provenance rows: **81**
- invalid provenance rows: **0**
- net increase in known first-air years: **+81**
- coverage improvement: **97.22% → 98.23%**

Only the 81 new P580-derived values have the new field-level provenance. The older 7,811 populated years retain their pre-existing record-level provenance and are not mislabeled as P580-derived.

## Post-write Catalogue Quality regression

Catalogue Quality V1 run `35186788315` completed successfully after the production write:

- catalogue total: **16,184**
- projected movies: **8,150**
- projected series: **8,034**
- **S0 Critical: 0**
- **S1 High: 0**
- S2 Medium: **7,486** (down from **7,567** before this enrichment)
- S3 Low: **8,034**
- `METADATA.LANGUAGE_UNKNOWN`: **7,344**
- `METADATA.YEAR_UNKNOWN`: **142** (down from **223**)
- `SERIES.LIFECYCLE_UNKNOWN`: **8,034**
- measured first-air-year coverage: **7,892 / 8,034 (98.23%)**
- measured series language coverage: **4,053 / 8,034 (50.45%)**

This confirms the year enrichment improved metadata completeness without introducing a critical or high-severity structural regression.

## Post-write audit reliability

GitHub did not emit the expected secondary `workflow_run` audit after the production workflow was dispatched through `GITHUB_TOKEN`. PR #19 therefore added `Catalogue Quality Post-Write Watch` as a bounded recovery mechanism.

The watcher:

- recognizes only successful enrichment `workflow_dispatch` runs whose `verify-write` job succeeded;
- checks whether a newer Catalogue Quality V1 run already exists;
- dispatches the audit only when the verified production write is still unaudited;
- runs on installation/manual invocation and every 15 minutes as a fallback;
- never mutates catalogue data.

Its first run `35186776121` successfully detected the unaudited first-air-year production write and dispatched Catalogue Quality V1 run `35186788315`.

## Acceptance

- dedicated enrichment tests pass: **YES — 15 tests**
- 223-row production backlog captured cleanly: **YES**
- read-only analysis partitions the snapshot exactly: **YES**
- migration applies cleanly: **YES**
- existing first-air years are never overwritten: **YES**
- every new resolved year has explicit P580 provenance: **YES — 81 / 81**
- invalid provenance rows: **0**
- post-write production coverage measured: **YES — 98.23%**
- Catalogue Quality V1 post-write regression: **YES — S0=0, S1=0**
- final measured results committed to this document: **YES**

## Remaining year backlog

The remaining **142** unresolved series are intentionally not guessed:

- **138** have no explicit usable P580 claim in the V1 source contract;
- **4** lack usable Wikidata identity.

Any future year source must preserve the same explicit provenance and no-inference standard.

## Next quality priorities

With first-air-year coverage raised to 98.23%, the current sequence is:

1. native/original titles;
2. movie language enrichment;
3. series lifecycle status;
4. artwork coverage;
5. multilingual search benchmarks;
6. resume bounded catalogue growth toward 25K → 50K with quality gates.
