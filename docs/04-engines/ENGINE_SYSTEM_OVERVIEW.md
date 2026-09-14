# Engine System Overview

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Purpose

Cinema and Series is operated by a set of dedicated data engines. Engines discover, acquire, parse, normalize, reconcile, validate and maintain cinema/series knowledge. The internal Control Room supervises them; humans handle ambiguity rather than routine ingestion.

## Golden rule

**No engine may write provider-derived values directly into canonical title/person/release records.**

All external observations flow through evidence and claims:

`Source -> Snapshot -> Parsed Observation -> Normalized Claim -> Identity Resolution -> Canonicalization -> Canonical Projection`

## Engine map

1. **Source Registry Engine** — knows approved sources, terms status, access method, trust profile, cadence and adapter health.
2. **Discovery Engine** — finds possible new works, people, companies, announcements and changes worth investigating.
3. **Acquisition Engine** — retrieves data only through approved source adapters and records immutable source snapshots where permitted.
4. **Parsing Engine** — converts source material into structured observations without deciding canonical truth.
5. **Normalization Engine** — standardizes dates, names, territories, languages, identifiers, credit roles and other values while preserving original source values.
6. **Identity Engine** — determines whether observations refer to an existing CAS entity, a new entity, or an ambiguous candidate.
7. **Claims Engine** — stores source-backed assertions and their evidence/provenance.
8. **Canonicalization Engine** — selects/derives the current canonical projection under explicit field-specific rules.
9. **Conflict Engine** — detects material disagreement among claims and creates review work where automation is unsafe.
10. **Release Engine** — maintains territory/language/platform/version-specific release events and reschedule history.
11. **Production Lifecycle Engine** — tracks announced, filming, post-production, completed, delayed, shelved, cancelled and released states over time.
12. **Relationship Engine** — maintains sequels, prequels, remakes, reboots, adaptations, franchise/universe and anthology relationships.
13. **Artwork/Media Engine** — discovers and manages media separately from metadata, including rights/provenance/usage status.
14. **Search Projection Engine** — creates rebuildable multilingual search documents from canonical data.
15. **Quality Engine** — detects missing, stale, contradictory, suspicious or structurally invalid data and computes CAS Coverage metrics.
16. **Audit/History Engine** — preserves canonical changes, review decisions, merge/split operations and privileged actions.

## Automation tiers

### Tier A — safe auto-processing
May complete without human review when all relevant gates pass:
- source is approved for production use;
- identity match is above the validated automatic threshold;
- claim is structurally valid;
- no protected conflict exists;
- field-specific canonicalization rule has a deterministic winner;
- operation is reversible/auditable.

### Tier B — review required
Examples:
- plausible duplicate with medium identity confidence;
- two competent sources disagree materially;
- working title may have become final title but linkage is uncertain;
- version/dub/remake classification is ambiguous;
- authoritative source conflicts with a newer but weaker source;
- relationship graph change could merge/split user-visible works.

### Tier C — hold/reject
Examples:
- source is not approved for the intended reuse;
- unsupported rumor with no admissible evidence;
- parser output is malformed or low-confidence;
- asset rights cannot support display/use;
- operation would destroy unresolved provenance.

## Human-in-the-loop principle

The Control Room should minimize manual work. Humans review **exceptions**, not every imported record.

Target operating pattern:

`large automated throughput -> small prioritized exception queue -> auditable human decisions`

## Engine boundaries

- Discovery may create candidates, not canonical works.
- Acquisition may create snapshots, not canonical facts.
- Parsing may create observations, not truth.
- Identity may propose/link entities, but uncertain destructive merges require review.
- Canonicalization may select among claims, but cannot invent unsupported facts.
- Quality may flag problems, not silently rewrite evidence.
- Artwork may approve media use, but missing artwork must never block metadata existence.
- Search/indexing is derived and rebuildable.

## Required observability per engine

Each engine must expose at least:
- jobs attempted/succeeded/failed;
- queue depth/backlog;
- throughput;
- latency/age of oldest pending item;
- source/field-specific error rate where applicable;
- retry/dead-letter state;
- last successful run;
- policy/version used for the decision;
- audit link to affected entities/claims.

## Safety properties

1. Idempotent ingestion wherever practical.
2. Reversible entity merges and canonical overrides.
3. Append-only evidence/history where feasible.
4. No provider-specific schema leaked into CAS public contracts.
5. Source suspension can stop one adapter without disabling the catalogue.
6. Search/cache/index loss cannot destroy authoritative data.
7. AI assistance may classify/extract/suggest, but unsupported AI output cannot become canonical metadata.

## Implementation note

These are logical engines, not necessarily separate deployed microservices. V1 uses a modular monolith plus asynchronous workers unless later ADRs prove extraction is necessary.
