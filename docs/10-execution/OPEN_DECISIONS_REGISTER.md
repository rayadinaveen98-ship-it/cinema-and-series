# Cinema and Series — Open Decisions Register

**Status: ACTIVE**  
**Rule:** no implementation-critical OPEN item may be silently decided during coding.

Decision states:
- `OPEN` — unresolved; freeze blocker when critical/high-impact.
- `WORKING` — preferred direction requiring measured validation.
- `LOCKED` — accepted; changes require ADR/spec revision.
- `LOCKED TARGET / EXECUTION PENDING` — required behavior/threshold is decided, but evidence still must prove it.
- `DEFERRED_OUT_OF_V1` — deliberately outside V1.

# A. Domain / identity decisions

| ID | Decision | State | Resolution |
|---|---|---|---|
| OD-D01 | Zack Snyder's Justice League Work/Version boundary | LOCKED | materially distinct Version of underlying Justice League Work under V1 semantics |
| OD-D02 | Kill Bill: The Whole Bloody Affair | LOCKED | Combined/Compilation Work derived from Volume 1 + Volume 2; original IDs survive |
| OD-D03 | Eleanor Rigby: Him/Her/Them | LOCKED | separate linked Works; Them derives from Him + Her |
| OD-D04 | Doctor Who 1963/2005 | LOCKED | separate Series-run Work IDs linked by revival/continuation and shared program lineage |
| OD-D05 | Twin Peaks / The Return | LOCKED | separate 2017 Series Work linked by continuation/lineage |
| OD-D06 | Money Heist broadcaster/Netflix recut | LOCKED | one Series Work with StructureEditions/ContentUnitMappings |
| OD-D07 | Character graph | LOCKED | bounded optional Character entities + role text; exhaustive graph not required |
| OD-D08 | Literary/source works | LOCKED | bounded `ExternalCreativeWork` entity; not a general books/comics/games database |
| OD-D09 | Film music model | LOCKED | MusicalWork, MusicRecording, MusicContribution, AudiovisualMusicUsage + soundtrack release mappings |

# B. Source / licensing decisions

| ID | Decision | State | Resolution |
|---|---|---|---|
| OD-S01 | Initial production source baseline | LOCKED | Wikidata CC0 + MusicBrainz CC0 core + CAS editorial/manual evidence; additional adapters opt-in only |
| OD-S02 | Wikidata ingestion/refresh | LOCKED | `docs/04-engines/WIKIDATA_ADAPTER_CONTRACT.md` |
| OD-S03 | MusicBrainz CC0 boundary | LOCKED | `docs/04-engines/MUSICBRAINZ_ADAPTER_CONTRACT.md` |
| OD-S04 | TMDB production use | DEFERRED_OUT_OF_V1 | commercial/licensed adapter may be added later |
| OD-S05 | TheTVDB production use | DEFERRED_OUT_OF_V1 | future licensed adapter only |
| OD-S06 | Streaming availability provider | DEFERRED_OUT_OF_V1 | schema remains; no V1 promise without sustainable licensed provider |
| OD-S07 | Scalable CBFC ingestion | WORKING / NON-BLOCKING | no CAPTCHA bypass; manual verification allowed; partnership/API remains desirable |
| OD-S08 | India historical source strategy | LOCKED | open seed + manual archival evidence; institutional bulk feed only with permission |
| OD-S09 | Artwork publication baseline | LOCKED | verified open/public-domain/licensed/approved assets + premium placeholder fallback |
| OD-S10 | Source-terms monitoring | LOCKED | policy version, scheduled review, adapter kill switch, material change as incident |

# C. Database / backend architecture decisions

Locked ADRs:
- ADR-001 PostgreSQL canonical authority;
- ADR-002 modular monolith + independent workers;
- ADR-003 ingestion through immutable evidence/Claims;
- ADR-004 rebuildable canonical projections;
- ADR-005 rebuildable search projection;
- ADR-006 Postgres-first portability with Supabase initially allowed;
- ADR-007 TypeScript/Python/Next.js/Kotlin stack direction;
- ADR-008 `pgmq`/Supabase Queues + `pg_cron`;
- ADR-009 SQL-first version-controlled migrations;
- ADR-010 Supabase Auth + custom claims/RLS Control Room RBAC;
- ADR-011 NestJS + Fastify + OpenAPI;
- ADR-012 transactional outbox;
- ADR-013 RFC 9562 UUIDv7 CAS IDs;
- ADR-014 S3-compatible ObjectStore abstraction;
- ADR-015 layered backup/recovery and production RPO/RTO;
- ADR-016 deterministic versioned canonicalization; AI is not canonical authority;
- ADR-017 public consumer API + no dedicated external cache initially;
- ADR-018 logical deployment units + provider-neutral observability.

Remaining measured/non-blocking architecture items:

| ID | Decision | State | Resolution path |
|---|---|---|---|
| OD-A07 | Dedicated search-engine escalation | LOCKED BOUNDARY / EXECUTION PENDING | start PostgreSQL FTS/pg_trgm; escalate only if locked search quality/latency gates fail after reasonable tuning |
| OD-A14 | Physical partitioning/archive strategy | WORKING / NON-BLOCKING | start unpartitioned; partition high-volume Claims/Snapshots/Audit only after measured thresholds |

All other previously listed API, queue, object-store, auth, cache, observability, deployment, recovery, canonicalization, outbox, ID, migration and contract-tooling decisions are resolved by ADR-008..018.

# D. Control Room / automation decisions

| ID | Decision | State | Resolution |
|---|---|---|---|
| OD-C01 | AUTO-APPLY/WATCH/HUMAN thresholds | LOCKED | `AUTOMATION_THRESHOLDS_V1.md`; no automatic entity merge; destructive identity ambiguity always reviewed |
| OD-C02 | Two-person approval | LOCKED | single-owner V1 uses explicit confirmation + reason + immutable audit; schema supports future dual approval |
| OD-C03 | Manual claim authority | LOCKED | editor Claims cannot erase evidence or automatically outrank direct authority; audited CanonicalDecision required |
| OD-C04 | Bulk review UX details | WORKING / NON-BLOCKING | implement after real queue data exists; protected semantics are already frozen |
| OD-C05 | Source suspension behavior | LOCKED | halt ingestion, preserve Claims where legal, recanonicalize only when policy/evidence requires; CAS identity survives |

# E. Consumer product decisions

| ID | Decision | State | Resolution |
|---|---|---|---|
| OD-P01 | Streaming availability in launch V1 | DEFERRED_OUT_OF_V1 | schema supported; no consumer promise without licensed provider |
| OD-P02 | User account/library/watchlist | DEFERRED_OUT_OF_V1 | database-first V1 does not require them |
| OD-P03 | Primary navigation | LOCKED | Home, Explore, Search, Calendar; entity pages via navigation |
| OD-P04 | Public provenance depth | LOCKED | simple evidence badges + expandable Sources/history; Control Room remains claim-deep |
| OD-P05 | Public CAS Coverage | LOCKED | numeric dimensional score internal-only; consumer sees qualitative verification/incompleteness states |
| OD-P06 | Artwork-less titles | LOCKED | premium metadata-led placeholder; missing art never hides/down-ranks a Work |

# F. Quality / benchmark gates

| ID | Decision | State | Freeze impact / evidence path |
|---|---|---|---|
| OD-Q01 | Final ~1,000-case corpus + quota compliance | OPEN / ACTIVE | **critical blocker** — `VALIDATION_COHORT_QUOTAS.md` |
| OD-Q02 | Machine-readable assertions for every eventual gold/adjudicated case | OPEN / ACTIVE | **critical blocker** — current researched set is 115/115 converted; continue on every new case |
| OD-Q03 | False-merge/false-split safety target | LOCKED TARGET / EXECUTION PENDING | zero known critical automatic false merges/misclassifications in gold cases; run benchmark |
| OD-Q04 | Search quality thresholds by script/transliteration | LOCKED TARGET / EXECUTION PENDING | `SEARCH_QUALITY_BENCHMARK_V1.md`, `SEARCH_QUALITY_THRESHOLDS_V1.md`, `SEARCH_QUALITY_GATE_RECONCILIATION_V1.md`; >=500 pre-freeze assertions and >=2,000 public-launch benchmark |
| OD-Q05 | Data coverage SLA for launch | LOCKED TARGET / EXECUTION PENDING | `LAUNCH_COVERAGE_SLA_V1.md`; benchmark-specific, language/era/domain-aware measurements |

# G. Non-blocking implementation configuration

These may remain tunable after V1 freeze only inside already-frozen behavior boundaries:
- page-size defaults;
- worker concurrency;
- rate-limit numeric values;
- cache TTLs;
- UI animation durations;
- final design token numeric values;
- index/query-plan tuning;
- batch sizes/timeouts;
- exact Node/runtime hosting vendor within ADR-018 boundaries.

# Freeze rule

`FROZEN_V1_CONTRACT.md` cannot be marked FROZEN while a critical item remains genuinely OPEN or while an unresolved high-impact question can change identity, source legality, data-loss behavior or core scope.

**Current genuine pre-freeze blockers:**
1. complete/adjudicate the ~1,000-case stratified validation corpus;
2. keep machine-readable assertions complete for every gold/adjudicated case;
3. build the >=500 pre-freeze multilingual search assertions and execute the required research/engine validations;
4. resolve any model defect those validations expose.

Search quality and launch coverage are no longer undefined design decisions; their targets are frozen and await evidence.
