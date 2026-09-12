# ADR-004 — Claims/History Are Authoritative Evidence; Clients Read Canonical Projections

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
Dynamically resolving every source Claim on every API read would be expensive and complicated, while writing only final values would destroy evidence/history.

## Decision
Maintain two complementary layers:

1. **Evidence/history layer:** Claims, SourceSnapshots, CanonicalDecisions, audit history.
2. **Canonical projection layer:** current read-optimized representations selected/derived by versioned rules.

Clients primarily read canonical projections. Evidence UI can trace projections back to decisions/Claims.

## Rationale
- fast client reads;
- full auditability;
- deterministic rebuilds;
- conflict/supersession history retained;
- supports source-policy and rule changes.

## Consequences
- projections require invalidation/recalculation;
- domain events/outbox should trigger dependent search/cache updates;
- projection tables are not independent sources of truth.

## Invariant
Deleting/rebuilding a projection must be possible from retained authoritative evidence/domain state, subject to source-retention policy.
