# Cinema and Series — Open Decisions Register

**Status: ACTIVE**  
**Rule:** no implementation-critical OPEN item may be silently decided during coding.

This register exists because the project contract requires architecture, data behavior, source policy and product behavior to be decided before production implementation begins.

Decision states:
- `OPEN` — unresolved, freeze blocker if implementation-critical.
- `WORKING` — preferred direction requiring validation/evidence.
- `LOCKED` — accepted; change requires ADR/spec revision.
- `DEFERRED_OUT_OF_V1` — deliberately outside V1; must not leak into V1 coding.

# A. Domain / identity blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-D01 | Zack Snyder's Justice League: separate Work vs materially distinct Version of 2017 project | OPEN | high | evidence + product behavior adjudication; schema must support either before decision |
| OD-D02 | Kill Bill: The Whole Bloody Affair: combined Version vs compilation/derivative Work | OPEN | high | authoritative release/credit evidence + split/combined model adjudication |
| OD-D03 | Eleanor Rigby: Him/Her/Them identity boundary | OPEN | high | authoritative distribution/creator evidence + Work/Version criteria |
| OD-D04 | Doctor Who 1963/2005 run boundary | WORKING | high | current rule = separate Series-run IDs linked by continuation/revival; expand benchmark and adjudicate |
| OD-D05 | Twin Peaks original/The Return run boundary | OPEN | medium/high | benchmark against Series Identity Spec and official Showtime/creator evidence |
| OD-D06 | Money Heist original-broadcast vs Netflix re-edit content-unit mapping | OPEN | high | obtain broadcaster evidence; validate StructureEdition model |
| OD-D07 | Full Character graph in V1 or text-only role names + optional Character IDs | WORKING | medium | validate product/search requirements; no need for exhaustive character graph if not a core V1 value |
| OD-D08 | External literary/source creative works as first-class V1 entity vs bounded external-source entity | WORKING | medium | adaptation benchmark breadth; freeze minimum representation |
| OD-D09 | Music model (`MusicalWork`, `MusicRecording`, `MusicContribution`, `AudiovisualMusicUsage`) | WORKING | high | 50+ Indian music cases across eras/languages; integrate into Entity Model before freeze |

# B. Source / licensing blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-S01 | Exact production source set for initial bulk/open ingestion | OPEN | critical | field-source matrix + licences + benchmark coverage |
| OD-S02 | Wikidata production role and refresh strategy | WORKING | high | dump/API benchmark, vandalism/error strategy, references/qualifier ingestion |
| OD-S03 | MusicBrainz exact CC0 field subset for production adapter | WORKING | high | verify core/supplementary field boundary against adapter contract |
| OD-S04 | TMDB production use | OPEN/PARTNER_REQUIRED | high | either commercial licence before use or keep non-production/test-only |
| OD-S05 | TheTVDB production use | OPEN | medium/high | tier/license/right image policy decision |
| OD-S06 | Streaming availability provider | OPEN | medium | licensed provider/partner or defer availability from launch while retaining schema |
| OD-S07 | CBFC scalable production access | OPEN | medium/high for India depth | do not bypass CAPTCHA; seek official/partner route or retain manual verification path |
| OD-S08 | India historical bulk source/collaboration path | OPEN | high | NFAI/NFDC/open sources/partnership strategy |
| OD-S09 | Initial artwork publication source strategy | OPEN | high UX, not core DB | rights-cleared/open/provider-licensed sources + placeholder policy |
| OD-S10 | Source terms-change monitoring method | WORKING | medium | source registry policy version + scheduled review + adapter kill switch |

# C. Database / backend architecture blockers

Already LOCKED:
- PostgreSQL authoritative store;
- Postgres-first portability even if Supabase hosts initially;
- modular monolith + asynchronous workers;
- source ingestion through immutable evidence/claims;
- canonical projections are derived/rebuildable;
- search is a rebuildable projection;
- TypeScript service layer + Python data tooling + Next.js web/control room + native Kotlin Android direction.

Still open:

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-A01 | TypeScript API framework | OPEN | high | compare Fastify/NestJS/Next server boundary against domain/worker needs; record ADR |
| OD-A02 | Background job/queue technology | OPEN | critical | reliability, retries, schedules, Supabase/Postgres compatibility, free/early-stage cost; record ADR |
| OD-A03 | Object storage for permitted raw snapshots/assets | OPEN | high | Supabase Storage/S3-compatible boundary + retention/right-to-delete requirements |
| OD-A04 | AuthN/AuthZ for Control Room | OPEN | critical | admin roles, least privilege, Supabase Auth portability boundary; record ADR |
| OD-A05 | Public API authentication/rate-limit strategy | OPEN | medium | V1 public read model vs future developer API |
| OD-A06 | Cache technology / invalidation | OPEN | medium | begin no-cache/HTTP/Postgres cache unless measured need; document threshold |
| OD-A07 | Search escalation threshold from Postgres FTS/pg_trgm | WORKING | medium | multilingual benchmark latency/quality threshold; no dedicated engine without evidence |
| OD-A08 | Observability stack | OPEN | high | logs, tracing, errors, source/job metrics, cost |
| OD-A09 | Deployment topology | OPEN | high | web/API/workers/DB/storage environments and separation |
| OD-A10 | Backup/restore RPO/RTO | OPEN | critical | define data classes, backup frequency, PITR/export strategy, restore drill |
| OD-A11 | Canonicalization rule-engine implementation | OPEN | critical | deterministic rule layer + versioning + explainability; AI cannot be authority |
| OD-A12 | Internal event/outbox pattern | OPEN | high | guarantee canonical change -> search/audit/job projections without distributed inconsistency |
| OD-A13 | Stable CAS ID format | OPEN | high | sortable/non-provider IDs, merge safety, public URL ergonomics |
| OD-A14 | Physical partitioning/archive strategy | WORKING | medium | do not partition prematurely; define thresholds for Claims/Snapshots/Audit |
| OD-A15 | Schema migration tooling | OPEN | high | SQL-first/version-controlled migration tool compatible with Postgres/Supabase and CI |
| OD-A16 | API contract tooling | WORKING | medium | OpenAPI-first or generated contract; choose exact framework/tooling |

# D. Control Room / automation blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-C01 | Exact thresholds for AUTO-APPLY vs WATCH vs HUMAN REVIEW | OPEN | critical | validation corpus precision/false-merge testing; field-specific thresholds |
| OD-C02 | Protected-action two-person approval requirement | OPEN | medium | decide whether single-owner V1 supports optional dual review or audit-only |
| OD-C03 | Manual claim authority level | WORKING | high | editor claims are explicit sources; cannot erase upstream evidence; define precedence rules |
| OD-C04 | Bulk review UX | OPEN | medium | design after review-queue data shapes are validated |
| OD-C05 | Source suspension effect on prior canonical facts | WORKING | high | retain claims; recanonicalize if policy invalidates use; preserve audit history |

# E. Consumer product blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-P01 | V1 launch includes streaming availability or schema-only | OPEN | medium | depends on licensed sustainable provider path |
| OD-P02 | V1 launch includes user account/library/watchlist | OPEN | medium | current foundation is database-first; decide after data product core acceptance |
| OD-P03 | Exact consumer navigation labels/order across web vs Android | WORKING | low/medium | production-realistic design validation before UI freeze |
| OD-P04 | Public evidence/provenance depth | WORKING | medium | consumer-friendly source summary vs expert detail; Control Room always deep |
| OD-P05 | Public CAS Coverage display | OPEN | low/medium | decide whether internal-only at V1 or exposed transparently to users |
| OD-P06 | Artwork-less title presentation | WORKING | medium | premium placeholder/text-led card; must never hide title because art unavailable |

# F. Quality / benchmark blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-Q01 | Final ~1,000-case corpus and quota compliance | OPEN/ACTIVE | critical | `VALIDATION_COHORT_QUOTAS.md` |
| OD-Q02 | Machine-readable conversion for all gold cases | OPEN/ACTIVE | critical | validation JSON schema + manifests |
| OD-Q03 | Critical false-merge / false-split pass thresholds | WORKING | critical | QA matrix + corpus execution; identity critical cases should target zero known false auto-merges |
| OD-Q04 | Search quality thresholds by script/transliteration | OPEN | high | query benchmark per priority language/script |
| OD-Q05 | Data coverage SLA for launch | OPEN | high | define by domain/language/era rather than raw title count |

# G. Explicit non-blocking implementation details
The following may remain configurable after V1 freeze **only if their behavior boundaries are already frozen**:
- page-size defaults;
- worker concurrency;
- cache TTL values;
- UI animation durations;
- exact color-token numeric values after design-system freeze;
- index tuning based on measured query plans;
- batch sizes/timeouts within documented safety bounds.

These are not excuses to leave architecture unspecified.

# Freeze rule
`FROZEN_V1_CONTRACT.md` cannot be marked FROZEN while any item marked `critical` in this register remains OPEN, or while a high-impact OPEN item can change entity identity, source legality, data-loss behavior or core product scope.

Every resolved architecture item should point to an ADR. Every resolved domain/product item should point to the controlling specification and validation evidence.
