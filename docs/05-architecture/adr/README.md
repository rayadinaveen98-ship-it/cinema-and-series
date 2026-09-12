# Architecture Decision Records

**Milestone: Research Foundation v0.1**

ADRs preserve why important architecture decisions were made. Accepted decisions may only be changed through a superseding ADR.

## Accepted / working toward lock

1. `ADR-001-postgresql-canonical-store.md` — PostgreSQL is the canonical authoritative datastore.
2. `ADR-002-modular-monolith.md` — modular monolith + independent workers, not premature microservices.
3. `ADR-003-ingestion-through-claims.md` — source adapters cannot write canonical facts directly.
4. `ADR-004-canonical-projections.md` — clients read canonical projections backed by Claims/history.
5. `ADR-005-search-is-rebuildable-projection.md` — search is derived/rebuildable.
6. `ADR-006-postgres-first-supabase-managed.md` — Supabase may host early Postgres but cannot become a non-portable dependency.
7. `ADR-007-client-and-service-stack.md` — TypeScript services/web, Kotlin Compose Android, Python data tooling.

## OPEN decisions before implementation milestone

The following are intentionally **not** guessed yet:

- exact TypeScript API framework;
- job queue/scheduler technology;
- object-storage provider;
- authentication provider/design for public users and admins;
- caching provider/need;
- observability vendor;
- exact deployment topology;
- migration tooling;
- secret-management implementation;
- backup/PITR tier and RPO/RTO;
- dedicated search engine threshold/provider;
- whether Supabase Auth/Storage/Realtime/Edge Functions are used;
- exact internal ID encoding (UUIDv7/ULID/etc.);
- partitioning strategy for Claims/Snapshots/Availability;
- AI/embedding provider or local model, if any.

Each OPEN choice must be resolved through benchmark/requirement-driven ADR before the implementation phase that needs it. Coding must not silently choose one.

## ADR template

```text
# ADR-NNN — Title
Status:
Date:

## Context
## Decision
## Rationale
## Consequences
## Rejected alternatives
## Revisit trigger
```

## Supersession rule

If a decision changes:
- create a new ADR;
- mark prior ADR `SUPERSEDED BY ADR-NNN`;
- explain migration/compatibility effects;
- update `START_HERE.md`/architecture docs if the reading contract changes.

Do not rewrite history to make the old decision appear never to have existed.
