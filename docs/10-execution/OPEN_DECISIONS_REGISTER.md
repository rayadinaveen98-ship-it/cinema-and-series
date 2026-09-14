# Cinema and Series — Open Decisions Register

**Status: ACTIVE**  
**Rule:** no implementation-critical OPEN item may be silently decided during coding.

This register exists because the project contract requires architecture, data behavior, source policy and product behavior to be decided before production implementation begins.

Decision states:
- `OPEN` — unresolved, freeze blocker if implementation-critical.
- `WORKING` — current preferred direction requiring validation/evidence.
- `LOCKED` — accepted; change requires ADR/spec revision.
- `DEFERRED_OUT_OF_V1` — deliberately outside V1; must not leak into V1 coding.

# A. Domain / identity decisions

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-D01 | Zack Snyder's Justice League: separate Work vs materially distinct Version | LOCKED | resolved | `DOMAIN_ADJUDICATIONS_V1.md`: materially distinct Version of underlying Justice League Work |
| OD-D02 | Kill Bill: The Whole Bloody Affair combined identity | LOCKED | resolved | distinct Combined/Compilation Work derived from Volume 1 + Volume 2; original Work IDs preserved |
| OD-D03 | Eleanor Rigby: Him/Her/Them identity boundary | LOCKED | resolved | Him, Her and Them are separate linked Works under one project/collection; Them derives from Him+Her |
| OD-D04 | Doctor Who 1963/2005 run boundary | LOCKED | resolved | separate Series-run Work IDs linked by revival/continuation and one program lineage |
| OD-D05 | Twin Peaks original/The Return run boundary | LOCKED | resolved | separate Series Work for 2017 limited event continuation, linked to original lineage |
| OD-D06 | Money Heist original-broadcast vs Netflix re-edit mapping | LOCKED | resolved | one Series Work with multiple StructureEditions/ContentUnitMappings; provider recut does not reset Series ID |
| OD-D07 | Full Character graph in V1 | LOCKED | resolved | bounded optional Character entities + role text; exhaustive Character graph not required |
| OD-D08 | External literary/source creative works in V1 | LOCKED | resolved | bounded first-class `ExternalCreativeWork` source entity; not a full book/comic/game database |
| OD-D09 | Music model | LOCKED | resolved | `MusicalWork`, `MusicRecording`, `MusicContribution`, `AudiovisualMusicUsage` + soundtrack release mappings |

# B. Source / licensing decisions

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-S01 | Exact production source set for initial bulk/open ingestion | LOCKED | resolved | `INITIAL_PRODUCTION_SOURCE_BASELINE.md`: Wikidata CC0 + MusicBrainz CC0 core + CAS editorial/manual evidence; other adapters opt-in only after approval |
| OD-S02 | Wikidata production role and refresh strategy | LOCKED | resolved | `WIKIDATA_ADAPTER_CONTRACT.md`: weekly JSON entity dump baseline + incremental/add-change validation + targeted refresh; statements become Claims |
| OD-S03 | MusicBrainz exact CC0 field subset for production adapter | LOCKED | resolved | `MUSICBRAINZ_ADAPTER_CONTRACT.md`: CC0 core dump allowlist; supplementary/non-commercial datasets fail closed |
| OD-S04 | TMDB production use | DEFERRED_OUT_OF_V1 | resolved for baseline | may be added later only under appropriate commercial licence/approval |
| OD-S05 | TheTVDB production use | DEFERRED_OUT_OF_V1 | resolved for baseline | future licensed adapter only |
| OD-S06 | Streaming availability provider | DEFERRED_OUT_OF_V1 | resolved for baseline | schema remains; launch availability disabled unless licensed sustainable provider is approved |
| OD-S07 | CBFC scalable production access | WORKING | non-blocking architecture / high coverage value | no CAPTCHA bypass; manual verification allowed; seek official/partner path for scalable ingestion |
| OD-S08 | India historical bulk source/collaboration path | LOCKED | resolved architecture | `INDIA_HISTORICAL_SOURCE_STRATEGY_V1.md`: open seed + manual archival evidence; bulk institutional adapter only with permission |
| OD-S09 | Initial artwork publication source strategy | LOCKED | resolved | `ARTWORK_PUBLICATION_BASELINE_V1.md`: verified open/public-domain/licensed/approved assets + premium placeholder fallback |
| OD-S10 | Source terms-change monitoring method | LOCKED | resolved | version source policy/terms reference; scheduled review; adapter kill switch; material change = operational incident |

# C. Database / backend architecture decisions

Already LOCKED:
- PostgreSQL authoritative store — ADR-001;
- modular monolith — ADR-002;
- source ingestion through immutable evidence/claims — ADR-003;
- canonical projections are derived/rebuildable — ADR-004;
- search is a rebuildable projection — ADR-005;
- Postgres-first portability even if Supabase hosts initially — ADR-006;
- TypeScript/Python/Next.js/Kotlin stack direction — ADR-007;
- Postgres-native durable queues (`pgmq`) + `pg_cron` scheduling — ADR-008;
- SQL-first, version-controlled database migrations — ADR-009;
- Supabase Auth + custom claims/RLS Control Room RBAC — ADR-010;
- NestJS + Fastify + OpenAPI API layer — ADR-011;
- transactional outbox for domain-event propagation — ADR-012;
- provider-independent UUIDv7 canonical IDs — ADR-013;
- S3-compatible ObjectStore abstraction; Supabase Storage may be initial implementation — ADR-014;
- layered backup/recovery with production RPO/RTO and restore drills — ADR-015;
- deterministic versioned canonicalization rules; AI is not canonical authority — ADR-016;
- public consumer API + no dedicated external cache initially — ADR-017;
- logical deployment units + provider-neutral observability contract — ADR-018.

Remaining architecture decisions:

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-A01 | TypeScript API framework | LOCKED | resolved | ADR-011 — NestJS + Fastify |
| OD-A02 | Background job/queue technology | LOCKED | resolved | ADR-008 — pgmq/Supabase Queues + pg_cron scheduling |
| OD-A03 | Object storage for permitted raw snapshots/assets | LOCKED | resolved | ADR-014 — S3-compatible ObjectStore; Supabase Storage initial candidate |
| OD-A04 | AuthN/AuthZ for Control Room | LOCKED | resolved | ADR-010 — Supabase Auth custom claims + RLS + domain permissions |
| OD-A05 | Public API authentication/rate-limit strategy | LOCKED | resolved | ADR-017 — public consumer reads without login, gateway rate limits; developer API deferred |
| OD-A06 | Cache technology / invalidation | LOCKED | resolved | ADR-017 — no dedicated cache initially; Postgres/read projections + HTTP/CDN caching; outbox-driven revalidation |
| OD-A07 | Search escalation threshold from Postgres FTS/pg_trgm | WORKING | medium | multilingual benchmark; no dedicated engine without measured need |
| OD-A08 | Observability stack | LOCKED | resolved | ADR-018 — structured logs + OpenTelemetry-compatible tracing/metrics; provider backend replaceable |
| OD-A09 | Deployment topology | LOCKED | resolved | ADR-018 — consumer web, Control Room, API, worker, Python tools, Postgres, ObjectStore are separate logical units |
| OD-A10 | Backup/restore RPO/RTO | LOCKED | resolved | ADR-015 — Tier-A RPO <=5m, RTO <=4h; PITR/equivalent + off-provider logical/object recovery |
| OD-A11 | Canonicalization rule-engine implementation | LOCKED | resolved | ADR-016 — deterministic typed versioned rule engine |
| OD-A12 | Internal event/outbox pattern | LOCKED | resolved | ADR-012 — transactional outbox + idempotent queue consumers |
| OD-A13 | Stable CAS ID format | LOCKED | resolved | ADR-013 — RFC 9562 UUIDv7, provider-independent |
| OD-A14 | Physical partitioning/archive strategy | WORKING | non-blocking until measured scale | begin unpartitioned; partition Claims/Snapshots/Audit only after measured volume/query/maintenance thresholds |
| OD-A15 | Schema migration tooling | LOCKED | resolved | ADR-009 — SQL migrations through Supabase CLI workflow |
| OD-A16 | API contract tooling | LOCKED | resolved | ADR-011 — OpenAPI through NestJS tooling |

# D. Control Room / automation decisions

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-C01 | Thresholds for AUTO-APPLY vs WATCH vs HUMAN REVIEW | LOCKED | resolved | `AUTOMATION_THRESHOLDS_V1.md`: discrete evidence gates; no auto entity merges; destructive identity ambiguity always reviewed |
| OD-C02 | Protected-action two-person approval requirement | LOCKED | resolved | single-owner V1 uses explicit confirmation + reason + immutable audit; schema supports future dual approval |
| OD-C03 | Manual claim authority level | LOCKED | resolved | editor Claims never erase evidence or automatically outrank direct authority; override requires audited CanonicalDecision reason |
| OD-C04 | Bulk review UX | WORKING | non-blocking design detail | implement after real queue data exists; protected action semantics already frozen |
| OD-C05 | Source suspension effect on prior canonical facts | LOCKED | resolved | stop ingestion; retain Claims where legally allowed; recanonicalize only when policy/evidence requires; identities survive |

# E. Consumer product decisions

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-P01 | V1 launch includes streaming availability | DEFERRED_OUT_OF_V1 | resolved | schema supported, no consumer promise without licensed provider |
| OD-P02 | V1 launch includes user account/library/watchlist | DEFERRED_OUT_OF_V1 | resolved | database-first V1 has no mandatory consumer accounts/library/watchlist |
| OD-P03 | Consumer primary navigation | LOCKED | resolved | `Home`, `Explore`, `Search`, `Calendar`; entity pages via navigation |
| OD-P04 | Public evidence/provenance depth | LOCKED | resolved | simple evidence badges + expandable Sources & history; Control Room remains claim-deep |
| OD-P05 | Public CAS Coverage display | LOCKED | resolved | dimensional numeric CAS Coverage internal-only in V1; consumers see qualitative verification/incompleteness states |
| OD-P06 | Artwork-less title presentation | LOCKED | resolved | premium metadata-led placeholder; no title hidden or down-ranked merely for lack of art |

# F. Quality / benchmark blockers

| ID | Decision | State | Freeze impact | Resolution path |
|---|---|---|---|---|
| OD-Q01 | Final ~1,000-case corpus and quota compliance | OPEN/ACTIVE | critical | `VALIDATION_COHORT_QUOTAS.md` |
| OD-Q02 | Machine-readable conversion for all gold cases | OPEN/ACTIVE | critical | validation JSON schema + manifests |
| OD-Q03 | Critical false-merge / false-split pass thresholds | LOCKED target / execution pending | critical execution gate | `AUTOMATION_THRESHOLDS_V1.md`: zero known critical automatic false merges/misclassifications; execute against corpus |
| OD-Q04 | Search quality thresholds by script/transliteration | OPEN | high | query benchmark per priority language/script |
| OD-Q05 | Data coverage SLA for launch | OPEN | high | define by domain/language/era rather than raw title count |

# G. Explicit non-blocking implementation details
The following may remain configurable after V1 freeze **only if their behavior boundaries are already frozen**:
- page-size defaults;
- worker concurrency;
- rate-limit numeric values;
- cache TTL values;
- UI animation durations;
- exact color-token numeric values after design-system freeze;
- index tuning based on measured query plans;
- batch sizes/timeouts within documented safety bounds;
- exact Node/runtime hosting vendor so long as ADR-018 boundaries hold.

These are not excuses to leave architecture unspecified.

# Freeze rule
`FROZEN_V1_CONTRACT.md` cannot be marked FROZEN while any item marked `critical` in this register remains OPEN, or while a high-impact OPEN item can change entity identity, source legality, data-loss behavior or core product scope.

At this point, the remaining genuine freeze blockers are primarily **validation evidence, search/transliteration quality and launch coverage SLA**, not unresolved core architecture.
