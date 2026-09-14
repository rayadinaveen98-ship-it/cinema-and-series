# ADR-015 — Backup, Recovery Targets & Restore Drills

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
Cinema and Series will contain data that is easy to reacquire (some external source observations) and data that is expensive or impossible to reconstruct exactly (manual adjudications, merge/split history, rights decisions, historical evidence, audit context).

A serious database product cannot treat provider-managed daily backup as the complete recovery plan. Supabase documents that:
- paid projects receive daily database backups;
- PITR provides recovery to a chosen point with seconds-level selection and is intended for lower RPO;
- current published PITR guidance cites a worst-case RPO around two minutes;
- logical backups can be created with `supabase db dump`/`pg_dump`;
- database backups do not include Storage object bytes;
- object deletion in Supabase Storage is not recoverable through DB restore.

Sources reviewed:
- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery
- https://supabase.com/docs/guides/deployment/going-into-prod
- https://supabase.com/docs/guides/storage/s3/compatibility

## Decision
Cinema and Series uses a **layered recovery strategy** with separate protection for:
1. PostgreSQL authoritative data;
2. object-storage bytes;
3. repository/configuration/migration state;
4. external-provider reacquisition/replay capability.

## Recovery classes

### Tier A — Irreplaceable / authoritative
Examples:
- CAS canonical identities;
- Claims and CanonicalDecisions;
- manual adjudications/overrides;
- merge/split lineage;
- rights decisions;
- source-policy versions;
- audit records;
- human review state.

Target once public production begins:
- **RPO <= 5 minutes**;
- **RTO <= 4 hours** for restoration of core read/control capability under a normal single-region/provider recovery scenario.

The RPO target requires PITR or an equivalent continuous WAL-based recovery mechanism before public production carries meaningful live editorial/admin work.

### Tier B — Durable but replayable
Examples:
- source observations/parsed records where upstream evidence can be reacquired;
- search/outbox/job state with authoritative source elsewhere;
- some computed quality results.

Target:
- RPO <= 24 hours where not already covered by database PITR;
- deterministic replay/rebuild mechanisms documented.

### Tier C — Rebuildable projections
Examples:
- search documents/index;
- derived caches;
- thumbnails/derivatives;
- analytics aggregates.

No independent fine-grained backup required if rebuild is tested and source data is protected.

## Database production policy
Before public production launch:
1. run on a paid/production-capable database plan with managed backups;
2. enable PITR or an equivalent mechanism meeting Tier A RPO;
3. retain at least 7 days of point-in-time recovery for early V1, unless a later risk review increases it;
4. create an **independent encrypted logical backup/export at least daily** using `pg_dump`/Supabase CLI, stored outside the primary database project/account failure domain where practical;
5. preserve migrations in Git independently of all database backups.

The independent logical backup exists for portability/provider-account/project-loss scenarios, not as a substitute for PITR.

## Pre-production / research environments
Before production:
- no expensive PITR requirement;
- database may be rebuildable from migrations/fixtures/corpus;
- if valuable manual research data is entered, run regular logical dumps;
- never claim production recovery guarantees for a free/dev environment.

## Object-storage recovery
Object bytes follow ADR-014 and are backed up separately because DB backup contains only storage metadata.

### Evidence-critical / rights-approved originals
At production maturity:
- mirror/export at least daily to a second storage failure domain when retention rights permit;
- preserve checksum and original key mapping;
- use immutable/content-addressed object behavior;
- backup deletion must honor rights/takedown requirements.

### Rebuildable derivatives
May be regenerated instead of mirrored.

### Objects not legally retainable
No backup is created beyond the permitted retention mode. Legal/source policy overrides convenience.

## Backup encryption / access
- backups encrypted at rest and during transfer;
- backup credentials separate from ordinary app clients;
- least-privilege access;
- backup locations/secrets never committed to Git;
- access to backups is auditable where platform support permits.

## Restore drills
Backups are not considered valid until restoration is tested.

### Before first public production launch
Perform a full recovery rehearsal that proves:
- schema restored;
- canonical entities/claims/decisions restored;
- auth/RLS migrations reproducible;
- queue/outbox can resume safely;
- search can rebuild;
- object references can be validated/restored;
- application/API can run against restored data.

### After launch
- **quarterly** restore drill minimum during V1;
- additionally after major backup architecture change;
- record actual RPO/RTO achieved;
- file issues for missed targets.

A restore drill should restore into an isolated environment/new project, not casually overwrite live production.

## Recovery runbook minimum
The operations documentation must include:
1. incident classification;
2. stop-writes/read-only decision;
3. chosen restore point;
4. DB restore procedure;
5. object restore/mirror procedure;
6. secrets/auth/config recreation;
7. migration/version verification;
8. integrity checks;
9. queue/outbox reconciliation;
10. search rebuild;
11. smoke tests;
12. reopen writes;
13. post-incident audit.

## Data integrity verification after restore
At minimum verify:
- row/entity count sanity by major domain;
- no broken CAS redirect/merge references;
- Claim -> Source/Evidence link integrity;
- CanonicalDecision references valid Claims;
- source snapshot/object checksum availability where required;
- migration version matches expected application release;
- pending outbox/queue work can be replayed idempotently.

## Project deletion / provider catastrophe
Provider-managed backup in the same project/account is not the sole disaster strategy. Independent logical exports and object mirrors must allow migration to a new Postgres/S3-compatible environment.

## Rejected approaches
- free-tier/no-backup as public production;
- daily backup alone for Tier A live editorial data;
- assuming object bytes are protected by database backup;
- backup without restore testing;
- search/cache backups instead of rebuilding them;
- storing only one copy of irreplaceable manual adjudication data.

## Cost note
PITR has material recurring cost. This decision intentionally treats that cost as a **production launch requirement**, not a research/development requirement. If the project is not yet ready to fund appropriate recovery, it remains pre-production rather than silently weakening the data-safety contract.
