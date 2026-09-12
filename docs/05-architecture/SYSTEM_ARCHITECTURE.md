# System Architecture — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Architectural objective

Build Cinema and Series as a durable data platform first and a set of clients second. The platform must survive source/provider changes, support evidence-backed metadata, scale from a free early deployment to a large catalogue, and keep the canonical model independent from individual vendors.

# 1. Logical system

```text
                           EXTERNAL SOURCES
  +-----------+ +-----------+ +-----------+ +-----------+ +-----------+
  | Open data | | Official  | | Archives  | | Licensed  | | Platforms |
  +-----+-----+ +-----+-----+ +-----+-----+ +-----+-----+ +-----+-----+
        \             |             |             |             /
         \            |             |             |            /
          +------------v-------------v-------------v-----------+
          |             SOURCE ADAPTER / ACQUISITION            |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | SOURCE SNAPSHOTS / ACQUISITION LOG / SOURCE POLICY  |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | PARSING / NORMALIZATION / OBSERVATIONS              |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | IDENTITY RESOLUTION                                |
          | candidate matching -> link/create/review           |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | CLAIMS + PROVENANCE                                 |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | CANONICALIZATION / CONFLICT ENGINE                  |
          +--------------------------+--------------------------+
                                     |
                                     v
          +-----------------------------------------------------+
          | POSTGRESQL CANONICAL DOMAIN + HISTORY/AUDIT         |
          +------------+----------------------+-----------------+
                       |                      |
              +--------v---------+   +--------v---------+
              | Search Projection|   | Quality/Analytics|
              +--------+---------+   +--------+---------+
                       |                      |
                       +----------+-----------+
                                  |
                           +------v------+
                           | API / BFF   |
                           +------+------+
                                  |
            +---------------------+--------------------+
            |                     |                    |
     +------v------+       +------v------+      +------v------+
     | Android App |       | Web Product |      | Admin Studio|
     +-------------+       +-------------+      +-------------+
```

# 2. Architecture layers

## Acquisition layer
Responsibilities:
- source authentication/access;
- rate limiting;
- scheduling;
- source-specific request logic;
- raw/permitted snapshot capture;
- checksums;
- retries/idempotency;
- terms/policy kill switch.

An adapter cannot write canonical Works, People or Releases.

## Interpretation layer
Responsibilities:
- parse source records;
- normalize dates/languages/names/types;
- produce Observations;
- map provider fields to domain predicates;
- preserve source wording/context;
- reject malformed payloads.

AI extraction may assist only with evidence-linked outputs and never bypass validation.

## Identity layer
Responsibilities:
- candidate generation;
- deterministic/high-precision matching;
- external-ID reconciliation;
- Work/Person/Organization/Version/Release identity;
- merge/split review tasks.

## Evidence layer
Responsibilities:
- Claims;
- evidence locators;
- claim lineage;
- trust inputs;
- temporal state;
- source policy eligibility.

## Canonical domain layer
Responsibilities:
- current Work/Version/Release/Person/etc. projections;
- canonical decisions;
- durable CAS IDs;
- relationships;
- history/audit;
- transaction-level invariants.

## Projection layer
Responsibilities:
- search documents/indexes;
- read-optimized title/person pages;
- calendars;
- discovery rows;
- coverage metrics;
- admin dashboards.

All projections are rebuildable.

## API layer
Responsibilities:
- public/client read APIs;
- authenticated admin APIs;
- locale/territory-aware presentation;
- pagination;
- stable versioned contracts;
- authorization/rate limiting;
- no provider-specific leakage.

# 3. Application strategy

## Backend
Working choice: TypeScript service application organized as a modular monolith.

Reasons:
- shared domain transactions are complex;
- early team/scale does not justify network boundaries;
- easier local development/testing;
- modules can later be extracted behind existing contracts.

Python workers/tools may be used for:
- ETL/data analysis;
- source parsers where libraries are superior;
- offline matching experiments;
- quality/corpus benchmarking;
- ML/embedding experiments if later justified.

The domain contract, IDs and DB invariants remain shared/explicit; Python must not become a second conflicting canonical business-logic implementation.

## Web/admin
Working choice: Next.js + TypeScript, sharing API contracts/types where safe but not reaching directly into database internals from client UI.

## Android
Working choice: native Kotlin + Jetpack Compose.

The Android client consumes product APIs and maintains local read caches/favorites later; it is never the canonical movie database.

# 4. Database strategy

## PostgreSQL source of truth
PostgreSQL is authoritative for:
- canonical entities;
- external mappings;
- claims/provenance metadata;
- canonical decisions;
- release/lifecycle history;
- audit records;
- source registry operational state;
- asset rights metadata;
- review queues;
- quality state.

## Supabase role
Supabase is a managed PostgreSQL/adjacent-services candidate for early deployment, not an architectural dependency.

Rules:
- standard PostgreSQL schema/migrations;
- business logic remains portable;
- no essential identity/provenance design depends on proprietary-only feature;
- export/restore path tested;
- Supabase Auth/Storage/Realtime may be used later only through explicit ADRs.

## Raw object storage
Large permitted raw snapshots/media should not bloat relational tables.

Use object storage abstraction with DB metadata/hash/reference.

Provider policies may require reference-only/hash-only rather than raw storage.

Exact provider remains OPEN.

# 5. Data writes

## Public/product users
V1 public clients are primarily read-oriented. Later watchlists/ratings/user state are separate user-domain writes.

## Ingestion writes
Only pipeline modules create Observations/Claims. Canonical projections update through canonicalization services/transactions.

## Admin writes
Admin correction creates/edits evidence-backed Claims/decisions, never unsupported direct canonical fields.

## Merge/split writes
Performed through privileged identity service transaction/workflow with audit, redirect and reindex effects.

# 6. Transaction boundaries

Transactions should protect:
- new CAS entity + external mapping link;
- Claim + evidence metadata creation;
- CanonicalDecision + canonical projection update;
- merge redirect + impacted identities;
- asset rights/publication state;
- manual-review completion + resulting decision.

Long-running source acquisition/parsing remains asynchronous and outside DB transactions.

# 7. Jobs and asynchronous work

Required job classes:
- source polling/import;
- parser execution;
- identity candidate generation;
- canonicalization recalculation;
- search reindex;
- volatile-data expiry;
- coverage/quality scans;
- source-policy revalidation;
- asset processing;
- backup verification;
- validation corpus runs.

Exact queue/scheduler technology remains OPEN pending free-tier/deployment benchmarking. Domain jobs must be idempotent and technology-agnostic enough to migrate.

# 8. API surfaces

Logical APIs:

### Public catalogue
- Work details
- Series/Season/Episode
- Person
- Organization
- Search
- Release calendar
- relationships/franchises
- source/evidence summary

### Internal/admin
- source registry/status
- ingestion jobs
- raw snapshot/observation inspection subject to rights
- candidate entities
- identity merge/split
- conflicts
- canonical decisions
- release verification
- production lifecycle review
- asset rights
- quality queues
- audit logs

### User-state later
- watchlist/library
- ratings/reviews
- notifications

User state should not be mixed into canonical entertainment metadata tables.

# 9. Caching

Caching is optional optimization, not truth.

Candidates:
- HTTP/CDN caching for public immutable-ish responses;
- application cache for hot projections;
- Redis-like store only if benchmarks justify it.

Canonical invalidation events should be able to expire affected read/search caches.

Exact cache provider remains OPEN.

# 10. Search

Phase 1 implementation direction:
- normalized PostgreSQL search documents;
- FTS;
- pg_trgm;
- language/script-aware aliases.

Dedicated search service threshold must be benchmark-driven.

Search indexes can be deleted/rebuilt without loss of canonical data.

# 11. Event/change propagation

The modular monolith should emit internal domain events/outbox records for effects such as:
- WorkCreated
- ClaimAdded
- CanonicalValueChanged
- EntityMerged
- EntitySplit
- ReleaseChanged
- LifecycleChanged
- AssetRightsChanged
- SourceSuspended

Use transactional outbox or equivalent once asynchronous side effects are implemented so database commit and event publication cannot silently diverge.

Exact broker is not required initially.

# 12. Auditability

Privileged actions record:
- actor/service;
- action;
- affected CAS IDs;
- prior/new state references;
- evidence/decision;
- timestamp;
- request/job correlation ID.

Logs are not a substitute for business audit records.

# 13. Security zones

## Public zone
Read-only catalogue APIs with rate limiting and strict query limits.

## Authenticated user zone — later
Personal lists/settings.

## Admin/editor zone
Role-based access, stronger auth, audit, no public credentials.

## Ingestion zone
Source credentials isolated by adapter/least privilege; source payload treated as untrusted input.

## Database
No direct public database write path.

# 14. Resilience

### Source failure
Disable/degrade source adapter; canonical catalogue remains online.

### Search failure
Fallback to limited canonical DB search if feasible; entity detail APIs remain available.

### Job failure
Retry idempotently; dead-letter/review after threshold.

### Provider contract ends
Kill adapter, honor retention/delete terms, recanonicalize affected data if needed; CAS IDs remain stable.

### Object storage loss
Restore from backups where permitted; raw snapshots missing must be marked, not fabricated.

# 15. Backup/recovery direction

Before production launch define:
- automated PostgreSQL backups;
- point-in-time recovery where tier permits;
- object-storage versioning/backup for permitted data;
- restore drills;
- RPO/RTO by maturity stage;
- encrypted secret backup;
- schema migration rollback/forward-fix policy.

Backups are incomplete unless restore is tested.

# 16. Observability

Required signals:
- API latency/error rate;
- DB performance/connections;
- job queue depth/failures;
- adapter success/rate limits/schema drift;
- new Claims/day;
- unresolved identity/conflict queue;
- search latency/zero-result rate;
- stale availability/release monitors;
- source terms-review due dates;
- rights/takedown alerts.

Exact vendor remains OPEN; prefer low-cost/open standards initially.

# 17. Deployment stages

### Research/prototype
Local/ephemeral only; no production data obligations.

### Alpha
One managed Postgres deployment, monolith API, workers, admin, limited source adapters, small corpus.

### Beta
Broader ingestion, public web/Android read clients, production observability/backups, stronger source SLAs.

### Scale
Only measured bottlenecks justify extraction of search, ingestion, identity, analytics or availability services.

# 18. Scaling boundaries

Likely future extraction candidates:
- high-volume source ingestion;
- search;
- image processing;
- availability polling;
- analytics/warehouse;
- recommendation engine.

Canonical identity/provenance semantics must remain consistent across any extracted services.

# 19. Cost philosophy

User requirement is to avoid unnecessary spend during build. Architecture should support:
- open data and free development tiers;
- local containers;
- scheduled rather than always-on workers where safe;
- no premature Kafka/Elasticsearch/Kubernetes;
- storage of only permitted/valuable raw content;
- cost budgets/alerts before scale.

Free-tier constraints must never justify corrupt data modeling.

# 20. Implementation gate

No production repository code/migrations are authorized by this document.

Before implementation:
- ADR package accepted;
- schema/domain model survives validation corpus;
- queue/storage/auth choices needed for first milestone resolved;
- QA acceptance criteria defined;
- V1 contract FROZEN.
