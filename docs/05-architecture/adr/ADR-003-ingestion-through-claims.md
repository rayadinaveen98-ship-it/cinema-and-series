# ADR-003 — Source Adapters Cannot Write Canonical Data Directly

**Status: ACCEPTED / WORKING TOWARD LOCK**  
**Date: 2026-09-12**

## Context
Multiple sources will disagree, change, disappear and operate under different licenses. Allowing an importer to write directly to canonical title/person/release tables would make provenance and conflict handling impossible.

## Decision
All external ingestion follows:

`Source -> Snapshot -> Observation -> Identity Resolution -> Claim -> Canonicalization -> Canonical Projection`

No source adapter may directly mutate canonical entertainment facts.

## Rationale
- preserves provenance;
- enables reprocessing after parser changes;
- supports disagreements/supersession;
- isolates provider-specific schema;
- makes source suspension/contract termination survivable;
- prevents "last importer wins" corruption.

## Consequences
- ingestion is more deliberate than a simple upsert;
- claims/history storage volume is higher;
- canonicalization/review tooling is mandatory;
- source adapters remain replaceable.

## Exception policy
There is no ordinary provider exception. Even verified first-party contributor input is represented as evidence/Claims under an authenticated Source identity.

Derived system fields may update projections without external Claims only when the derivation rule and inputs are recorded.
