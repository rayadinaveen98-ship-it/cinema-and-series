# ADR-011 — NestJS + Fastify for the V1 API Layer

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
Cinema and Series needs a TypeScript API layer that can support:
- a modular-monolith domain structure;
- public read APIs;
- privileged Control Room commands;
- OpenAPI contracts;
- authentication/authorization guards;
- validation;
- background-worker shared domain services without coupling domain logic to HTTP controllers;
- future extraction of selected modules if scale requires it.

The framework should reduce architectural drift without forcing microservices.

NestJS provides explicit modules, dependency injection, guards/interceptors and a dedicated OpenAPI module. It supports Fastify through the official `FastifyAdapter`.

Sources reviewed:
- https://docs.nestjs.com/openapi/introduction
- https://docs.nestjs.com/techniques/performance

## Decision
V1 uses **NestJS** for the primary TypeScript HTTP/API application with the official **Fastify adapter**.

OpenAPI is generated/maintained through the NestJS OpenAPI tooling and becomes a versioned contract artifact in CI.

## Why NestJS fits this project
The project already has explicit bounded modules:
- catalog/works;
- people/credits;
- organizations;
- releases;
- lifecycle;
- source/evidence/claims;
- identity;
- canonicalization;
- assets;
- search;
- quality;
- admin/audit.

Nest modules map naturally to these boundaries while still deploying as one modular application.

## Domain isolation rule
NestJS is an **application/framework shell**, not the domain model.

Core domain rules must not depend on:
- HTTP request objects;
- Fastify-specific APIs;
- decorators as the only source of domain invariants;
- Supabase client behavior.

Domain services should be callable by HTTP controllers, workers and tests.

## Fastify
Use Nest's `FastifyAdapter` rather than default Express for the V1 API unless a required incompatible middleware forces a documented exception.

Reasons:
- official Nest support;
- lower HTTP overhead;
- strong JSON/API fit;
- preserves Nest framework abstractions.

Raw performance is not the primary architectural reason; database/search work will dominate many requests. Fastify is selected because it is a supported efficient default for this API-heavy product.

## API surfaces
Conceptually separate contracts even if hosted in one process initially:

### Public/consumer API
Read-oriented endpoints for canonical Works, people, releases, search and provenance summaries.

### Control Room API
Privileged commands and deep evidence/review views.

### Internal worker/domain API
Prefer direct module/service access or queue messages rather than exposing every worker operation as public HTTP.

## OpenAPI requirements
Once implementation begins:
- API versioning is explicit;
- OpenAPI document generated in CI;
- breaking contract changes require review;
- clients should be generated/validated from the contract where practical;
- provider-specific external schemas must not leak into public contracts.

## Input/output validation
Transport DTO validation is mandatory. Domain commands perform their own invariant validation as well.

No API endpoint may trust:
- provider IDs as canonical IDs;
- arbitrary source URLs as approved sources;
- user-supplied canonical confidence scores;
- client-selected privileged actor IDs.

## Error model
Use a stable application error taxonomy rather than exposing raw PostgreSQL/provider errors.

Examples:
- validation error;
- not found;
- conflict;
- review required;
- forbidden;
- source policy violation;
- stale version/concurrency conflict;
- transient dependency failure.

## Rejected alternatives for V1
### Next.js route handlers as the primary backend
Rejected: useful for web BFF/page needs but too easy to blur the durable domain/worker/API boundaries for this data platform.

### Bare Fastify
Not selected despite simplicity: we value explicit module/DI/guard/OpenAPI structure for a large long-lived domain.

### Microservice-per-domain Nest deployment
Rejected under ADR-002. Nest modules remain in a modular monolith until extraction is justified.

## Consequences
### Positive
- explicit module boundaries;
- strong testing/DI story;
- first-party OpenAPI support;
- straightforward RBAC guards/interceptors;
- Fastify adapter gives efficient HTTP layer;
- easier onboarding for future developers/agents.

### Negative
- framework ceremony/metadata;
- care required to prevent domain code becoming Nest-specific;
- worker packages should not be forced to bootstrap a full HTTP app unnecessarily.
