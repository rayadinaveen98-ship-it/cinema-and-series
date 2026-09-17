# Recommendation Metadata Foundation P1 — Execution Status

**Status:** ACTIVE — FINGERPRINTED READ-ONLY AUDITS + MATERIALIZATION HARDENING  
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

## Current production identity baseline

Authoritative read-only production projection captured on 2026-09-17:

- Movie QIDs: **4,343**
- Series QIDs: **7,921**
- total recommendation candidates: **12,264**
- duplicate movie projection overlaps safely suppressed: **199**
- Movie/Series cross-type QID collisions: **0**
- projection SHA-256: **`86da6c202ca5013d595596226a80e9dbe008b25a4a7c6b656c61b7c3a1a17786`**

The fingerprint covers the canonical recommendation projection fields: Wikidata QID, media type, display title, source table, source ID, and source URL. A future production write must recapture the projection and match this fingerprint before applying analyzed metadata.

## Global coverage audit

Workflow: `Recommendation Metadata Foundation V1`  
Run: `35204375729`

The authoritative 8-shard audit is read-only, bounded to 2,000 titles per shard, and uses the fingerprinted production snapshot above.

Validated through shards 0–4; shard 5 is currently active. First three completed shards established a stable signal:

- candidates: **4,514**
- recommendation-ready: **2,088 / 4,514 = 46.26%**
- recommendation-ready Movies: **1,119**
- recommendation-ready Series: **969**
- cross-type identity collisions: **0**
- production mutation: **false**

Shard-level readiness has remained consistently around the mid-40% range, so the source contract has clearly useful yield. Final authorization still waits for the official 8-shard aggregate summary.

## India-language cohort audit

Workflow: `Recommendation Metadata India Cohort Audit`  
Run: `35204143430`

This audit uses the same production catalogue projection with language fields added only for cohort grouping. The preserved India snapshot was compared row-for-row with the authoritative global snapshot after removing `language_name`:

- Movies: **3,114 / 3,114 rows identical**
- catalogue Movies: **1,428 / 1,428 rows identical**
- Series: **7,921 / 7,921 rows identical**

Therefore the India cohort evidence is tied to the same canonical projection fingerprint: **`86da6c202ca5013d595596226a80e9dbe008b25a4a7c6b656c61b7c3a1a17786`**.

Validated through shards 0–5; shard 6 is currently active. Final language-specific readiness percentages will come from the workflow aggregate rather than hand-summed partial results.

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

## Fingerprint-bound materialization

`Recommendation Metadata Materialization V1` remains manual-only and read-only. The materialization path is now hardened so:

1. it captures the canonical production projection
2. it builds the deterministic projection manifest
3. each shard output carries the projection SHA-256
4. generated SQL includes the projection fingerprint as evidence metadata
5. aggregate materialization fails if shard projection fingerprints drift
6. aggregate candidate counts must match the manifest
7. explicit source relations must partition into emitted or missing-label relations

The latest hardening commit passed full Python tests, catalogue audit, web typecheck, and production web build.

## Migration numbering rule

The active Recommendation Metadata Foundation owns migration number **0021**.

A dormant `feature/series-native-title-enrichment-v1` branch also contains an unmerged `0021_series_native_title_provenance.sql`. That branch has no open PR and must be rebased/renumbered to **0022 or later** before any future merge. Recommendation P1 keeps `0021` because it is the locked active product phase and will merge first.

## Remaining P1 gates

Before production enrichment:

1. complete the global 8-shard aggregate coverage audit
2. complete the India-language cohort aggregate audit
3. run fingerprint-bound read-only materialization analysis on the final P1 implementation
4. quantify unresolved labels and total relationship volume
5. create immutable analysis evidence and an explicit operator write-request gate
6. recapture production catalogue projection and require an exact fingerprint match
7. only then apply migration `0021` and bounded/resumable metadata writes
8. verify normalized row counts, referential integrity, provenance, and idempotency
9. rerun Catalogue Quality V1 and keep S0/S1 at zero
10. document final production recommendation-ready coverage and unresolved backlog

## P1 exit rule

Phase P2/onboarding logic must not begin merely because the schema exists. P1 exits only after a meaningful, production-verified portion of the catalogue has safe recommendation metadata and the post-write quality gate remains clean.
