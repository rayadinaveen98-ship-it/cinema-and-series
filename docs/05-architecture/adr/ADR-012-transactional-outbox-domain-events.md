# ADR-012 — Transactional Outbox for Domain Events

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
A canonical change can require several downstream reactions:
- rebuild a search projection;
- recalculate CAS Coverage/quality checks;
- update related entity projections;
- invalidate caches;
- surface Control Room activity/audit context;
- trigger later notifications or exports.

Cinema and Series cannot accept a failure mode where the canonical database commit succeeds but the application crashes before publishing the downstream event, leaving search or quality projections silently stale.

ADR-008 selects Postgres-native queues for durable background work, but canonical state and event publication still need an atomic boundary.

## Decision
V1 uses a **transactional outbox** for domain events emitted by authoritative state changes.

Within the same PostgreSQL transaction that commits the canonical/domain change, the application writes one or more immutable outbox records.

A dispatcher publishes pending outbox events to the appropriate durable queue(s) and marks publication state idempotently.

## Why an outbox even though pgmq is in Postgres
`pgmq` could technically be invoked in the same transaction, but an explicit outbox is retained because it:
- separates domain-event persistence from queue implementation;
- preserves event history/diagnostics;
- supports future broker migration;
- permits replay/reprojection without coupling business transactions to queue-specific functions;
- makes `what should have been emitted` auditable.

The dispatcher may optimize publication to pgmq, but domain services write the outbox contract, not raw broker calls.

## Event envelope
Each outbox record includes at minimum:
- `event_id` — stable CAS UUID;
- `event_type`;
- `event_schema_version`;
- `aggregate/entity_type`;
- `aggregate/entity_id`;
- `occurred_at`;
- `actor_id` / machine actor context where appropriate;
- `correlation_id`;
- `causation_id` nullable;
- compact payload or references to authoritative IDs;
- publish status/attempt metadata outside the immutable logical event body.

Do not copy large raw provider payloads into events.

## Event semantics
Events describe **facts about committed CAS domain changes**, not imperative provider-specific instructions.

Good:
- `work.canonical_projection_changed`
- `identity.merge_completed`
- `release_event.canonical_state_changed`
- `source.suspended`

Bad:
- `call_elasticsearch_now`
- `update_tmdb_row`

Consumers decide what projection/work follows from the event.

## Delivery semantics
Outbox-to-queue and queue-to-consumer behavior is **at least once at the business-effect level**.

Therefore:
- dispatcher publication is idempotent by `event_id`;
- queue consumer effects are idempotent by event/work key;
- projections upsert/replace deterministically;
- event replays must not duplicate canonical history.

## Ordering
Do not depend on one global event order.

When ordering matters for one aggregate/entity, consumers use:
- event occurrence/version metadata;
- current authoritative state;
- idempotent rebuild strategy.

Search/quality projections should prefer rebuilding from current canonical state over applying fragile incremental patches when practical.

## Audit vs outbox
Audit history and outbox events are related but not identical:
- **audit** explains who/what changed and why;
- **outbox** guarantees downstream systems learn that committed domain state changed.

Do not rely on application logs as either mechanism.

## Failure handling
If dispatch fails:
- canonical transaction remains valid because outbox record exists;
- dispatcher retries;
- backlog age/size is monitored;
- Control Room System Health exposes stale outbox state;
- repair can replay unpublished events.

If a consumer fails, the queue retry/dead-letter policy from ADR-008 applies.

## Retention
Published outbox records may be compacted/archived after a configured retention window once durable audit/event replay requirements are met. The authoritative audit and domain history remain governed separately.

## Rejected alternatives
- publish after commit with no durable outbox;
- synchronous calls to every projection during the write transaction;
- using application logs as a replay source;
- embedding queue-specific calls throughout domain services.

## Consequences
Adds an outbox table/dispatcher and monitoring, but removes a major class of dual-write inconsistency while preserving broker portability.
