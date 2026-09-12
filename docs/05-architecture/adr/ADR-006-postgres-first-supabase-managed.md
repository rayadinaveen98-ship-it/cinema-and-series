# ADR-006 — Postgres-First Architecture; Supabase as Initial Managed Candidate

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
The project benefits from a low-cost managed Postgres platform during early stages, but previous attempts have shown the danger of designing the product around a vendor rather than the domain.

## Decision
Treat **Supabase as the preferred initial managed PostgreSQL deployment candidate**, while keeping Cinema and Series architecturally Postgres-first and portable.

## Rules
- schema defined by standard PostgreSQL migrations;
- CAS IDs/business rules do not depend on Supabase-specific generated identity;
- essential domain logic lives in application/database standards-compatible code;
- proprietary features require separate ADR before becoming critical dependencies;
- export/restore/migration path must be tested before production launch;
- Auth, Storage, Realtime and Edge Functions are optional capabilities, not automatically selected.

## Rationale
- low initial cost/developer speed;
- managed backups/auth/storage options can be useful later;
- preserves ability to move to another Postgres provider/self-hosting.

## Consequences
- vendor convenience cannot bypass architecture rules;
- free-tier limits may shape test scale but must not distort schema;
- deployment/provider choice can change without changing canonical IDs/domain meaning.
