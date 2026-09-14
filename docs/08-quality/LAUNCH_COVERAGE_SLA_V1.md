# Launch Coverage SLA — Cinema and Series V1

**Status: LOCKED TARGETS / MEASUREMENT EXECUTION PENDING**  
**Date: 2026-09-14**

## Principle

Cinema and Series V1 does **not** claim universal completeness.

Launch readiness is measured against defined benchmark populations and metadata dimensions, not a vanity total-title count.

# 1. Coverage dimensions

Measure separately:
- identity/existence;
- names/localization;
- core type/language/country;
- principal credits;
- release history;
- production lifecycle for upcoming titles;
- relationships (remake/dub/adaptation/etc.);
- provenance/evidence;
- music credits where applicable;
- artwork publication rights/availability.

Artwork is never allowed to drag core metadata quality down or hide records; it has its own metric.

# 2. Coverage denominator policy

There is no honest denominator for `all films ever made`.

Use explicit benchmark populations such as:
- authoritative/archival catalogues;
- selected director/actor/company filmographies;
- annual/language release lists from lawful reference sources;
- festival programmes;
- certification/public institutional lists where permitted;
- carefully adjudicated validation corpus cohorts.

Every published/internal coverage percentage must name its denominator.

Forbidden:
`India coverage = 94%`

Allowed:
`Core identity coverage = 94% of the locked Telugu 2010-2019 benchmark set (n=1,200)`

# 3. Mandatory launch benchmark groups

## India — modern cinema
For each priority language, maintain sampled/defined benchmark sets across at least 2000-present:
- Telugu;
- Tamil;
- Malayalam;
- Kannada;
- Hindi;
- Bengali;
- Marathi;
- additional languages as data allows.

## India — historical
Separate benchmark groups:
- pre-1931/silent;
- 1931-1949;
- 1950-1969;
- 1970-1989;
- 1990-1999.

Historical denominators must come from archival/scholarly/authoritative lists, not only modern APIs.

## Global
Benchmark populations across:
- US/English-language cinema;
- European cinema samples;
- East Asian cinema samples;
- major world-cinema festival/catalogue samples;
- series/episodic samples;
- animation/anime/documentary samples.

## Upcoming/future
Track a defined source-list population of officially announced upcoming projects rather than rumors.

# 4. P0 launch thresholds

Across the locked ~1,000 hard-case corpus:
- representation/model pass: **100% of adjudicated gold cases**;
- known critical false automatic merges: **0**;
- known critical false automatic Work/Version decisions: **0**;
- provenance available for every non-derived benchmark fact expected by the assertion: **100%**.

# 5. Core metadata coverage targets

For each priority modern India benchmark cohort before public V1:
- CAS identity: >= 98%;
- preferred/original/native title where knowable: >= 97%;
- Work type: >= 98%;
- original language(s): >= 97%;
- primary/original release year/date context: >= 95%;
- director: >= 95% for films where applicable;
- principal cast: >= 90%;
- production-company evidence: >= 85%;
- at least one provenance-bearing source path for P0 facts: >= 98%.

These percentages are measured against known benchmark facts, not empty source fields.

# 6. Historical India targets

Historical data is less complete by nature, so use different quality expectations:
- Work identity/existence: >= 95% of named benchmark titles;
- original/known title form: >= 90%;
- year/date with correct precision or explicit dispute/unknown state: >= 90%;
- director where historically known: >= 85%;
- survival/preservation state when benchmark specifies it: >= 95%;
- no invented exact date/person/credit to fill a historical gap: 100%.

`Unknown historically` counts as correct representation when supported by evidence.

# 7. Series targets

For series benchmark cohorts:
- Series identity: >= 98%;
- Season/StructureEdition representation: >= 97%;
- episode identity in selected benchmark series: >= 98%;
- provider-specific numbering must not overwrite another valid structure: 100% on gold edge cases;
- premiere/release context: >= 95% where benchmark evidence exists.

# 8. Upcoming-project freshness

For the defined tracked upcoming-title population:
- new eligible official announcement discovery target: <= 24h from source observation path once adapter/monitor exists;
- major release-date/status change target: <= 24h;
- high-priority India theatrical changes near release: target <= 12h when a lawful automated source path exists;
- stale upcoming title detection: daily quality check.

These are operational targets, not guarantees for sources we cannot lawfully monitor automatically.

# 9. Search SLA

Search quality follows `SEARCH_QUALITY_BENCHMARK_V1.md`.

No cohort can be considered successfully covered if its names exist in storage but ordinary native/romanized searches cannot retrieve them at the required ranking threshold.

# 10. Music coverage

For titles in the dedicated Indian music benchmark:
- film-level score/music-director representation: >= 95% where benchmark fact exists;
- song identity: >= 90% for the selected soundtrack benchmark;
- composer/lyricist/playback-singer relationship correctness: >= 95% of asserted relationships;
- MusicalWork vs Recording false collapse: 0 critical gold-case failures.

Music completeness is not required for every historical film before V1 launch.

# 11. Artwork SLA

Report separately:
- `% titles with rights-approved primary image`;
- `% people with rights-approved portrait`;
- placeholder usage.

No minimum artwork percentage is a launch blocker for the metadata database, provided the placeholder UX passes design acceptance.

# 12. Provenance SLA

For imported P0/P1 production data:
- source ID present: 100%;
- observation/retrieval timestamp: 100%;
- adapter/rule version: 100%;
- source-policy version/linkage: 100%;
- canonical decision explainable from eligible Claims: 100%.

# 13. No vanity-count launch gate

The following are explicitly **not** V1 launch criteria:
- `1 million movies imported`;
- `10 million records`;
- `more titles than competitor X`;
- `poster coverage > N%`.

A smaller measured, trustworthy database is preferred to a larger opaque one.

# 14. Launch report

Before public V1, generate a versioned `V1_DATA_READINESS_REPORT` containing:
- benchmark definitions and sizes;
- pass/fail percentages by cohort;
- known gaps;
- source coverage;
- stale/conflict counts;
- search metrics;
- open licensing limitations;
- historical uncertainty notes;
- explicit statement that universal completeness is not claimed.

The report is part of V1 Definition of Done.