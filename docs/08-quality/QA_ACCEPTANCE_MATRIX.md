# V1 QA & Acceptance Matrix

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Purpose

This document defines the gates that must be satisfied before the Cinema and Series V1 specification may be frozen and, later, before implementation milestones may be considered done.

Exact numerical thresholds that depend on measured benchmark behavior remain OPEN until the evidence-labeled validation corpus is populated. Thresholds must be chosen before production tuning, not retrofitted to make failures disappear.

## Gate levels

- **G0 Specification** — definitions/decisions exist and do not materially contradict each other.
- **G1 Model validation** — difficult real-world cases can be represented without schema hacks.
- **G2 Engine validation** — deterministic pipeline behavior passes benchmark cases.
- **G3 Control Room validation** — exception workflows are explainable, recoverable and auditable.
- **G4 Consumer semantics** — public surfaces preserve data meaning and uncertainty.
- **G5 Operational readiness** — reliability, backup, observability and policy controls exist.

The Research Foundation freeze primarily requires G0-G1 plus testable specifications for G2-G5. Production launch later requires all applicable gates implemented and tested.

## Acceptance matrix

| Area | Required acceptance condition | Freeze status |
|---|---|---|
| Product scope | V1 goals/non-goals are explicit; no social/news/playback scope is silently assumed. | REQUIRED |
| Domain terminology | Work, Version, ReleaseEvent, Claim, Source, Person, Company, Series/Season/Episode and relationship terms are defined. | REQUIRED |
| Work identity | Remake is separable from dub/version; working-title changes do not create duplicate Works by default. | REQUIRED |
| Episodic model | Series -> Season -> Episode hierarchy handles numbered, special and irregular cases without flattening everything into films. | REQUIRED |
| Localization | Native title, localized title, translation, transliteration and alias are independently representable. | REQUIRED |
| Release model | Multiple territory/version/type/platform dates and reschedules are representable without one global date field. | REQUIRED |
| Lifecycle | Upcoming, filming, delayed, shelved, cancelled and released histories are auditable. | REQUIRED |
| Claims/provenance | Important canonical facts can be explained by admissible claims/evidence. | REQUIRED |
| Canonicalization | Conflicts can remain unresolved; system is not forced to invent a winner. | REQUIRED |
| Identity resolution | Auto-link/review/keep-separate/merge/split paths exist conceptually and merges are recoverable. | REQUIRED |
| External IDs | No provider ID is canonical CAS identity. | REQUIRED |
| Source governance | Every production source must have registry, use/policy status and field scope before activation. | REQUIRED |
| Artwork rights | Metadata correctness and media usage rights are independent. Missing artwork never invalidates a title. | REQUIRED |
| Search semantics | Search plan covers native script, transliteration, aliases, typo/fuzzy behavior and identity disambiguation. | REQUIRED |
| Architecture | PostgreSQL authority, modular monolith/workers, claims ingestion path and rebuildable projections are recorded in ADRs. | REQUIRED |
| Control Room | All high-risk exception workflows have explicit screens/actions/audit behavior. | REQUIRED |
| Consumer IA | Public screens preserve work/version/release/relationship semantics and uncertainty. | REQUIRED |
| Data quality | CAS Coverage and anomaly/quality rules are specified separately from popularity/rating. | REQUIRED |
| Validation corpus | Evidence-labeled benchmark corpus covers the required edge-case cohorts. | BLOCKING |

## Benchmark acceptance categories

The validation corpus must measure at least the following independently.

### Identity
Expected outcomes include:
- same Work;
- different Work;
- same Work different Version;
- remake relationship;
- adaptation relationship;
- ambiguous / human review.

Metrics to define before engine implementation:
- false merge rate;
- false split rate;
- auto-link precision;
- review recall for ambiguous cases.

False merges are treated as especially severe because they corrupt multiple downstream facts.

### Localization/search
Must test:
- native-script exact lookup;
- common Romanization;
- alternate spelling;
- English/localized marketing title;
- typo/fuzzy query;
- person/company same-name ambiguity;
- language/territory filtering.

### Releases
Must test:
- world/festival/theatrical/digital distinctions;
- territory-specific dates;
- multi-language release events;
- postponements/reschedules;
- re-releases/restorations;
- unknown vs announced vs actual date.

### Production lifecycle
Must test:
- official announcement;
- working-title project;
- filming/post-production transitions;
- delayed/on-hold;
- shelved/cancelled;
- release-scheduled to released;
- stale-state detection.

### Relationships
Must test:
- sequel/prequel;
- spin-off;
- remake;
- reboot;
- adaptation;
- franchise/universe;
- anthology;
- alternate cut/version;
- cross-language manifestations.

### Claims/canonicalization
Must test:
- corroborating claims;
- stale weaker claim vs new authoritative claim;
- two authoritative sources in conflict;
- source correction;
- source retraction/removal;
- editor-backed correction;
- unresolved public conflict.

### Source policy
Must test:
- approved source;
- suspended source;
- expired/changed policy status;
- unapproved public page discovery;
- raw-retention restricted source;
- media rights incompatible with metadata use.

## Control Room acceptance scenarios

Before V1 implementation is considered complete, operators must be able to perform and recover from:
- approve/reject identity candidate;
- keep similar works separate;
- merge duplicate entities with preview;
- reverse an incorrect merge;
- resolve/leave unresolved a fact conflict;
- classify dub/version/remake;
- correct release history without deleting old schedule;
- add manual correction as a claim;
- suspend a source adapter;
- inspect job failure/dead-letter context;
- reprocess a bounded cohort;
- approve/reject artwork with rights context;
- trace a public fact to evidence/audit history.

## Consumer acceptance scenarios

A public user must be able to:
- distinguish two same-title works;
- see native/original title and searchable transliteration;
- understand whether a related title is a remake, sequel or dub/version;
- see territory-specific release context;
- see changing/upcoming date status without outdated dates silently replacing history;
- browse craft credits beyond headline cast;
- use the product when artwork is missing;
- see a clear uncertainty/conflict indicator when data is not settled.

## Non-functional acceptance categories

Exact implementation thresholds will be frozen later, but V1 architecture must support testing for:
- API latency and pagination;
- ingestion throughput;
- job idempotency;
- retry/backoff correctness;
- concurrency safety;
- database backup/restore;
- search rebuild from canonical data;
- source outage isolation;
- observability/alerting;
- audit integrity;
- authorization on privileged operations;
- accessibility;
- responsive Android/web behavior.

## Freeze blockers

The V1 specification must not be frozen while any of these remain materially undefined:
1. canonical entity boundary that changes core schema;
2. source/legal assumption on which V1 coverage depends;
3. unrecoverable merge/identity behavior;
4. release model unable to express benchmark cases;
5. native-title/localization model ambiguity;
6. no evidence path for important canonical facts;
7. no validation corpus covering required cohorts;
8. architecture decision conflict;
9. Control Room unable to resolve a known high-risk exception type.

## Anti-gaming rule

No benchmark case may be removed solely because the engine performs poorly on it. Cases can be corrected/reclassified only with documented evidence that the test expectation itself was wrong.
