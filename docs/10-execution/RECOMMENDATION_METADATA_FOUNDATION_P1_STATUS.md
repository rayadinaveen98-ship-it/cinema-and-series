# Recommendation Metadata Foundation P1 — Execution Status

**Status:** ACTIVE — READ-ONLY ANALYSIS + MATERIALIZATION FOUNDATION  
**Date:** 2026-09-17  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Shared schema

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

The shared title registry is keyed by stable Wikidata identity. Exact-date `movies` rows take precedence over duplicate QIDs in `catalogue_titles`; Series remains a distinct media type. A QID appearing as both Movie and Series is a hard audit failure.

## Production identity baseline

Read-only production projection on 2026-09-17:

- Movie QIDs: **3,952**
- Series QIDs: **7,921**
- total recommendation candidates: **11,873**
- duplicate movie projection overlaps safely suppressed: **199**
- Movie/Series cross-type QID collisions: **0**

## Coverage audit

Workflow: `Recommendation Metadata Foundation V1`

The corrected full 8-shard audit is read-only and currently active. Each shard is bounded to 2,000 titles and Wikidata requests are paced sequentially.

First validated shard:

- candidates: **1,463**
- explicit genre relations: **1,330**
- explicit people relations: **5,035**
- recommendation-ready Movies: **352**
- recommendation-ready Series: **310**
- total recommendation-ready sample: **662 / 1,463 = 45.25%**
- unique genre QIDs observed: **219**
- unique people QIDs observed: **4,608**
- production mutation: **false**

This yield is useful enough to continue P1, but it is not yet authorization for production writes.

## Dry-run materializer

`scripts/enrich_recommendation_metadata.py` converts the same explicit source contract into normalized rows and transaction-wrapped SQL artifacts.

Important safety behavior:

- never connects to D1 directly
- never mutates production
- English Wikidata labels preferred; explicit `mul` label accepted as fallback
- unresolved labels skip only the dependent relationship
- Movie `P170` is ignored; Series `P170` is allowed
- relationship SQL is idempotent (`INSERT OR IGNORE`)
- entities use QID-stable IDs
- every relationship retains source property + source entity URL

Tests: `tests/test_recommendation_metadata_enrichment.py`.

## Read-only materialization workflow

`Recommendation Metadata Materialization V1` is manual-only and read-only. It:

1. captures stable QID-backed production snapshots
2. validates the shared projection
3. resolves allowed claims + entity labels in 8 bounded sequential shards
4. generates JSON + SQL artifacts per shard
5. verifies emitted relationship counts never exceed explicit source relationship counts
6. aggregates materialization evidence

It has no D1 write path.

## Remaining P1 gates

Before production enrichment:

1. complete the full global 8-shard coverage audit
2. add and run India-language cohort coverage breakdown required by the locked roadmap
3. run main-branch read-only materialization analysis
4. quantify unresolved labels and relationship volume
5. create immutable analysis evidence / operator write request gate
6. verify the production catalogue projection has not drifted since analysis
7. only then apply migration `0021` and bounded shard SQL
8. verify normalized row counts and referential integrity
9. run Catalogue Quality V1 and keep S0/S1 at zero
10. document final recommendation-ready coverage and unresolved backlog

## P1 exit rule

Phase P2/onboarding logic must not begin merely because the schema exists. P1 exits only after a meaningful, production-verified portion of the catalogue has safe recommendation metadata and the post-write quality gate remains clean.
