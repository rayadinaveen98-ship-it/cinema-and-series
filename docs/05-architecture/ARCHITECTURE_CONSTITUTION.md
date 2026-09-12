# Architecture Constitution

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Architectural objective

Build a durable cinema/series data platform whose canonical database, provenance model, and identity system survive provider changes, source outages, product expansion, and future scale.

## Working system shape

```text
Sources
  -> Acquisition adapters/workers
  -> Immutable raw source snapshots
  -> Parsing / extraction
  -> Normalization
  -> Identity resolution
  -> Claims / provenance store
  -> Canonicalization / reconciliation
  -> Canonical PostgreSQL model
  -> Search/index projection
  -> API layer
  -> Admin / Web / Android
```

## Core technology direction

### Authoritative datastore
**PostgreSQL** is the working choice for the canonical relational data platform.

### Managed hosting
**Supabase** is a preferred initial managed PostgreSQL platform, but architecture must remain Postgres-first rather than Supabase-dependent.

### Backend/API
**TypeScript** is the working choice for primary API/domain services.

### Data/ETL tooling
**Python** is the working choice for source ingestion, parsing, reconciliation experiments, data-quality analysis, and batch processing where its ecosystem is advantageous.

### Web
**Next.js + TypeScript** is the working choice for web and internal admin surfaces.

### Android
**Kotlin + Jetpack Compose** is the working native Android direction.

### Search
Begin with PostgreSQL capabilities (`FTS`, `pg_trgm`, normalized search documents) where sufficient. A dedicated search service may be introduced behind an abstraction once requirements/scale justify it.

### Local development / CI
Docker-based local dependencies where practical, version-controlled migrations, GitHub Actions for CI, and deterministic test fixtures.

These are WORKING decisions until the architecture research is complete and ADRs are written.

## Service strategy

Start with a **modular monolith plus independent asynchronous workers**, not a premature microservice mesh.

Expected domain modules include:

- catalog/titles
- people
- companies
- credits
- localization
- releases
- production lifecycle
- sources
- raw snapshots
- claims/provenance
- identity resolution
- canonicalization
- assets
- search
- quality
- admin/audit
- user-facing API

Boundaries must be strong enough that high-load domains can later be extracted without redesigning the data meaning.

## Canonical database rule

The canonical relational model is authoritative. Search indices, caches, analytics stores, and UI projections are derivatives and must be rebuildable.

## Raw-data preservation

Source acquisition must retain immutable or append-only snapshots/observations sufficient to:

- audit what was seen;
- rerun newer parsers;
- explain canonical changes;
- detect source drift;
- reproduce data-quality incidents where legally and technically permitted.

Each snapshot should carry source identity, retrieval time, request/source metadata, checksum, parser version linkage, and payload/object reference as applicable.

## Ingestion isolation

No source adapter may write canonical title/person/release values directly.

Expected flow:

`adapter -> raw snapshot -> parser -> normalized candidate/claim -> identity resolution -> canonicalization -> canonical projection`

## Asynchronous processing

Source polling, batch imports, identity matching, quality analysis, artwork processing, and reindexing should run as jobs/workers rather than blocking user requests.

The exact queue/scheduler technology remains OPEN.

## API principles

- versioned contracts;
- stable Cinema and Series IDs;
- pagination designed for large catalogues;
- explicit locale/territory context where relevant;
- source/provenance exposure appropriate to product/admin use;
- no leaking of provider-specific schema into public domain contracts;
- idempotent write operations for ingestion/admin workflows where practical.

## Reliability principles

- provider outages must degrade a source, not destroy core product availability;
- imports must be resumable/idempotent;
- migrations must be version-controlled and reversible where practical;
- source policy/licensing changes must be capable of disabling one adapter;
- canonical history/audit data must be backed up and restorable;
- search/indexes must be rebuildable from authoritative data.

## Security principles

- separate public read APIs from privileged admin/ingestion operations;
- least-privilege credentials per adapter/service;
- secrets never committed to Git;
- audit privileged canonical overrides;
- validate/escape untrusted source content;
- protect ingestion from malformed or hostile payloads;
- rate-limit externally exposed endpoints appropriately.

## Architecture decisions still OPEN

- exact PostgreSQL schema and partitioning strategy;
- queue/job technology;
- object storage layout;
- exact API framework;
- authentication/authorization implementation;
- search service threshold and future provider;
- caching layer and invalidation model;
- observability stack;
- deployment topology;
- backup/RPO/RTO targets;
- canonicalization rule engine implementation;
- AI/embedding usage boundaries;
- cost envelope by stage.

No OPEN item should be silently chosen during coding; resolve it through the architecture specification/ADR process first.
