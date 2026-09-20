# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — 16,380-TITLE REBASELINE ACTIVE  
**Date:** 2026-09-20  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. The corrected V3 orchestration is merged to `main`, the reviewed source-identity cleanup completed successfully on **2026-09-20 UTC**, and the next eligible recommendation-data mutation is the **V3 top-up**.

Production recommendation metadata still contains only the inherited parent shard-0 materialization; the cleanup changed source identity rows only and did not populate a recommendation V3 operation.

The corrected frozen recommendation projection remains exactly:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**
- cross-type collisions after reviewed cleanup: **0**

This fingerprint supersedes the obsolete 14,115-title / 8-shard production-population contract.

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Reviewed media-identity corrections — COMPLETE

The durable correction registry is `data/quality/media_identity_corrections.json`, consumed by `scripts/media_identity_corrections.py`.

Reviewed identities:

- **`Q3049630` — Eko Eko Azarak**: non-audiovisual manga-series identity; excluded from Movie and Series recommendation projection.
- **`Q3146368` — Shattered City: The Halifax Explosion**: reviewed miniseries identity; canonicalized to **Series**.

Unknown or unreviewed Movie/Series collisions remain hard failures.

### Production cleanup evidence

Controller run **`35490594774`** reserved the 2026-09-20 UTC quota day for operation `cleanup` and dispatched `P1 Reviewed Source Identity Cleanup` run **`35490618771`**.

The cleanup workflow:

1. verified exact expected pre-state,
2. deleted exactly the three reviewed non-canonical source rows,
3. verified exact post-state,
4. retained canonical `series_titles / series-wd-Q3146368`,
5. recaptured the recommendation projection,
6. proved the projection remained exactly **16,380 = 6,562 Movie + 9,818 Series** at SHA `f26f6218...12ff6`, with zero cross-type collisions.

Deleted source rows:

- `movies / wd-Q3049630`
- `series_titles / series-wd-Q3049630`
- `catalogue_titles / wd-Q3146368`

Retained canonical row:

- `series_titles / series-wd-Q3146368`

The reviewed source-cleanup gate is therefore **COMPLETE**.

## Schema and quota guard

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the single-row-per-UTC-day D1 write reservation. Its legacy `shard_index` range remains `0..7`; V3 uses it only as a guard slot while binding the exact operation into `workflow_run_id` as `<controller-run-id>:<operation>`.

P1 still owns migrations **0021** and **0022**. Do not add `0023+` to `main` until P1 closes unless the P1 plan is explicitly revised.

The 2026-09-20 quota day is intentionally consumed by the completed source cleanup. It must not be reused for a recommendation operation.

## Immutable materialization evidence

### Parent materialization

- run: **`35252106776`**
- analysis commit: **`0e319f86a4a9c7ca085de93bb5b3246606b7d6d0`**
- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- parent projection SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**
- genre relationships: **13,689**
- credit relationships: **58,069**
- production mutation: **false**

Exact lineage to the corrected projection:

- unchanged reusable identities: **14,114**
- newly added identities: **2,266**
- removed identities: **1**
- removed QID: **`Q3049630` only**
- changed common entries: **0**

### Delta materialization — COMPLETE

Workflow: `P1 Rebaseline Materialization V2`  
Run: **`35421562708`**  
Production mutation: **false**

Evidence:

- candidate titles: **2,266 / 2,266**
- missing title entities: **0**
- skipped relationships because of missing labels: **0**
- unusable claims: **5**
- top-up production estimate: **15,531 D1 rows written**

### Authoritative V3 materialization — COMPLETE / READ-ONLY

Workflow: `P1 Repartition Materialization V3`  
Run: **`35428784454`**  
Analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**  
Artifact: `recommendation-metadata-materialization-v3-repartitioned`

Authoritative normalized graph:

- recommendation titles: **16,380**
- distinct genres: **612**
- distinct people: **37,964**
- title-genre relationships: **16,489**
- title-credit relationships: **70,551**
- global materialization graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**

`scripts/verify_p1_v3_production.py` reconstructs the normalized production graph and requires the complete production graph SHA to equal the reviewed V3 graph; counts alone are insufficient.

## V3 quota-safe production plan

Parent shard 0 already present in production corresponds exactly to physical modulo-16 partitions **0 and 8**, so those inherited rows are not rewritten.

Locked recommendation operation order:

`topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`

Exact reviewed write-cost estimates:

| Operation | Estimated D1 rows written |
|---|---:|
| top-up | **15,531** |
| physical 1 | 39,575 |
| physical 2 | 41,741 |
| physical 3 | **49,159** |
| physical 4 | 39,785 |
| physical 5 | 46,591 |
| physical 6 | 39,371 |
| physical 7 | 41,117 |
| physical 9 | 40,831 |
| physical 10 | 36,946 |
| physical 11 | 40,223 |
| physical 12 | 39,166 |
| physical 13 | 47,836 |
| physical 14 | 41,466 |
| physical 15 | 42,118 |

Largest reviewed write is **49,159 rows**, below the P1 conservative **80,000 rows/UTC-day** ceiling.

## V3 production orchestration — MERGED / ACTIVE

PR **#32** merged the corrected 16,380-title V3 orchestration into `main`. The worker `.github/workflows/recommendation-metadata-production-write-v3.yml` requires:

1. `main` branch and explicit production authorization,
2. successful immutable V3 analysis run `35428784454`,
3. V3 analysis commit ancestry,
4. exact artifact-attestation SHA,
5. exact projection SHA and graph SHA,
6. exact executable-file SHA for the selected operation,
7. reviewed source cleanup complete,
8. exact live corrected projection recaptured before every write,
9. operation-bound UTC-day quota guard ownership,
10. selected operation exactly `not_started` before mutation,
11. selected operation exactly `complete` after mutation,
12. zero orphan relationships and zero invalid provenance after every write,
13. final normalized graph exactly equal to graph SHA `9a931b9a...`,
14. final Catalogue Quality V1 **S0 = 0 / S1 = 0**.

The daily controller `.github/workflows/p1-quota-safe-daily-resume.yml` runs at **00:25 UTC** and dispatches at most one production mutation per eligible UTC day.

Its state machine is:

1. refuse a second mutation on an already-reserved UTC day,
2. perform reviewed source cleanup first if needed,
3. process `topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`,
4. hard-stop partial/overfilled state,
5. enforce attested ≤80k write cost,
6. bind exact operation to daily guard token,
7. dispatch exactly one V3 mutation,
8. after all operations, dispatch read-only final graph/catalogue verification,
9. retire only after successful final-verification evidence exists.

## Existing production recommendation state

The recommendation graph still contains the original parent shard-0 materialization from writer run **`35323383185`**:

- recommendation titles: **1,744**
- genres: **235**
- people: **6,184**
- title-genre relationships: **1,641**
- title-credit relationships: **6,931**
- D1 rows written by that parent operation: **65,299**
- orphan/provenance violations: **0**

No corrected V3 recommendation `topup` or physical-shard operation has been written yet. The next eligible operation is therefore **`topup`**, expected at **15,531 rows**.

## Automation safety state

Catalogue-mutating growth workflows remain frozen during P1. PR #34 made the coordinator idempotent when those workflows are already disabled, and the repaired coordinator has subsequently passed on `main`.

The obsolete 14,115-title / 8-shard scheduled writer remains frozen. `P1 Repartition Materialization V3` is manual-only after its immutable read-only assembly run.

A read-only observability workflow is being added at `.github/workflows/p1-production-status-snapshot.yml`. It restores the immutable V3 artifact, probes every operation state, records current graph counts, source-cleanup state, orphan/provenance health and UTC quota-day ownership, and emits one compact JSON/Markdown status artifact. It is explicitly forbidden from D1 mutations, migrations, workflow dispatches or infrastructure creation.

## Remaining P1 gates

1. ~~lock reviewed media-identity corrections~~ ✅
2. ~~freeze stale catalogue / old daily-write paths~~ ✅
3. ~~materialize all 2,266 new identities~~ ✅
4. ~~assemble and attest exact 16,380-title V3 graph~~ ✅
5. ~~derive 16-way quota-safe write plan~~ ✅
6. ~~finish V3 orchestration CI / contract review~~ ✅
7. ~~merge PR #32 with V3 analysis ancestry preserved~~ ✅
8. ~~execute reviewed source cleanup on its own reserved UTC quota day~~ ✅
9. execute **top-up + 14 remaining physical shards**, one operation per eligible UTC day
10. run final exact graph verification
11. require Catalogue Quality V1 **S0 = 0 / S1 = 0**
12. record final production evidence and mark P1 COMPLETE

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the production graph exactly matches the reviewed V3 graph, referential/provenance checks pass, reviewed source identity cleanup is complete, and post-write catalogue quality remains S0/S1 clean. P2/onboarding does not begin from a partial materialization.
