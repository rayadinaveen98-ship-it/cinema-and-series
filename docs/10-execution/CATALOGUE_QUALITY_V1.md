# Catalogue Quality V1

**Status: BASELINE ESTABLISHED — REMEDIATION ACTIVE**  
**Started: 2026-09-16**  
**Baseline catalogue: 16,184 production titles (8,150 movies + 8,034 series)**

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

## Measured production baseline — 2026-09-16

The first complete `Catalogue Quality V1` production workflow passed successfully. It captured read-only D1 snapshots, ran all six audit-engine regression tests, generated JSON and Markdown reports, and preserved the audit artifact.

### Structural integrity

- **S0 Critical: 0**
- **S1 High: 0**
- S2 Medium: 11,375
- S3 Low: 8,034

This establishes that the current catalogue has no detected critical cross-type identity collisions, blank public identities, impossible series year ordering, unresolved QID-only public titles, invalid exact movie release years, or missing production source locators under the V1 rules.

### Production projection

| Projection | Count |
| --- | ---: |
| Exact-date movie rows | 2,736 |
| Year-precision catalogue movie rows | 5,613 |
| Exact movie/catalogue QID overlaps suppressed | 199 |
| Projected movies | 8,150 |
| Projected series | 8,034 |
| **Combined catalogue** | **16,184** |

### Movie coverage

| Dimension | Coverage |
| --- | ---: |
| Identity title | 100.00% (8,150/8,150) |
| Release year | 100.00% (8,150/8,150) |
| Country | 100.00% (8,150/8,150) |
| Provenance locator | 100.00% (8,150/8,150) |
| Language | 61.18% (4,986/8,150) |
| Wikidata identity | 48.49% (3,952/8,150) |
| Native title | 0.00% (0/8,150) |
| Poster on exact movie rows | 0.00% (0/2,736) |

### Series coverage

| Dimension | Coverage |
| --- | ---: |
| Identity title | 100.00% (8,034/8,034) |
| Country | 100.00% (8,034/8,034) |
| Provenance locator | 100.00% (8,034/8,034) |
| Series kind | 100.00% (8,034/8,034) |
| Wikidata identity | 98.59% (7,921/8,034) |
| First-air year | 97.22% (7,811/8,034) |
| Language | 3.05% (245/8,034) |
| Native title | 0.00% (0/8,034) |
| Lifecycle status | 0.00% (0/8,034) |

### Findings by active rule

| Rule | Count |
| --- | ---: |
| `METADATA.LANGUAGE_UNKNOWN` | 11,152 |
| `METADATA.YEAR_UNKNOWN` | 223 |
| `SERIES.LIFECYCLE_UNKNOWN` | 8,034 |

The largest quality problem is therefore **metadata enrichment, not structural identity integrity**. Series language coverage is the highest-impact next remediation target.

### Priority Indian-language catalogue counts

| Language | Movies | Series | Total |
| --- | ---: | ---: | ---: |
| Hindi | 617 | 220 | 837 |
| Malayalam | 624 | 23 | 647 |
| Tamil | 482 | 0 | 482 |
| Telugu | 453 | 0 | 453 |
| Kannada | 346 | 2 | 348 |
| Bengali | 236 | 0 | 236 |
| Marathi | 191 | 0 | 191 |
| Punjabi | 101 | 0 | 101 |
| Gujarati | 11 | 0 | 11 |

These are current operational counts based on explicit language metadata. The many zero/low series counts are strongly affected by the 3.05% series-language coverage and must not be interpreted as actual absence of those industries from the catalogue.

## Artifacts

Every production audit preserves for 30 days:

- machine-readable quality report JSON;
- human-readable Markdown report;
- the three read-only D1 snapshots used as the audit input.

This makes each result reproducible and debuggable.

First baseline artifact:
- workflow: `Catalogue Quality V1`;
- run: `35132955496`;
- artifact: `catalogue-quality-v1` (`10462445054`).

## Acceptance gate

Catalogue Quality V1 baseline requires:

1. quality-engine unit tests are green — **PASS**;
2. production D1 snapshots can be captured reproducibly — **PASS**;
3. the multidimensional report is generated successfully — **PASS**;
4. priority India-language counts are visible — **PASS**;
5. **S0 Critical = 0** — **PASS**;
6. the production artifact is preserved by GitHub Actions — **PASS**.

**Baseline gate: PASS.**

S1/S2/S3 findings become the ordered remediation/enrichment backlog; thresholds will be set only from measured evidence rather than invented retroactively.

## Active remediation order

1. **Series language enrichment** — current explicit coverage 3.05%; preserve provenance and never infer language from country alone.
2. **Series first-air-year completion** — 223 records currently lack explicit year context.
3. **Native/original title enrichment** — currently absent from both projections.
4. **Movie language enrichment** — current explicit coverage 61.18%.
5. **Series lifecycle enrichment** — currently unknown across the projection; treat as low severity unless stronger evidence is available.
6. **Artwork pipeline** — exact movie poster coverage is currently 0%; publication remains subject to the repository artwork-rights policy.
7. Execute multilingual search benchmarks after language/title enrichment is materially improved.
8. Resume bounded catalogue growth toward 25K, then 50K+, with regression gates that prevent quality backsliding.
