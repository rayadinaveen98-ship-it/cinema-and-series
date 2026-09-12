# ADR-005 — Search Is a Rebuildable Projection, Not Source of Truth

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
Search requires denormalized multilingual documents and may later require a dedicated search engine. Making search storage authoritative would couple identity/data semantics to retrieval technology.

## Decision
Search indexes/documents are generated from canonical Cinema and Series data and can be deleted/rebuilt.

Initial implementation direction: PostgreSQL FTS + `pg_trgm` + normalized search-document projection. Introduce a dedicated search service only if benchmark evidence proves necessary.

## Rationale
- technology portability;
- avoids premature operational complexity;
- canonical corrections/merges can reindex cleanly;
- search ranking experiments cannot corrupt data.

## Consequences
- canonical change events trigger index updates;
- search has separate quality benchmarks;
- consumer-search fuzzy thresholds must never become identity auto-merge thresholds.

## Rejected alternative
Elasticsearch/OpenSearch/other search engine as canonical entertainment store.
