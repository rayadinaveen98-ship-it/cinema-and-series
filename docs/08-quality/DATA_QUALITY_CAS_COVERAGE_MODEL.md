# Data Quality & CAS Coverage Model — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series must measure data quality rather than claiming vague completeness. The system should be able to state what it knows, what it does not know, how trustworthy the evidence is, how fresh volatile data is, and which catalogue slices need improvement.

## Core rule

**Coverage is multidimensional and slice-specific. There is no honest single percentage for "every movie in the world."**

## Quality dimensions

### 1. Identity Coverage
Can we uniquely identify the Work/entity without unresolved duplicate risk?

Signals:
- CAS ID exists;
- minimum identity fields;
- strong source/external mappings;
- no unresolved high-risk duplicate candidate;
- WorkKind resolved.

### 2. Core Metadata Coverage
Availability of essential descriptive facts such as:
- titles;
- original language;
- production country;
- WorkKind;
- principal release/year context;
- runtime where appropriate;
- production companies;
- genres/synopsis if V1 requires them.

### 3. Credits Coverage
Measured separately by role groups:
- director;
- writers;
- principal cast;
- full cast;
- producers;
- camera;
- editing;
- music;
- India-deep craft roles;
- episode-specific credits.

Do not equate "has director" with "credits complete".

### 4. Release Coverage
Measures:
- existence of release history;
- territory coverage;
- planned vs actual status;
- India release details;
- festival/premiere evidence;
- re-release/version history;
- release provenance.

### 5. Localization Coverage
Measures:
- native/original title;
- localized titles;
- transliterations;
- script tagging;
- language tagging;
- territory-specific naming.

### 6. Provenance Coverage
Measures whether canonical data can be traced to eligible evidence.

Important P0/P1 canonical facts should target 100% provenance coverage by design.

### 7. Relationship Coverage
Measures supported sequel/prequel/remake/adaptation/franchise/version relationships where expected.

### 8. Lifecycle Coverage
For current/future Works:
- production state evidence;
- announcement history;
- date-change history;
- freshness.

### 9. Asset Coverage
Measures separately:
- publishable poster;
- localized poster;
- person portrait;
- trailer;
- rights basis completeness.

Asset coverage never determines whether the Work itself exists in the catalogue.

### 10. Freshness
Applies to volatile fields such as:
- streaming availability;
- showtimes;
- future release dates;
- production status.

Stable historical facts use different freshness expectations.

### 11. Conflict Health
Measures:
- unresolved credible conflicts;
- conflict age;
- fields blocked by conflict;
- review backlog.

Conflict is not automatically poor quality; hiding a real conflict is worse.

## CAS Coverage

`CAS Coverage` is the name for our structured quality profile. It should **not** initially be represented as one misleading consumer-facing 0–100 score.

Example internal profile:

```text
Work CAS...
Identity             Complete / High evidence
Core Metadata        92%
Principal Credits   100%
Extended Credits     74%
Release History      88%
Localization         80%
Provenance          100% of P0/P1 fields
Relationships        67%
Publishable Assets   Poster yes / trailer yes / stills no
Freshness            Current
Conflicts             1 unresolved historical date
```

A future composite score may be used internally for prioritization only after weights are validated.

## Requiredness profiles

Completeness depends on entity type and lifecycle.

### Released feature film P0 fields
Proposed minimum:
- CAS identity;
- WorkKind;
- at least one reliable title;
- original/native title when knowable;
- original language(s) or explicit unknown;
- production country or explicit unknown;
- at least one release/history fact or explicit historical unknown;
- director or explicit unknown when evidence exhausted;
- provenance for all populated P0 fields.

### Upcoming announced feature
Different minimum:
- project identity;
- official/strong existence evidence;
- current lifecycle status;
- at least one title/working title;
- production company/creator/cast only as supported;
- release date may be UNKNOWN.

A missing date must not make an announced project "incomplete" in the same way as an unsupported guessed date.

### Series
Additional requirements:
- Series identity;
- status;
- season/episode hierarchy as known;
- episode identity/release metadata;
- broadcaster/platform context where supported.

### Historical/lost work
Requiredness adapts to scarcity:
- year-only dates accepted;
- unknown credits accepted;
- archive/lost-status evidence valued;
- evidence notes/conflict states matter more than modern artwork.

## Data-state distinctions

Each field/domain must distinguish:
- `KNOWN`
- `UNKNOWN_AFTER_RESEARCH`
- `MISSING_NOT_YET_RESEARCHED`
- `NOT_APPLICABLE`
- `CONFLICTING`
- `UNVERIFIED`
- `STALE`
- `WITHHELD_BY_POLICY` where necessary

SQL NULL alone cannot communicate these semantics to quality tooling.

## Catalogue slice metrics

Coverage reports must support slicing by:
- country;
- original language;
- script;
- era/decade/year;
- WorkKind;
- released/upcoming/historical state;
- source/provider dependency;
- territory;
- genre where useful;
- Indian cinema tradition/market as a discovery dimension;
- series vs film.

Example:

```text
Telugu feature films, 2010–2026
Known Work coverage benchmark: 94%
Director: 98%
Principal cast: 96%
Extended crew: 72%
India release-date evidence: 93%
Native title: 99%
P0 provenance: 100%
Publishable poster: 61%
```

The denominator must always be defined by a benchmark/source corpus; never imply absolute world completeness without a defensible denominator.

## Benchmark denominators

Potential denominator strategies:

### Closed benchmark set
A manually curated/listed collection with known members. Best for testing.

### Authority corpus
All records in an archive/registry within a documented scope.

### Multi-source union estimate
Union of several sources after deduplication. Useful operationally but not absolute truth.

### Capture-recapture/statistical estimate
Possible future research method to estimate unseen catalogue size; not needed for V1.

Public coverage claims must state denominator/methodology.

## Quality issue taxonomy

### Identity
- POSSIBLE_DUPLICATE
- FALSE_MERGE_SUSPECTED
- EXTERNAL_ID_CONFLICT
- PERSON_COLLISION

### Evidence
- CANONICAL_WITHOUT_SUPPORT
- LOW_AUTHORITY_ONLY
- SOURCE_POLICY_INVALID
- EVIDENCE_LOCATOR_BROKEN

### Release
- SCHEDULE_PASSED_NO_OCCURRENCE
- RELEASE_DATE_CONFLICT
- TERRITORY_MISSING
- VERSION_MISMATCH
- RE_RELEASE_OVERWROTE_ORIGINAL

### Credits
- PRINCIPAL_ROLE_MISSING
- DUPLICATE_CREDIT
- ANNOUNCED_VS_FINAL_CONFLICT
- JOB_NORMALIZATION_UNKNOWN

### Localization
- NATIVE_TITLE_MISSING
- GENERATED_TRANSLITERATION_MARKED_OFFICIAL
- SCRIPT_LANGUAGE_CONFLICT
- DUPLICATE_ALIAS

### Lifecycle
- STATUS_STALE
- RELEASED_WITHOUT_RELEASE_EVENT
- RUMOR_PROMOTED_WITHOUT_THRESHOLD
- IMPOSSIBLE_EVENT_ORDER

### Assets
- RIGHTS_BASIS_MISSING
- LICENSE_EXPIRED
- ATTRIBUTION_MISSING
- TAKEDOWN_PENDING

### Availability
- OFFER_STALE
- TERRITORY_MISSING
- PROVIDER_UNKNOWN

## Severity levels

- `CRITICAL` — can corrupt identity/legal compliance/public truth; e.g. false merge, unauthorized asset.
- `HIGH` — important P0/P1 wrong/missing fact or strong conflict.
- `MEDIUM` — non-core completeness/normalization issue.
- `LOW` — enrichment opportunity/cosmetic issue.

## Automated quality rules

Examples:
- every public Work has exactly one active CAS identity;
- every P0 canonical fact has supporting eligible Claim;
- no public Asset lacks publication-approved rights state;
- no ExternalIdentifier maps to two active CAS entities without conflict record;
- released status requires occurred ReleaseEvent;
- future event with date in past triggers occurrence/postponement review;
- generated transliteration cannot have official-source flag;
- Certification authority/territory required;
- ReleaseEvent territory required except approved global event class;
- Episode must belong to Series;
- Version must belong to Work;
- manual override must have rationale;
- stale AvailabilityOffer is excluded from current projection.

## Source dependency concentration

Quality includes resilience.

Track for important domains:
- percent canonical facts supported by only one provider;
- percent catalogue identities dependent on one external mapping;
- percent artwork from one provider;
- percent current availability from one partner.

High concentration becomes a platform-risk metric even when data is accurate.

## Freshness SLA concepts

Proposed classes:
- F0 live: minutes/hours;
- F1 daily;
- F2 weekly/event-driven;
- F3 stable periodic/change-driven;
- F4 archival correction-driven.

Report stale percentage by field/source.

## Human-review metrics

Track:
- queue size;
- oldest task age;
- tasks by severity/type;
- resolution time;
- automatic suggestion acceptance rate;
- false-positive review rate;
- reopen rate.

Backlog growth can expose a broken automation/source strategy.

## Ingestion quality metrics

Per adapter:
- acquisition success rate;
- parser success rate;
- schema-change failures;
- invalid observation rate;
- identity unresolved rate;
- claim rejection rate;
- later correction/supersession rate;
- source latency/freshness;
- rate-limit incidents.

## Identity quality targets

Exact numeric thresholds should be frozen after corpus testing, but policy direction is:
- auto-merge precision must be extremely high;
- false merges are more costly than missed duplicates;
- consumer search can tolerate much higher recall-oriented ambiguity than identity resolution.

## Public quality communication

Potential later user-facing indicators:
- Official / Confirmed / Conflicting evidence badge;
- source drawer;
- last verified date for volatile data;
- "information incomplete" for historical records;
- correction/contribution action.

Do not show misleading internal percentages without context.

## Quality dashboard requirements

Admin dashboard should provide:
- catalogue totals by WorkKind/language/country;
- new Works/day;
- duplicate candidates;
- P0 provenance failures;
- source health;
- release/status stale queues;
- conflict backlog;
- rights issues;
- coverage heatmap by language/year;
- India regional-cinema coverage;
- provider concentration;
- validation-corpus regression score.

## Regression policy

Every engine/schema change reruns validation corpus and quality rules.

Block release/merge of implementation if it materially worsens:
- false-merge rate;
- P0 provenance;
- core search recall by target script;
- release accuracy;
- source-policy compliance;
- rights-gate integrity.

## Lock criteria

Move to LOCKED only when:
- V1 requiredness profiles are finalized;
- validation corpus denominator exists;
- quality checks are mapped to schemas/engines;
- target thresholds are defined from benchmark results;
- admin dashboard requirements are accepted;
- public/internal quality terminology is unambiguous.
