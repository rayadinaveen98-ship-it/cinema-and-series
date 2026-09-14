# ADR-017 — Public API and Cache Policy

**Status: ACCEPTED**  
**Date: 2026-09-14**

## Context

Cinema and Series needs a consumer web/Android read API, but a public developer platform, API-key business and distributed cache are not V1 goals. Introducing Redis/API-key infrastructure before traffic exists adds failure modes without proving value.

## Decision

### Public consumer read API
V1 consumer catalogue read endpoints are:
- publicly readable without user login where content is public;
- rate-limited at the API/gateway boundary;
- protected against abuse/scraping bursts;
- versioned and documented through OpenAPI;
- read-only from the public client perspective.

### Privileged API
Control Room/admin/ingestion endpoints require authenticated, authorized sessions and domain permissions under ADR-010.

### Developer API
A third-party developer API/key product is deferred beyond V1. Public app endpoints are not a promise of unlimited third-party bulk access.

### Caching
V1 starts **without a dedicated external cache service**.

Use, in order:
1. PostgreSQL canonical/read projections and indexes;
2. HTTP caching headers / ETag / conditional requests where appropriate;
3. framework/CDN caching for safe public immutable/semi-static reads;
4. in-process short-lived cache only for non-critical repeat reads if useful.

A dedicated cache such as Redis may be introduced only after benchmark/production evidence shows a bottleneck that cannot be solved cleanly through PostgreSQL/index/query/projection/CDN improvements.

## Invalidation

The transactional outbox (ADR-012) publishes canonical changes. Any cached public representation must be either:
- keyed/versioned so stale data naturally expires;
- invalidated/revalidated from the outbox event; or
- bounded by a documented TTL appropriate to field volatility.

No cache becomes authoritative storage.

## Rate-limit classes

Initial policy classes:
- ordinary catalogue reads;
- search/autocomplete;
- expensive graph/filter queries;
- media/asset delivery handled separately by CDN/storage;
- authenticated Control Room actions.

Exact numeric limits are deployment configuration, not frozen semantics, and are tuned from observed traffic.

## Rationale

- keeps V1 free/low-cost;
- avoids premature Redis/vendor dependency;
- Postgres/search projections should handle early traffic;
- public consumer product remains accessible;
- abuse controls remain possible;
- future developer API can have separate contracts/keys/quotas.

## Revisit trigger

Introduce a dedicated cache or developer API only after measured latency/load/business requirements justify it, using a superseding ADR if architectural behavior changes.