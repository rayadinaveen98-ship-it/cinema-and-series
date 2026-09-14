# ADR-018 — Observability and Deployment Topology

**Status: ACCEPTED**  
**Date: 2026-09-14**

## Context

Cinema and Series has asynchronous ingestion, claims, canonicalization, search projection and quality jobs. These need separate operational visibility from the consumer web app. At the same time, V1 should avoid vendor-locked infrastructure and unnecessary always-on services during research/development.

## Decision

# 1. Logical deployment units

The system is separated into these deployable/runtime responsibilities:

1. `web-consumer` — Next.js public product.
2. `web-control-room` — Next.js authenticated operations UI; may share code/monorepo with consumer web but has separate route/auth/security boundary.
3. `api` — NestJS/Fastify application service exposing public and privileged APIs.
4. `worker` — asynchronous TypeScript worker runtime for queues, ingestion orchestration, projection rebuilds and quality jobs.
5. `python-data-tools` — offline/batch/research tooling, not part of latency-sensitive request path.
6. `postgres` — authoritative PostgreSQL/Supabase database.
7. `object-store` — S3-compatible raw snapshot/asset storage behind `ObjectStore` abstraction.

A web request process must never be the only place a durable background job can complete.

# 2. Environment separation

Minimum environments:
- local/developer;
- test/CI;
- production.

A separate staging environment becomes mandatory before public beta if production source adapters or migrations could affect irreversible data/rights behavior.

Production credentials/data are isolated from development.

# 3. Initial provider posture

- Supabase is the preferred initial managed PostgreSQL/Auth/Storage/Queue platform under existing portability ADRs.
- Next.js surfaces may use Vercel initially where useful.
- API/worker runtime provider is **replaceable** and must support ordinary Node.js execution, environment secrets, health checks and queue connectivity.

The exact Node hosting vendor is operational configuration, not domain architecture. Production launch requires a reliable worker runtime even if research/dev workers are run locally or manually.

# 4. Observability standard

V1 uses provider-neutral observability primitives:

## Structured logs
Every API request/job/source adapter run emits structured JSON logs with, where applicable:
- timestamp;
- environment;
- service;
- severity;
- trace/correlation ID;
- job ID;
- source ID;
- entity/claim/decision IDs where safe;
- rule/adapter version;
- duration;
- outcome/error class.

Never log secrets or protected raw payloads unnecessarily.

## Tracing
Use OpenTelemetry-compatible tracing boundaries for:
- inbound API request;
- queue enqueue/dequeue;
- source acquisition;
- parsing;
- identity proposal;
- canonicalization;
- projection/outbox processing.

A specific trace vendor/backend may be selected later without changing instrumentation semantics.

## Metrics
At minimum monitor:
- API latency/error rate;
- queue depth/age/retry/dead-letter counts;
- source fetch success/failure/freshness;
- claims created/rejected;
- conflicts/review queue size;
- canonicalization failures/recalculations;
- search indexing lag;
- validation/quality failures;
- object-storage failures;
- DB health/connection saturation;
- worker heartbeat/last successful run.

## Error tracking
A hosted error tracker may be used (e.g. Sentry or equivalent) if available within budget, but the application must not depend on that provider for correctness.

# 5. Health endpoints

API/worker deployments expose operational health checks suitable for orchestration/monitoring:
- process alive;
- database connectivity;
- queue connectivity where applicable;
- worker heartbeat;
- no deep external-source call inside ordinary liveness checks.

# 6. Alert classes

Critical alert examples:
- DB unavailable;
- queue processing stopped;
- canonicalization/outbox repeatedly failing;
- source terms/policy kill switch triggered;
- production migration failed;
- restore/PITR safety unavailable beyond allowed window;
- evidence/object storage integrity failure.

Warning examples:
- source stale;
- search projection lag;
- rising duplicate/conflict queue;
- adapter error-rate regression.

# 7. Cost posture

During research/pre-production:
- prefer free tiers/local tooling;
- no always-on premium observability requirement;
- correctness tests and structured logs still required.

Before public production:
- monitoring must meet operational acceptance criteria;
- reliable worker execution and backup targets are mandatory even if that introduces paid infrastructure.

## Consequences

- public UI hosting can evolve independently from workers;
- worker reliability is not coupled to serverless page traffic;
- observability remains portable;
- production operations have measurable source/data-pipeline health;
- exact hosting vendor can change without rewriting domain code.

## Revisit trigger

A superseding ADR is required only if the logical service boundaries or observability contract change materially, not for a normal provider migration.