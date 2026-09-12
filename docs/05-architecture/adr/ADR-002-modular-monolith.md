# ADR-002 — Modular Monolith + Independent Workers

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
Cinema and Series has many logical domains but begins with a small team, tightly coupled canonical transactions, and no measured scale requiring service distribution.

## Decision
Build the initial backend as a **modular monolith with strong domain boundaries**, plus independently runnable asynchronous workers/jobs.

Initial modules include:
- catalog/work/version;
- people/organizations/credits;
- localization;
- releases/availability;
- production lifecycle;
- sources/snapshots;
- claims/provenance;
- identity;
- canonicalization;
- assets;
- search projections;
- quality;
- admin/audit.

## Rationale
- preserves transactional simplicity;
- lower deployment/observability cost;
- easier testing and local development;
- avoids premature distributed failure modes;
- clear module APIs enable future extraction.

## Consequences
- module dependency rules must be enforced;
- workers may share domain packages/contracts but cannot bypass canonical write paths;
- internal domain events/outbox prepare for eventual distribution;
- scaling decisions are benchmark-driven.

## Rejected alternative
Microservices from day one. This would add network, deployment, consistency and operational complexity before we know which domains need independent scale.

## Extraction triggers
A module becomes a service only when measured evidence shows independent scaling, failure isolation, ownership, deployment cadence or technology requirements justify it.
