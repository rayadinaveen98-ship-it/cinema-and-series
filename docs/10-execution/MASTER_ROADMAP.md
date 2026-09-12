# Master Roadmap

**Status: WORKING**  
**Current milestone: Research Foundation v0.1**

## Build philosophy

Cinema and Series is executed in two eras:

1. **Definition, research, and proof** — determine what the product means and prove the hard data problems before building production surfaces.
2. **Implementation and scale** — build only after the frozen V1 contract exists.

---

# ERA A — Definition, Research, Proof

## Phase 0 — Project Constitution

**Goal:** establish permanent product rules and execution discipline.

Deliverables:
- product vision
- product philosophy
- V1 scope
- V1 non-goals
- decision-state system
- required reading order

**Status:** substantially initialized on 2026-09-12; remains WORKING until Research Foundation review.

## Phase 1 — Market, Gap, and Source Research

**Goal:** understand the competitive landscape and prove which data sources are legally, technically, and economically usable.

Deliverables:
- competitor audit
- India gap analysis
- global database landscape
- source registry
- source licensing matrix
- source trust model
- data-field/source matrix
- provider failure/fallback analysis
- artwork/media rights strategy

Exit gate:
- every V1 metadata class has at least one viable acquisition strategy or is explicitly marked unavailable/deferred;
- no planned production source depends on unreviewed reuse assumptions.

## Phase 2 — Domain and Data Model

**Goal:** freeze the semantic model before production database migrations.

Deliverables:
- terminology/glossary
- entity model
- work/version/manifestation policy
- person/company model
- credit model
- localization/title model
- release-event model
- production lifecycle
- relationship graph
- source/claim/provenance model
- asset rights model
- audit/change model
- ERD

Exit gate:
- difficult validation corpus cases can be represented without hacks or provider-specific fields becoming the domain model.

## Phase 3 — Research Data Pipeline Prototype

**Goal:** test source acquisition, parsing, normalization, provenance, and replayability on a disposable/non-production pipeline.

Deliverables:
- approved-source prototype adapters
- raw snapshot convention
- parser versioning convention
- normalized candidate schema
- reproducible test fixtures
- source-health metrics

Exit gate:
- source observations can be ingested repeatedly without losing provenance or producing uncontrolled duplicates.

## Phase 4 — Identity and Canonicalization Proof

**Goal:** prove that records from multiple sources can be resolved safely.

Deliverables:
- canonical ID strategy
- exact-ID matching
- title/year/language/cast/company feature model
- candidate duplicate scoring
- auto-match thresholds
- human-review thresholds
- merge/split workflow
- canonicalization rules
- conflict model
- manual override/audit rules

Exit gate:
- benchmark duplicate/identity corpus meets frozen precision/recall targets;
- uncertain cases reliably enter review instead of being silently merged.

## Phase 5 — Search and Localization Proof

**Goal:** prove that global and Indian-language discovery works against the domain model.

Deliverables:
- normalized search document
- exact/fuzzy search
- alias/native-script indexing
- transliteration approach for priority Indian languages
- person search
- structured filters
- relevance benchmark suite

Exit gate:
- frozen search test corpus meets agreed recall and ranking targets.

## Phase 6 — Product and Admin UX Specification

**Goal:** design consumer and data-operations experiences against proven data contracts.

Deliverables:
- information architecture
- navigation model
- screen inventory
- user flows
- title/movie/series/person page specifications
- release timeline interaction
- provenance/evidence presentation
- admin review queues
- source-health/quality dashboards
- design philosophy
- design system
- production-realistic Figma prototypes
- accessibility requirements

Exit gate:
- every major UI element maps to real domain/API data;
- no visual concept requires data that has no acquisition/legal strategy.

## Phase 7 — Quality, Security, Operations, and V1 Freeze

**Goal:** define measurable production acceptance criteria.

Deliverables:
- CAS Coverage model
- data-quality scorecards
- source freshness SLAs
- benchmark validation corpus
- QA matrix
- security/threat model
- backup/recovery targets
- observability requirements
- cost envelope
- final ADRs
- `FROZEN_V1_CONTRACT.md`

Exit gate:
- V1 contract explicitly marked FROZEN.

---

# ERA B — Implementation and Scale

Implementation starts only after Phase 7 passes.

## Phase 8 — Platform Foundation

- repository/workspace production structure
- database migrations
- CI/CD
- environments
- secrets/configuration strategy
- API skeleton
- worker/job infrastructure
- observability baseline

## Phase 9 — Core Data Platform

- canonical catalog
- people/companies/credits
- localization
- releases
- lifecycle
- relationships
- claims/provenance
- audit history
- assets

## Phase 10 — Production Ingestion

- source adapters approved for production
- ingestion orchestration
- replay/reprocessing
- policy enforcement
- source monitoring

## Phase 11 — Identity, Canonicalization, and Quality

- production resolver
- conflict queues
- merge/split tools
- canonical rule engine
- coverage/quality dashboards

## Phase 12 — Search

- production search index/projection
- multilingual/transliteration behavior
- relevance tests
- filters/facets

## Phase 13 — Admin Control Center

- new-title queue
- duplicate/conflict review
- source evidence
- canonical editor
- asset review
- change history
- source health

## Phase 14 — Public API and Web

- stable read contracts
- web catalogue/explore/search/title/series/person experiences
- release timelines and evidence surfaces

## Phase 15 — Android

- native Kotlin/Jetpack Compose application
- same canonical API contracts
- premium cinematic archive design system

## Phase 16 — V1 Production Validation

- benchmark corpus regression
- load/performance tests
- accessibility
- backup/restore test
- source outage tests
- security review
- data-quality acceptance
- beta launch decision

---

# Rules for changing this roadmap

- New features do not jump ahead of unresolved foundation work simply because they are visually exciting.
- Research prototypes are disposable unless explicitly promoted after review.
- Every implementation-phase dependency must point to a frozen specification.
- If research invalidates a working assumption, update the specification first, then the roadmap.
- Future chat/agent sessions must read `START_HERE.md` before executing project work.
