# ADR-007 — Primary Service and Client Technology Directions

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
The product needs a public API/backend, web/admin interface, Android-first mobile client, and data/ETL tooling. Technology should be widely supported, low-cost to start, and compatible with the domain model.

## Decision
Working stack:
- primary domain/API services: **TypeScript**;
- web and admin: **Next.js + TypeScript**;
- Android: **Kotlin + Jetpack Compose**;
- data engineering/research/batch analysis: **Python** where advantageous;
- API contracts: explicit/versioned, with **OpenAPI or equivalent generated contract** before client implementation;
- local/dependency environment: **Docker/containers where practical**;
- CI: **GitHub Actions**.

## Rules
- Python workers cannot maintain a competing version of canonical business truth;
- web UI does not become the business-logic layer;
- Android does not query provider APIs as canonical data sources;
- shared API contracts are generated/validated rather than manually drifting between clients;
- exact framework/library versions are selected at implementation start and pinned, not frozen in this research ADR.

## Rationale
These choices balance ecosystem maturity, product fit, development velocity, native Android quality, data-engineering capability and portability.

## Revisit triggers
- benchmark or platform requirement invalidates a choice;
- team constraints materially change;
- framework maintenance/support status changes before implementation.
