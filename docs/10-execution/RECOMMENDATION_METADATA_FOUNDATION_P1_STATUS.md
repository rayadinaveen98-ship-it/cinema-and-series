# Recommendation Metadata Foundation P1 — Execution Status

**Status:** PRODUCTION POPULATION IN PROGRESS — 16,380-TITLE REBASELINE ACTIVE  
**Date:** 2026-09-19  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Current authoritative state

P1 remains active. Production contains only the original reviewed parent shard-0 recommendation data. No stale shard-1 write occurred and no V3 production mutation has been performed yet.

The corrected frozen recommendation projection is:

- candidates: **16,380**
- Movie QIDs: **6,562**
- Series QIDs: **9,818**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- authoritative projection run: **`35421313646`**

This fingerprint supersedes the obsolete 14,115-title / 8-shard production-population contract.

## Locked source contract

Only explicit Wikidata relationships are admissible for P1 recommendation metadata:

- `P136` — genre
- `P57` — director
- `P170` — creator, Series only
- `P161` — cast member

No title text, country, language, script, page category, popularity, or model inference may create canonical genre/credit relationships.

## Reviewed media-identity corrections

The production recapture surfaced two Movie/Series QID collisions. Both were reviewed against explicit Wikidata type evidence before any stale write was allowed:

- **`Q3049630` — Eko Eko Azarak**: non-audiovisual manga-series identity; excluded from Movie and Series recommendation projection.
- **`Q3146368` — Shattered City: The Halifax Explosion**: reviewed miniseries identity; canonicalized to **Series**.

The durable registry is `data/quality/media_identity_corrections.json`, consumed by `scripts/media_identity_corrections.py`. Unknown or unreviewed Movie/Series collisions remain hard failures.

The common movie SQL generator also consults this registry so reviewed non-movie identities cannot silently re-enter through future Wikidata catalogue growth.

## Schema and quota guard

Migration `0021_recommendation_metadata_foundation.sql` defines:

- `recommendation_titles`
- `genres`
- `people`
- `title_genres`
- `title_credits`

Migration `0022_recommendation_materialization_daily_guard.sql` defines the single-row-per-UTC-day D1 write reservation. Its legacy `shard_index` range remains `0..7`; V3 uses it only as a guard slot while binding the exact operation into `workflow_run_id` as `<controller-run-id>:<operation>`.

P1 still owns migrations **0021** and **0022**. Do not add `0023+` to `main` until P1 closes unless the P1 plan is explicitly revised.

## Historical source-yield evidence

The original read-only source-yield audits remain useful for coverage context but are not current production locks:

- global audit run: **`35204375729`**
- India cohort audit run: **`35204143430`**

They established sufficient explicit `P136` / `P57` / Series `P170` / `P161` yield to proceed without inventing a composite quality score or inferred metadata.

## Immutable parent materialization

The first complete reviewed materialization remains preserved as immutable evidence:

- run: **`35252106776`**
- analysis commit: **`0e319f86a4a9c7ca085de93bb5b3246606b7d6d0`**
- candidates: **14,115**
- Movie QIDs: **5,235**
- Series QIDs: **8,880**
- parent projection SHA-256: **`4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448`**
- genre relationships: **13,689**
- credit relationships: **58,069**
- production mutation: **false**

Exact manifest lineage against the corrected projection proved:

- unchanged reusable identities: **14,114**
- newly added identities: **2,266**
- removed identities: **1**
- removed QID: **`Q3049630` only**
- changed common entries: **0**

Therefore the rebaseline reused immutable parent evidence and queried Wikidata only for the 2,266-title delta.

## Delta materialization — COMPLETE

Workflow: `P1 Rebaseline Materialization V2`  
Run: **`35421562708`**  
Production mutation: **false**

All eight logical delta shards completed successfully. Shard 3 initially stopped on persistent Wikidata `maxlag`; only that failed job was retried, and the targeted retry succeeded.

Final delta evidence:

- candidate titles: **2,266 / 2,266**
- missing title entities: **0**
- skipped relationships because of missing labels: **0**
- unusable claims: **5**
- delta shard-0 production top-up estimate: **15,531 D1 rows written**

The merged read-only delta artifact is `recommendation-metadata-materialization-v2-rebaseline` from run `35421562708`.

## Authoritative V3 materialization — COMPLETE / READ-ONLY

Workflow: `P1 Repartition Materialization V3`  
Run: **`35428784454`**  
Analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**  
Artifact: `recommendation-metadata-materialization-v3-repartitioned`  
Production mutation: **false**

The V3 assembly reconstructed the reviewed parent+delta graph, removed only the reviewed `Q3049630` identity, and repartitioned the exact current graph into 16 physical QID-modulo shards without another Wikidata pass.

Authoritative normalized graph:

- recommendation titles: **16,380**
- distinct genres: **612**
- distinct people: **37,964**
- title-genre relationships: **16,489**
- title-credit relationships: **70,551**
- global materialization graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**

The artifact additionally attests every reviewed shard JSON, reviewed SQL, D1-compatible executable SQL, write-cost manifest, and the preserved shard-0 top-up. Final artifact-attestation SHA-256:

**`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**

`scripts/verify_p1_v3_production.py` reconstructs the normalized production graph and requires the complete production graph SHA-256 to equal the reviewed V3 graph. Final verification therefore does not rely on counts alone.

## V3 quota-safe production plan

The old 8-way write plan is retired. Parent shard 0 already present in production corresponds exactly to physical modulo-16 partitions **0 and 8**, so those inherited rows are not rewritten.

Production operations are:

1. one delta-only top-up for the already-present parent shard-0 identities
2. full physical shards **1–7 and 9–15**

Exact V3 write-cost estimates:

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

Largest remaining write: **49,159 rows**, well below P1's conservative **80,000 rows/UTC-day** ceiling and below the 100,000 Free daily allowance used by this plan.

## Reviewed source cleanup — GATED / NOT YET EXECUTED

Catalogue Quality V1 audits the physical source graph, not only the corrected recommendation projection. The two reviewed source collisions therefore must be physically cleaned before final P1 verification can reach S0 = 0.

`.github/workflows/p1-reviewed-source-identity-cleanup.yml` is a fail-closed main-only workflow that deletes exactly these three non-canonical rows:

- `movies / wd-Q3049630`
- `series_titles / series-wd-Q3049630`
- `catalogue_titles / wd-Q3146368`

It must retain canonical `series_titles / series-wd-Q3146368`.

The workflow requires the exact expected pre-state, an operation-bound UTC-day quota guard token, exact post-state, and a recaptured recommendation projection that remains byte-identical at SHA `f26f6218...`. The cleanup has **not** been executed yet.

## V3 production orchestration — IMPLEMENTED / NOT YET MERGED TO MAIN

`.github/workflows/recommendation-metadata-production-write-v3.yml` is the graph-attested production worker. It requires:

1. `main` branch and explicit production authorization
2. successful immutable V3 analysis run `35428784454`
3. V3 analysis commit ancestry
4. exact artifact-attestation SHA
5. exact projection SHA and graph SHA
6. exact executable-file SHA for the selected operation
7. reviewed source cleanup already complete
8. exact live corrected projection recaptured before every write
9. operation-bound UTC-day quota guard ownership
10. selected operation must be exactly `not_started` before mutation
11. selected operation must become exactly `complete` after mutation
12. zero orphan relationships and zero invalid provenance after every write
13. final normalized graph must equal graph SHA `9a931b9a...`
14. final Catalogue Quality V1 must have **S0 = 0 / S1 = 0**

`.github/workflows/p1-quota-safe-daily-resume.yml` is the replacement V3 controller. Its ordered state machine is:

1. refuse a second mutation on an already-reserved UTC day
2. perform the reviewed three-row source cleanup first if still needed
3. then process `topup, 1,2,3,4,5,6,7,9,10,11,12,13,14,15`
4. hard-stop on partial/overfilled state
5. enforce the attested ≤80k write cost
6. bind the exact operation into the daily guard token
7. dispatch exactly one V3 mutation per eligible UTC day
8. after all operations, dispatch read-only final graph/catalogue verification
9. retire itself only after a successful final verification artifact exists

The background write coordinator is also updated to keep catalogue-growth writers paused until the **V3** final-verification artifact succeeds. Only then may those writers resume.

## Existing production recommendation state

The only recommendation materialization currently present in production remains the original parent shard 0 from writer run **`35323383185`**:

- recommendation titles: **1,744**
- genres: **235**
- people: **6,184**
- title-genre relationships: **1,641**
- title-credit relationships: **6,931**
- D1 rows written: **65,299**
- orphan/provenance violations: **0**

No V3 source cleanup, top-up, or physical-shard write has been executed as of this status update.

## Automation safety state

Catalogue mutation workflows remain paused by `.github/workflows/p1-background-write-coordinator.yml`.

The obsolete 14,115-title / 8-shard scheduled resume was frozen on `main` through PR #33, merge `0633f7d8fa400e1ad1805a2e0ed93e31fab8ac47`. The rebaseline branch now replaces that legacy controller contract with the V3 state machine described above; it must not be merged until CI and workflow-contract review are green.

`P1 Repartition Materialization V3` has been restored to **manual-only** after the one-time read-only assembly run. There is no branch push trigger left in its final workflow contract.

## Remaining P1 gates

1. ~~lock reviewed media-identity corrections~~ ✅
2. ~~freeze stale catalogue / old daily-write paths~~ ✅
3. ~~materialize all 2,266 new identities~~ ✅
4. ~~assemble and attest exact 16,380-title V3 graph~~ ✅
5. ~~derive 16-way quota-safe write plan~~ ✅
6. finish V3 orchestration CI / contract review
7. merge PR #32 with V3 analysis ancestry preserved
8. execute reviewed source cleanup on its own reserved UTC quota day
9. execute top-up and remaining 14 physical shards, one operation per eligible UTC day
10. run final exact graph verification
11. require Catalogue Quality V1 **S0 = 0 / S1 = 0**
12. record final production evidence and mark P1 COMPLETE

## P1 exit rule

P1 exits only after the full corrected 16,380-title reviewed recommendation metadata foundation is present in production, the production graph exactly matches the reviewed V3 graph, referential/provenance checks pass, reviewed source identity cleanup is complete, and post-write catalogue quality remains S0/S1 clean. P2/onboarding does not begin from a partial materialization.
