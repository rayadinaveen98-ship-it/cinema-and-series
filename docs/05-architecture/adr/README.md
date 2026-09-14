# Architecture Decision Records

**Milestone: Research Foundation v0.1**

ADRs preserve why important architecture decisions were made. Accepted decisions may only be changed through a superseding ADR.

## Accepted / LOCKED for V1

1. `ADR-001-postgresql-canonical-store.md` — PostgreSQL is the canonical authoritative datastore.
2. `ADR-002-modular-monolith.md` — modular monolith + independent workers, not premature microservices.
3. `ADR-003-ingestion-through-claims.md` — source adapters cannot write canonical facts directly.
4. `ADR-004-canonical-projections.md` — clients read canonical projections backed by Claims/history.
5. `ADR-005-search-is-rebuildable-projection.md` — search is derived/rebuildable.
6. `ADR-006-postgres-first-supabase-managed.md` — Supabase may host early Postgres but cannot become a non-portable dependency.
7. `ADR-007-client-and-service-stack.md` — TypeScript services/web, Kotlin Compose Android, Python data tooling.
8. `ADR-008-postgres-native-queues-and-scheduling.md` — pgmq/Supabase Queues for durable jobs; pg_cron for scheduling.
9. `ADR-009-sql-first-versioned-database-migrations.md` — authoritative schema changes are version-controlled SQL migrations.
10. `ADR-010-control-room-auth-rbac.md` — Supabase Auth + custom claims/RLS + domain permissions for Control Room.
11. `ADR-011-nestjs-fastify-api-framework.md` — NestJS + Fastify is the V1 TypeScript API shell; OpenAPI is the contract.
12. `ADR-012-transactional-outbox-domain-events.md` — canonical state changes emit downstream events through a transactional outbox.
13. `ADR-013-canonical-id-format-uuidv7.md` — durable CAS entity IDs use provider-independent RFC 9562 UUIDv7.
14. `ADR-014-s3-compatible-object-storage.md` — object bytes live behind an S3-compatible ObjectStore boundary; Supabase Storage may be the first implementation.
15. `ADR-015-backup-recovery-and-restore-drills.md` — layered DB/object recovery with production RPO/RTO targets and mandatory restore drills.
16. `ADR-016-deterministic-versioned-canonicalization-engine.md` — canonicalization is deterministic, versioned, explainable typed rules; AI is never canonical authority.

## Significant OPEN decisions before implementation milestone

The remaining architecture choices are intentionally **not** guessed:

- public API authentication/rate-limit policy;
- cache strategy and threshold for introducing a dedicated cache;
- observability/logging/tracing stack;
- exact deployment topology for API/web/workers;
- secret-management implementation;
- dedicated search-engine escalation threshold/provider;
- physical partition/archive thresholds for Claims/Snapshots/Audit;
- protected-action dual-approval policy;
- exact production source adapter set and provider/licensing choices.

These are tracked in `docs/10-execution/OPEN_DECISIONS_REGISTER.md`.

Each OPEN choice must be resolved through benchmark/requirement-driven ADR or controlling specification before the implementation phase that needs it. Coding must not silently choose one.

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
