# Quality Engine Specification

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Purpose

The Quality Engine continuously evaluates catalogue health. It does not decide whether cinema is "good"; it detects whether **our data** is incomplete, stale, contradictory, suspicious or structurally invalid.

## Quality dimensions

### Identity quality
Detect:
- likely duplicate works/people/companies;
- conflicting external-ID mappings;
- impossible merge patterns;
- one external identity mapped to multiple incompatible CAS entities;
- suspiciously similar entities created close together.

### Metadata completeness
Detect missing/unknown priority fields by entity type and cohort. Missing must remain distinct from `unknown`, `not applicable` and `conflicting`.

### Provenance quality
Detect:
- canonical facts without admissible claims;
- claims without source/evidence linkage where required;
- stale policy references;
- unsupported editor overrides;
- claims produced by retired/broken parser versions requiring review.

### Release quality
Detect:
- scheduled date in the past with no actual-release resolution;
- impossible date ordering;
- duplicated release events;
- territory/version ambiguity;
- conflicting same-context release dates;
- release event attached to incompatible work/version.

### Production lifecycle quality
Detect:
- invalid transitions;
- stale active states;
- released work still marked pre-production/filming;
- cancelled/shelved project with active future release event without explanation;
- state changes unsupported by evidence.

### Localization quality
Detect:
- missing native/original title for priority cohorts;
- transliteration incorrectly replacing native title;
- duplicated aliases;
- language/territory mismatch;
- script mismatch for claimed language;
- suspicious machine-generated aliases promoted as official.

### Credits quality
Detect:
- duplicate credits;
- impossible/contradictory person mappings;
- malformed departments/jobs;
- broken series/episode credit inheritance assumptions;
- billing/order anomalies where source provides ordering.

### Relationship quality
Detect:
- self-referential relationships;
- contradictory reciprocal edges;
- remake loops;
- sequel/prequel cycles that violate expected direction;
- version incorrectly represented as remake/new work;
- orphan franchise/universe membership.

### Media quality
Detect:
- missing provenance/usage status;
- exact/near duplicates;
- corrupt/unsupported files;
- insufficient resolution for intended usage;
- artwork attached to wrong entity;
- approved asset whose rights/policy review expired or changed.

### Source quality
Track:
- uptime/fetch success;
- schema drift;
- disagreement rate by field;
- correction/reversal rate;
- freshness lag;
- duplicate/noise rate;
- policy status.

## Finding model

Each quality finding records:
- finding_id;
- rule_id/version;
- severity;
- entity/source/job scope;
- first_seen_at;
- last_seen_at;
- current state;
- evidence/context;
- recommended action;
- auto-fix eligibility;
- review/audit linkage.

## Finding states

`OPEN -> ACKNOWLEDGED -> FIX_IN_PROGRESS -> RESOLVED`

Possible alternate states:

`FALSE_POSITIVE`, `ACCEPTED_EXCEPTION`, `SUPPRESSED_UNTIL`, `OBSOLETE`.

Suppressions require reason and expiry/review policy for important rules.

## Severity

- **S0 Critical** — data integrity/policy/security issue that may require stopping ingestion or public projection.
- **S1 High** — material identity/canonical error or widespread source regression.
- **S2 Medium** — significant quality problem affecting a limited cohort.
- **S3 Low** — completeness/cleanup opportunity with low immediate user impact.

## Auto-fix policy

The Quality Engine may auto-fix only when a separate validated rule explicitly authorizes the action and it is reversible/auditable. It must never auto-merge uncertain identities or fabricate missing values.

Typical safe automated actions may include:
- rebuild a derived search projection;
- normalize a deterministic formatting representation while preserving raw claim;
- re-run canonicalization after new evidence;
- deduplicate identical derived index entries;
- queue a stale entity for refresh.

## CAS Coverage integration

Quality findings and CAS Coverage are related but distinct:
- **Coverage** measures how much of expected metadata/evidence is present.
- **Quality** measures whether present data is trustworthy/consistent/valid.

A catalogue can be highly complete but low quality, or sparse but internally correct.

## Cohort analysis

Every rule should be filterable by meaningful cohorts:
- language;
- country/market;
- era/year;
- work type;
- released/upcoming/historical;
- source;
- ingestion/parser version.

This prevents global averages from hiding weak regional cinema coverage.

## Control Room requirements

Quality screens must provide:
- trend over time;
- counts by severity/rule/cohort;
- oldest unresolved findings;
- regression detection after releases/parser changes;
- source disagreement heatmaps;
- direct jump to affected entity/evidence/job;
- bulk re-evaluation after rule fixes;
- benchmark corpus status.

## V1 quality gate

The V1 freeze must define numerical thresholds for critical validation categories. Exact thresholds remain OPEN until the evidence-labeled validation corpus exists; they must not be invented after implementation simply to make tests pass.
