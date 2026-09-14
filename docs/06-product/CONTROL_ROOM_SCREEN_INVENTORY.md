# Control Room Screen Inventory

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

This inventory defines the required private/admin surfaces before UI design begins. Screen IDs are stable references for product/design/QA discussion.

## Overview

| ID | Screen | Purpose |
|---|---|---|
| CR-001 | Operations Overview | Daily command center: catalogue counts, changes, review queues, incidents, coverage and recent high-impact changes. |
| CR-002 | Activity Timeline | Chronological view of engine runs, ingestion waves, canonical changes and admin actions. |
| CR-003 | Incident Center | Active source/engine/data-quality incidents with severity, ownership and resolution history. |

## Catalogue

| ID | Screen | Purpose |
|---|---|---|
| CR-100 | Work Catalogue | Filter/search all works and inspect core status/quality. |
| CR-101 | Series Catalogue | Series-specific catalogue view. |
| CR-102 | Episode Browser | Season/episode hierarchy and anomalies. |
| CR-103 | People Catalogue | People identities, aliases, credits and duplicate risk. |
| CR-104 | Company Catalogue | Production/distribution/broadcast/streaming company identities. |
| CR-105 | Release Catalogue | Release events across territory, language, format and platform. |
| CR-106 | Relationship Graph | Remake/sequel/adaptation/franchise/universe/anthology graph inspection. |
| CR-107 | Entity Inspector | Common detailed inspector for any entity. |
| CR-108 | Canonical Data Tab | Current selected/derived canonical facts and their selection rules. |
| CR-109 | Claims & Evidence Tab | All supporting/conflicting claims with source snapshots/references. |
| CR-110 | Names & Localization Tab | Native, localized, translated, transliterated and alias names. |
| CR-111 | Change History Tab | Canonical/history timeline for the selected entity. |

## Discoveries

| ID | Screen | Purpose |
|---|---|---|
| CR-200 | Discovery Inbox | All discovered leads before/while downstream processing. |
| CR-201 | New Work Candidates | Potential new movies/series/episodes. |
| CR-202 | Upcoming Project Changes | Announcements, working titles and production-state changes. |
| CR-203 | Release Change Discoveries | New/postponed/cancelled/changed release signals. |
| CR-204 | Credit Change Discoveries | Cast/crew additions or corrections. |
| CR-205 | Relationship Discoveries | Possible remakes, sequels, adaptations, franchise links. |

## Review Queue

| ID | Screen | Purpose |
|---|---|---|
| CR-300 | Unified Review Queue | Prioritized list of human-required exceptions. |
| CR-301 | Identity / Duplicate Review | Same-vs-different entity decisions with side-by-side evidence. |
| CR-302 | Conflict Review | Competing claims for one fact/field. |
| CR-303 | Release Verification | Date/territory/version/platform conflict resolution. |
| CR-304 | Work vs Version vs Dub vs Remake Review | Resolve manifestation boundaries. |
| CR-305 | Person / Company Disambiguation | Resolve same-name/pseudonym/entity mapping ambiguity. |
| CR-306 | Relationship Review | Validate or reject graph relationships. |
| CR-307 | Canonical Override Review | Privileged editor-backed canonical correction with reason/evidence. |
| CR-308 | Merge Preview | Exact consequences before merging entities. |
| CR-309 | Split / Merge Recovery | Reverse incorrect prior merges safely. |

## Sources

| ID | Screen | Purpose |
|---|---|---|
| CR-400 | Source Registry | Master list of candidate/approved/suspended/deprecated sources. |
| CR-401 | Source Detail | Access method, allowed fields, terms status, attribution, cadence, trust and fallback. |
| CR-402 | Licensing / Policy Matrix | Production eligibility and legal/terms review state. |
| CR-403 | Source Health | Availability, last success, error rate, latency and schema drift. |
| CR-404 | Source Reliability | Field-specific agreement/correction statistics. |
| CR-405 | Quota / Rate Limit | Consumption, remaining quota and throttling state. |
| CR-406 | Adapter Configuration | Privileged adapter configuration excluding secrets. |

## Jobs & Engines

| ID | Screen | Purpose |
|---|---|---|
| CR-500 | Engine Overview | Health and throughput by logical engine. |
| CR-501 | Job Queue | Pending/running/completed jobs. |
| CR-502 | Retry Queue | Retryable failures and next attempt. |
| CR-503 | Dead-Letter Queue | Exhausted/non-retryable jobs needing investigation. |
| CR-504 | Job Detail | Inputs, policy/version, logs, outputs and affected entities. |
| CR-505 | Reprocess Tool | Privileged targeted reparse/reconcile/reindex without source mutation. |
| CR-506 | Engine Version History | Parser/normalizer/rule versions and deployment history. |

## Quality

| ID | Screen | Purpose |
|---|---|---|
| CR-600 | Quality Overview | Aggregate data health and CAS Coverage. |
| CR-601 | Missing Metadata | Prioritized missing-field cohorts. |
| CR-602 | Stale Data | Upcoming/active productions or availability data beyond freshness threshold. |
| CR-603 | Duplicate Risk | Machine-detected likely duplicate clusters. |
| CR-604 | Conflict Heatmap | Disagreement by source, field, language, market and era. |
| CR-605 | Structural Anomalies | Invalid transitions, orphan links, impossible dates, broken hierarchies. |
| CR-606 | Localization Gaps | Missing native titles, aliases/transliterations and market labels. |
| CR-607 | Validation Corpus | Benchmark case status and pass/fail evidence. |
| CR-608 | Coverage Explorer | Coverage by language, country, era, work type and metadata dimension. |

## Artwork & Media

| ID | Screen | Purpose |
|---|---|---|
| CR-700 | Media Inbox | Candidate posters/backdrops/logos/stills/portraits. |
| CR-701 | Media Review | Asset quality + provenance/rights review. |
| CR-702 | Missing Artwork | Works/people without approved display media. |
| CR-703 | Media Rights Ledger | Source/rightsholder/license/attribution/usage status. |
| CR-704 | Duplicate Media | Exact/near-duplicate detection and asset consolidation. |

## Audit & System

| ID | Screen | Purpose |
|---|---|---|
| CR-800 | Audit Log | Material automated/admin actions. |
| CR-801 | Merge/Split History | Identity operation audit and recovery entry point. |
| CR-802 | Canonical Change Log | Field-level canonical history across catalogue. |
| CR-803 | Policy Change Log | Source/rule/policy changes and effective dates. |
| CR-900 | System Health | DB, workers, queues, storage, search/index and dependencies. |
| CR-901 | Backup / Recovery Status | Backup health, last restore test and RPO/RTO signals. |
| CR-902 | Feature Flags | Privileged rollout switches. |
| CR-903 | Build / Deployment Info | Current service/client versions and commit/deploy metadata. |

## Global utilities

Available throughout the Control Room:
- universal search;
- CAS ID copy/open;
- source/evidence quick peek;
- keyboard command palette;
- territory/locale context selector where relevant;
- saved filters/views (post-foundation implementation detail);
- direct link to audit history;
- queue navigation (next/previous review item).

## V1 design requirement

Every listed screen must either be explicitly included in V1, deferred with rationale, or merged into another screen during the frozen UX specification. No production designer/developer should silently remove workflows because a screen seems complex.
