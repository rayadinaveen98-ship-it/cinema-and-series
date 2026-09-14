# Cinema and Series Control Room — Information Architecture

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Product role

The **Control Room** is the private operational website used to supervise Cinema and Series data engines, review exceptions, inspect evidence, correct identities, monitor source health and understand catalogue quality.

It is not a manual movie-entry CMS and must not require approval of routine high-confidence ingestion.

## Primary operator goals

1. Know whether the data platform is healthy.
2. See what changed today.
3. Review only items that automation cannot safely resolve.
4. Understand why the system believes a fact.
5. Correct mistakes without destroying history.
6. Measure catalogue coverage and source quality.
7. Suspend/problem-isolate a source or engine quickly.

## Top-level navigation

### 1. Overview
Operational command center.

Modules:
- total catalogue counts;
- changes today;
- automated resolutions;
- review queue counts;
- source/engine incidents;
- ingestion throughput;
- upcoming-release freshness;
- CAS Coverage summary;
- recent high-impact canonical changes.

### 2. Catalogue
Browse and inspect canonical entities.

Subsections:
- Works;
- Series;
- Seasons;
- Episodes;
- People;
- Companies;
- Franchises/relationships;
- Releases;
- Certifications.

Catalogue screens are primarily investigative. Direct editing must create auditable claims/actions rather than overwrite raw values.

### 3. Discoveries
Leads found by Discovery Engine.

Views:
- new works;
- upcoming projects;
- title reveals;
- production changes;
- release changes;
- cast/crew changes;
- relationship candidates;
- certification discoveries;
- media/artwork candidates.

### 4. Review Queue
Unified human exception queue.

Queue types:
- identity/duplicate review;
- conflict review;
- release verification;
- work-vs-version/dub/remake classification;
- relationship review;
- person/company disambiguation;
- canonical override review;
- suspicious/stale data;
- media rights review.

Each item has severity, age, reason, evidence summary and recommended action.

### 5. Sources
Source governance and operations.

Subsections:
- Source Registry;
- licensing/policy status;
- adapters;
- source health;
- quotas/rate limits;
- source field coverage;
- trust/reliability metrics;
- schema drift/incidents;
- fallback sources.

### 6. Jobs & Engines
Operational processing.

Views:
- active jobs;
- scheduled jobs;
- retries;
- dead-letter queue;
- engine throughput;
- backlog;
- last successful run;
- parser/normalizer/canonicalization versions;
- reprocessing tools (privileged).

### 7. Quality
Catalogue health.

Subsections:
- CAS Coverage;
- missing metadata;
- stale upcoming titles;
- invalid state transitions;
- duplicate risk;
- conflicting fields;
- orphan relations;
- missing native titles;
- release-date anomalies;
- source disagreement heatmap;
- benchmark/validation corpus results.

### 8. Artwork & Media
Separate media operations.

Views:
- candidate assets;
- approved assets;
- blocked/unusable assets;
- missing artwork;
- source/rightsholder/license evidence;
- attribution requirements;
- duplicate/near-duplicate media;
- quality/resolution checks.

### 9. Audit
Immutable operational history.

Views:
- canonical changes;
- admin decisions;
- merges/splits;
- overrides;
- source suspensions;
- policy changes;
- reprocessing actions;
- user/operator activity.

### 10. System
Privileged configuration and diagnostics.

Views:
- engine configuration versions;
- feature flags;
- environment health;
- queue/worker health;
- storage/database health;
- backup status;
- search index state;
- deployment/build metadata.

## Global entity inspector

Every major entity should open a common inspector layout with tabs such as:

- Summary
- Canonical Data
- Claims & Evidence
- Releases
- Credits
- Names & Localization
- Relationships
- External IDs
- Media
- Quality
- Change History

This avoids separate incompatible admin experiences for each engine.

## Universal search

Control Room search must search by:
- CAS ID;
- title/name;
- native script;
- aliases/transliterations;
- external IDs;
- source identifiers;
- person/company names;
- release IDs;
- job/discovery/claim IDs where appropriate.

## Review-item interaction model

Every review screen should answer five questions immediately:

1. **What is the system proposing?**
2. **Why is it unsure?**
3. **What evidence exists?**
4. **What would each action change?**
5. **Can the action be reversed?**

## Review actions

Depending on queue type:
- accept recommendation;
- reject recommendation;
- choose claim as canonical;
- mark unresolved;
- request/queue additional evidence;
- merge entities;
- keep separate;
- split prior merge;
- classify as dub/version/remake/new work;
- correct relationship;
- suspend source-derived claim;
- create editor-backed claim with reason;
- escalate.

All privileged actions require reason/audit metadata where material.

## Design philosophy

The Control Room should feel like a premium professional data operations console, not a consumer entertainment site.

Principles:
- dense but readable;
- evidence-first;
- keyboard-friendly for repetitive review;
- strong status hierarchy;
- minimal decorative UI;
- tables where comparison matters;
- side-by-side evidence when resolving conflicts;
- persistent entity context during review;
- color never used as the only status signal;
- destructive/reversible actions clearly distinguished.

## What must not happen

- No giant manual `Add Movie` form as the primary ingestion workflow.
- No one-click silent canonical overwrite.
- No merge without preview and audit record.
- No artwork approval without rights/provenance context.
- No source activation without registry/policy status.
- No confidence percentage without explainable underlying evidence/rules.

## V1 Control Room success condition

A small operator team should be able to supervise a very large automated catalogue by focusing on exceptions, while every material decision remains explainable and recoverable.
