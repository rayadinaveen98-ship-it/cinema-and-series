# ADR-001 — PostgreSQL as Canonical Data Store

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
Cinema and Series requires relational integrity, complex identity/relationship queries, provenance/history, transactions, multilingual text, JSON for provider payload metadata, and strong portability.

## Decision
Use **PostgreSQL** as the authoritative canonical relational datastore.

## Rationale
- mature ACID transactions;
- strong relational constraints and indexing;
- recursive/graph-like relationship querying where needed;
- JSONB for bounded extensibility without making JSON the domain model;
- full-text + trigram capabilities for initial search;
- broad managed/self-hosted portability;
- strong ecosystem/tooling;
- avoids vendor-specific NoSQL schema compromise.

## Consequences
- domain schema/migrations become a core asset;
- relational modeling discipline required;
- large append-only claims/history may later need partitioning/archival based on measured volume;
- dedicated search/analytics stores can be added only as rebuildable projections.

## Rejected alternatives
- Firebase/Firestore as canonical DB: weak fit for relational provenance/identity model and creates vendor/data-model coupling.
- Provider API as database: violates source independence.
- Elasticsearch/OpenSearch as source of truth: search engine is not appropriate canonical transactional store.
- Flat JSON/data lake only: poor integrity/transaction semantics for canonical domain.

## Revisit trigger
Only if validation/scale proves an essential workload fundamentally unsuitable for Postgres; even then replacement requires migration ADR and preservation of canonical semantics.
