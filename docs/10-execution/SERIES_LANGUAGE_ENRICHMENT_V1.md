# Series Language Enrichment V1

**Status: IMPLEMENTATION ACTIVE**  
**Started: 2026-09-16**

## Why this is next

The first Catalogue Quality V1 production baseline measured:

- total SeriesRun records: **8,034**;
- explicit language known: **245 / 8,034 (3.05%)**;
- explicit language unknown: **7,789**;
- Wikidata identity mapped: **7,921 / 8,034 (98.59%)**.

This makes SeriesRun language the highest-impact metadata remediation target that can be improved from an already-attached stable identity source.

## Source contract

V1 enrichment uses only explicit Wikidata **P364 — original language of film or TV show** claims.

It does **not** infer language from:

- country;
- title spelling or script;
- cast/crew nationality;
- Wikipedia category unless that category already supplied the existing value;
- popularity or market assumptions.

## Resolution policy

A production row is eligible only when:

1. current `language_name` is missing or `Unknown`;
2. the row has a valid Wikidata QID;
3. Wikidata exposes at least one non-deprecated P364 claim.

Resolution behavior:

- one unique usable P364 value → resolve;
- one unique preferred-rank P364 value → resolve to the preferred value;
- multiple preferred values → ambiguous, no write;
- multiple normal-rank values with no unique preferred value → ambiguous, no write;
- missing P364 → no write;
- unresolved language-item label → no write.

The scalar V1 field will not silently collapse genuinely multilingual works.

## Provenance

Migration `0019_series_language_provenance.sql` adds:

- `language_source`;
- `language_source_url`.

Existing explicit languages are backfilled as `wikipedia_category` with their existing source URL. New P364 resolutions are stored as `wikidata:P364` with the SeriesRun Wikidata entity URL.

## Write safety

Generated SQL updates include both canonical row ID and Wikidata QID and only execute while the production value is still unresolved. A language resolved after snapshot capture is therefore not overwritten by a stale enrichment artifact.

## Bounded production run

The first workflow accepts at most **8,000** unresolved QID-backed SeriesRun rows, enough to cover the current production backlog while retaining a hard upper bound.

The workflow:

1. runs unit tests;
2. applies D1 migrations;
3. captures a read-only unresolved-language snapshot;
4. queries Wikidata in bounded batches;
5. separates resolved, ambiguous, missing-claim and missing-label cases;
6. generates provenance-safe SQL;
7. applies only explicit resolved values;
8. verifies post-write production coverage and provenance counts;
9. preserves inputs/results/SQL as a 30-day artifact.

## Acceptance

The slice is complete when:

- enrichment unit tests pass;
- migration applies cleanly;
- production run completes without overwriting known language values;
- every newly written language has explicit provenance;
- post-run language coverage is measured and committed to this document;
- Catalogue Quality V1 remains S0=0 after enrichment.

No numeric coverage target is invented before the first P364 production run. The measured yield determines whether a second source or representation change is justified.
