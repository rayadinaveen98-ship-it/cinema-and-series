# Catalogue Quality V1

**Status: ACTIVE**  
**Started: 2026-09-16**  
**Baseline catalogue entering milestone: 16,184 production titles (8,150 movies + 8,034 series)**

## Goal

Turn catalogue scale into measurable catalogue trustworthiness before the next large growth milestone.

This milestone audits production read-only. It does not silently rewrite titles, auto-merge uncertain identities, or fabricate missing values.

## V1 principles

- Quality and coverage are separate concepts.
- Do not collapse multidimensional coverage into a consumer-facing or internal single score.
- Missing remains missing; `Unknown` is not converted into guessed metadata.
- Exact external-ID collisions across incompatible media types are critical.
- Duplicate candidates are review findings, not automatic merge instructions.
- Lower-severity thresholds are not invented merely to make CI pass.
- Only S0 structural-integrity findings block the initial production audit workflow.

## Production audit inputs

The workflow captures three D1 projections:

1. `movies` — exact-date movie records, including artwork state;
2. `catalogue_titles` — year-precision movie discovery records;
3. `series_titles` — series-run records.

When an exact movie and a year-precision catalogue row share the same valid Wikidata identity, the exact movie projection wins for catalogue counting so the audit matches the public production count model.

## Initial finding rules

### S0 Critical

- blank public identity title;
- same Wikidata identity simultaneously projected as movie and series;
- series `last_air_year` earlier than `first_air_year`.

### S1 High

- unresolved QID-only title;
- invalid exact movie release date/year;
- missing source locator on catalogue or series projection.

### S2 Medium

- unknown language;
- unknown country;
- missing year context;
- unresolved series kind;
- same normalized title/year backed by multiple distinct Wikidata identities (duplicate candidate only).

### S3 Low

- unresolved series lifecycle state.

## Coverage dimensions

Reported independently for movies and series where applicable:

- identity title;
- year context;
- language;
- country;
- Wikidata identity mapping;
- native title;
- provenance/source locator;
- exact-movie poster coverage;
- series kind;
- series lifecycle status.

The report also exposes counts for priority Indian-language cohorts:

- Telugu
- Tamil
- Malayalam
- Kannada
- Hindi
- Bengali
- Marathi
- Gujarati
- Punjabi

These counts are operational catalogue counts, not claims of absolute industry coverage.

## Artifacts

Every production audit preserves for 30 days:

- machine-readable quality report JSON;
- human-readable Markdown report;
- the three read-only D1 snapshots used as the audit input.

This makes each result reproducible and debuggable.

## Acceptance gate

Catalogue Quality V1 baseline is established when:

1. quality-engine unit tests are green;
2. production D1 snapshots can be captured reproducibly;
3. the multidimensional report is generated successfully;
4. priority India-language counts are visible;
5. **S0 Critical = 0** or every S0 is explicitly diagnosed and remediated before the gate is declared complete;
6. the production artifact is preserved by GitHub Actions.

S1/S2/S3 findings become the ordered remediation/enrichment backlog; their thresholds will be set only from evidence after the baseline is measured.

## Successor work

After the baseline is healthy:

1. remediate critical/high integrity defects;
2. enrich core metadata and provenance;
3. improve India regional-language coverage by measured cohorts;
4. execute multilingual search benchmarks;
5. resume bounded catalogue growth toward 25K, then 50K+, while preventing quality regression.
