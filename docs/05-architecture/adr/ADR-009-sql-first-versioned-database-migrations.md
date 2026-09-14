# ADR-009 — SQL-First Versioned Database Migrations

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
The Cinema and Series database is the authoritative product asset. Schema drift between local, staging and production environments would undermine provenance, reproducibility and recovery.

Supabase's current deployment guidance explicitly warns that direct remote Dashboard/SQL schema edits bypass migration history and can cause migration synchronization problems. It recommends versioned migration files and local reset/testing before pushing changes.

Source reviewed:
- https://supabase.com/docs/guides/deployment/database-migrations

## Decision
All authoritative PostgreSQL schema changes are managed through **version-controlled SQL migrations** stored in the repository.

The Supabase CLI is the initial migration workflow because it is compatible with local Postgres/Supabase development while producing ordinary SQL migration files.

Supabase is tooling/hosting; **SQL remains the source of truth**.

## Mandatory rules
1. Production/staging schema changes do not occur manually in the remote Dashboard.
2. Every table, type, function, trigger, RLS policy, extension enablement and index change is represented in migration history.
3. A shared/applied migration is not silently rewritten; corrections use a new migration.
4. Migrations must be reviewable as SQL in Git.
5. Local reset from zero must reproduce the expected schema.
6. CI must apply the full migration chain against a clean database before merge once implementation begins.
7. Destructive migrations require explicit data-migration/rollback/recovery notes.
8. Provider-specific generated schema must not become an unreviewed source of truth.

## Workflow
Expected development flow:
1. create migration (`supabase migration new ...`) or generate a local diff when appropriate;
2. edit/review SQL;
3. run `supabase db reset` locally;
4. run schema/data/contract tests;
5. review migration in PR/commit;
6. apply to staging;
7. verify;
8. back up/confirm recovery preconditions for risky changes;
9. apply to production using controlled deployment.

`supabase db diff` may help capture local Dashboard experiments, but remote production editing remains prohibited.

## Migration categories
Every migration should be mentally classified as:
- additive/safe;
- backfill/data transition;
- behavioral (functions/triggers/RLS);
- index/performance;
- destructive/contract-changing.

Destructive/contract-changing changes require a documented expand-migrate-contract strategy where practical.

## Application ORM/query tooling
A query builder/ORM may be used later for developer ergonomics, but it does **not** own the database schema lifecycle unless a future ADR explicitly replaces this decision.

The canonical schema remains understandable as PostgreSQL SQL.

## Extensions
Required extensions (for example `pg_trgm`, `pgmq`, possibly others) are enabled through migrations and are documented dependencies.

## RLS and permissions
RLS policies, grants, functions used by auth hooks, service roles and queue authorization are schema behavior and must be migration-controlled.

## Seeds / fixtures
Development/test seed data is separate from production migrations unless it represents required reference vocabulary.

Reference vocabularies such as languages/scripts/territory code systems may use deterministic versioned seed migrations or dedicated reference-data loading with checksums, depending on final physical design.

## Rejected alternatives
- remote Dashboard as schema source of truth;
- auto-sync ORM schema changes directly to production;
- hand-maintained production SQL with no repository history;
- migration state stored only in a developer machine.

## Consequences
This adds discipline and review overhead, but gives us reproducibility, auditability, CI verification and hosting portability—the correct trade for a long-lived data platform.
