# ADR-008 — Postgres-Native Durable Queues + Cron Scheduling

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
Cinema and Series needs durable asynchronous processing for source acquisition, parsing, identity resolution, canonicalization, quality analysis, search projection updates, artwork processing and maintenance jobs.

A premature external broker would increase operational cost and system count before workload evidence justifies it. At the same time, plain `cron + database table polling` without a queue contract would make retry/visibility/audit behavior ad hoc.

Supabase Queues is built on the open `pgmq` Postgres extension and provides durable messages, visibility timeouts, delivery guarantees and archival. Supabase Cron is built on `pg_cron` and can schedule SQL/functions or invoke an HTTP worker.

Sources reviewed:
- https://supabase.com/docs/guides/queues
- https://supabase.com/docs/guides/queues/pgmq
- https://supabase.com/docs/guides/cron

## Decision
V1 uses **Postgres-native durable queues based on `pgmq` / Supabase Queues** for production background work.

Recurring schedules use **`pg_cron` / Supabase Cron only as the scheduler**, normally to enqueue work or trigger a worker—not to execute long-running ingestion pipelines inside the cron job itself.

Workers may be TypeScript or Python depending on domain responsibility.

## Required abstraction
Application code must access the queue through a Cinema and Series queue interface rather than scattering raw `pgmq.*` SQL throughout business modules.

Conceptual operations:
- enqueue
- receive/read with visibility timeout
- acknowledge/delete
- retry / make visible again
- archive
- inspect age/retry/queue depth

This preserves a future migration path to another broker if measured scale or reliability requirements demand it.

## Message envelope
Every durable job message must carry, at minimum:
- message/job type;
- schema version;
- correlation/trace ID;
- idempotency key or deterministic work key where possible;
- source/entity/job reference;
- enqueued timestamp;
- attempt/retry context where not supplied by queue metadata;
- optional causation ID linking upstream event.

Large raw payloads should normally live in approved snapshot/object storage; queues carry references, not arbitrary megabyte documents.

## Handler contract
`Exactly once delivery within a visibility window` does **not** mean business side effects are magically exactly once.

Therefore every worker handler must be **idempotent** at the domain boundary.

Examples:
- ingesting the same SourceSnapshot twice must not duplicate Claims;
- replaying a canonicalization job must not emit duplicate canonical history events;
- reindexing a Work must replace/upsert its search projection rather than create another search identity.

## Queue classes — initial V1
Expected logical queues include:
- `source-acquisition`
- `source-parse`
- `identity-resolution`
- `canonicalization`
- `quality-analysis`
- `search-projection`
- `asset-processing`
- `maintenance`

Exact physical queue count may be consolidated early, but logical job type remains explicit.

## Retry / poison-message policy
Each job type defines:
- visibility timeout;
- maximum automatic attempts;
- retry delay/backoff policy;
- terminal failure classification;
- archival/dead-letter review behavior.

Repeatedly failing messages must become visible in Control Room system/job health instead of retrying forever.

## Scheduling policy
`pg_cron` is used for bounded scheduling such as:
- enqueue source polling jobs;
- stale-source checks;
- quality scans;
- search consistency checks;
- terms/source review reminders if implemented in-system;
- backup/export orchestration where appropriate.

Heavy jobs are executed by workers after enqueueing.

Supabase documentation currently recommends avoiding more than eight concurrent Cron jobs and keeping a Cron job under ten minutes. Our architecture avoids relying on Cron as a heavy worker for this reason.

## Rejected alternatives for V1
### External Redis/BullMQ as default
Rejected initially: adds another authoritative operational dependency without demonstrated need.

### Kafka/NATS/RabbitMQ as default
Rejected initially: excessive operational complexity for V1.

### Fire-and-forget serverless tasks
Rejected for critical ingestion/canonicalization: insufficient durable audit/retry contract.

### Cron-only pipelines
Rejected: scheduling is not durable workflow execution.

## Portability
Although Supabase exposes convenient queue management, the architectural dependency is **PostgreSQL + pgmq semantics**, not a Supabase-only consumer API.

If later migrated to managed SQS/Kafka/NATS/etc., domain job envelopes and idempotency contracts remain unchanged.

## Consequences
### Positive
- durable queue in same Postgres operational boundary;
- fewer infrastructure services initially;
- replay/archival fits provenance-heavy product;
- SQL visibility for Control Room metrics;
- strong local-development story.

### Negative
- queue load shares database resources;
- extremely high throughput may later justify external broker;
- workers still need polling/concurrency/backpressure discipline;
- queue portability requires maintaining our abstraction.

## Extraction threshold
A separate broker should be reconsidered when evidence shows sustained queue volume/latency materially interferes with canonical DB workload, or when fan-out/streaming semantics exceed pgmq's intended model.
