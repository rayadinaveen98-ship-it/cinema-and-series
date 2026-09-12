# Database Architecture — Pre-Implementation Design Principles

**Status: WORKING — no migrations authorized**  
**Research date: 2026-09-12**

## Purpose

Translate the conceptual domain model into PostgreSQL implementation principles without prematurely writing production schema/migrations.

## Core database zones

Recommended logical schemas/namespaces (final naming OPEN):

### `catalog`
- Works
- Versions
- Seasons/Episode membership
- Names
- Languages/Scripts/Territories
- Organizations/People
- Credits
- relationships/franchises
- certifications

### `evidence`
- Sources
- source policy versions
- snapshots/references
- observations
- Claims
- ClaimLinks
- CanonicalDecisions

### `release`
- ReleaseEvents
- AvailabilityOffers
- production/lifecycle events

### `media`
- Assets
- rights records
- asset relationships

### `identity`
- ExternalIdentifiers
- redirects/tombstones
- merge/split operations
- match candidates/review decisions

### `quality`
- QualityIssues
- Coverage metrics/snapshots
- validation-run results

### `admin`
- ReviewTasks
- ManualDecisions
- AuditEvents

### `projection`
- read-optimized/current canonical projections
- search documents/materialized helpers

Physical schema boundaries may be simplified, but logical ownership should remain clear.

## ID policy

All canonical entities use application-independent CAS internal IDs.

Exact encoding remains OPEN. Requirements:
- globally unique without provider dependency;
- safe for distributed creation later;
- immutable;
- sortable/time-friendly is desirable but not mandatory;
- opaque to clients semantically;
- retired/merged IDs never reused.

Human-friendly prefixed IDs may be API display forms while DB stores native UUID/binary value; decide through later ADR.

## Referential integrity

Prefer real foreign keys for canonical relational entities where scale permits.

Do not replace integrity with application-only conventions simply to make imports easier.

Large evidence tables may use carefully designed polymorphic subject references only if validation proves generic Claim storage is viable; otherwise use domain-specific claim association tables with a common provenance core.

## Generic Claim warning

A pure EAV table for every fact risks:
- weak type constraints;
- difficult queries;
- poor performance;
- migration complexity.

Preferred direction:
- strongly typed domain tables/projections for canonical state;
- common Claim metadata/provenance core;
- typed claim-value families or domain claim tables where needed;
- JSONB only for bounded source/raw/extensible metadata.

Physical design will be prototyped against corpus before lock.

## Temporal data

Use explicit timestamps/date precision rather than hiding temporal semantics.

For partial historical dates, consider structured fields:
- year;
- month nullable;
- day nullable;
- precision enum;
- circa/range metadata.

Do not fake SQL DATE precision with January 1 placeholders.

## Soft deletion / tombstones

Canonical identities should rarely be hard-deleted.

Use status/tombstone/redirect for:
- merged duplicate;
- invalid source-created entity;
- deprecated external mapping;
- removed public visibility.

Hard deletion may still be required for privacy/legal/security/user-data cases, governed separately.

## History

Important state change is append-only/audited where practical:
- Claims immutable except administrative metadata/status transitions;
- CanonicalDecision immutable/superseding;
- Merge/split operations immutable;
- lifecycle/release histories preserved;
- source snapshots immutable subject to retention/legal deletion.

## Uniqueness constraints

Likely constraints:
- CAS IDs unique;
- external ID unique per namespace/context unless provider semantics require many-to-one history;
- source record mappings unique per source namespace;
- one active redirect target per retired CAS ID;
- no active Version without Work;
- Episode membership requires Series;
- rights-approved Asset requires rights-basis fields;
- Claim must point to eligible source/evidence representation.

Exact constraints follow schema prototype.

## Indexing strategy

Initial indexes likely include:
- CAS primary IDs;
- external namespace + ID;
- WorkKind/status;
- normalized Name forms;
- trigram indexes for search aliases;
- ReleaseEvent territory/date/status;
- production current projection;
- Claim subject/predicate/context;
- source/snapshot timestamps;
- unresolved review/quality queues;
- AvailabilityOffer territory/provider/verified-at.

Do not index every field preemptively; use benchmark/query plans.

## Partitioning

No premature partitioning.

Candidates if scale proves necessary:
- SourceSnapshots by source/time;
- Claims by hash/time/domain;
- AuditEvents by time;
- AvailabilityOffer observations by time/territory.

Partition only after measured table/query/retention patterns justify it.

## JSONB policy

Appropriate:
- permitted raw provider payload metadata;
- source-specific adapter attributes;
- low-value extensible technical fields;
- diagnostic/job metadata.

Not appropriate as replacement for:
- Works;
- Names;
- Credits;
- Releases;
- External IDs;
- Claims/provenance relationships;
- Organizations/People.

## Search storage

SearchDocument can be a table/materialized projection containing:
- entity ID/type;
- localized/normalized text variants;
- filter facets;
- search vectors.

It is regenerated from canonical state.

## Concurrency

Use DB constraints/transactions to protect:
- duplicate CAS entity creation during concurrent ingestion;
- external-ID linking;
- merge/split;
- canonical decision updates;
- review task claiming/completion.

Likely techniques:
- unique constraints + retry;
- row/advisory locking for identity operations;
- optimistic version column for editor workflows;
- transactional outbox for side effects.

Exact patterns require prototypes.

## Idempotency

Every acquisition/import/job should carry idempotency keys based on:
- source;
- source record/version;
- retrieval/snapshot hash;
- operation type.

Repeated job execution must not create duplicate Claims/events unnecessarily.

## Retention

Retention is source-policy dependent.

Categories:
- canonical domain: long-term;
- Claims/decisions: long-term where legally permitted;
- raw snapshots: source-contract/license dependent;
- volatile availability observations: retention policy based on value/cost/contract;
- job logs: bounded operational retention;
- audit logs: long-lived according to security/admin policy.

## Privacy

Canonical public film/person data and user-account data should be logically separated.

User data later requires:
- deletion/export workflows;
- authentication ownership;
- minimal PII;
- separate retention/privacy policy.

Do not mix personal watch history into entertainment-domain provenance tables.

## Backup requirements before production

- automated DB backup;
- restore test;
- schema + seed/reference vocabulary reproducible from Git;
- claims/audit included;
- permitted object storage backup/versioning;
- recovery procedure documented;
- provider contract deletion obligations compatible with backups.

## Prototype requirements before schema lock

Create disposable test schema only after explicit validation authorization to benchmark:
- 1,000-case validation corpus;
- millions-scale synthetic Work/Name rows;
- Claims volume amplification;
- identity candidate queries;
- release-calendar queries;
- multilingual search;
- merge/split transaction;
- canonical projection rebuild;
- volatile availability cleanup.

Results decide physical schema, not aesthetic preference.

## Migration philosophy

Once implementation begins:
- migrations version-controlled;
- forward-only preferred for production data transformations, with tested rollback where safe;
- destructive migrations require backup/verification;
- data backfills resumable/idempotent;
- schema version compatible with worker/API deployments during rollout.

## Gate

This document does not authorize creating Supabase tables yet. Physical schema remains WORKING until corpus + performance prototypes validate the conceptual model and V1 is frozen.
