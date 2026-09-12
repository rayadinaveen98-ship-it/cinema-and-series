# Identity Resolution Specification — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Identity Resolution decides whether source records refer to the same real Work, Person, Organization, Version, Season, Episode, ReleaseEvent or other entity.

This is one of the highest-risk systems in Cinema and Series. A false duplicate is inconvenient; a false merge can corrupt credits, release history, external IDs and relationships across the entire platform.

## Core policy

**When uncertain, prefer temporary separation + review over destructive merge.**

## Identity pipeline

```text
Source record
 -> normalize
 -> candidate generation
 -> feature comparison
 -> hard-rule checks
 -> match classification
 -> auto-link / create / review
 -> audit history
```

## Match outcomes

- `EXACT_MATCH`
- `HIGH_CONFIDENCE_MATCH`
- `POSSIBLE_MATCH_REVIEW`
- `DISTINCT_ENTITY`
- `INSUFFICIENT_EVIDENCE`
- `BLOCKED_BY_CONTRADICTION`

Do not expose arbitrary probability scores to users unless calibrated. Internal models may use scores to rank candidates, but hard invariants and review thresholds govern actions.

# Work identity

## Candidate-generation signals

Generate plausible candidates using combinations of:
- normalized titles/aliases;
- native-script forms;
- transliterations;
- release year/date windows;
- original languages;
- production countries;
- director/writer/lead cast overlap;
- production companies;
- runtime proximity with version awareness;
- external identifiers;
- franchise/series membership;
- source-record relationships.

Search candidate generation must optimize recall; final matching optimizes precision.

## Strong positive signals

- exact same trusted external identifier namespace + ID;
- provider cross-ID mapping supported by multiple sources;
- same original/native title + director + year + language;
- official source explicitly identifies alternate/localized title for the same project;
- title-change announcement linking old/new title;
- archive/provider record gives known external/canonical mapping.

## Hard contradiction examples

- same IMDb/TMDB-style namespace maps candidate records to two currently valid distinct IDs with no merge history;
- different directors + different production companies + different release years despite same title;
- one record is episode and other is unrelated feature;
- evidence proves remake rather than dub/version;
- simultaneous existence of independently produced works with same title.

A hard contradiction blocks auto-merge even when title similarity is high.

## Title normalization

Normalize for candidate generation without destroying originals:
- Unicode normalization;
- case folding where script supports it;
- punctuation/spacing normalization;
- common article handling only as ranking feature;
- transliteration aliases;
- diacritic-insensitive search feature;
- numeric/roman numeral normalization as feature;
- common provider suffix removal only through known adapter rules.

Never store normalized search text as the canonical title.

## Year/date tolerance

Year differences can arise from:
- festival vs theatrical release;
- territory release differences;
- production year vs release year;
- database errors.

Therefore `year mismatch = no match` is invalid.

Use release-event evidence and plausible windows. Large unexplained date differences reduce match confidence but do not alone prove distinction.

## Runtime

Runtime is a supporting feature only.

Different cuts, certification versions, PAL speedup, episode edits or incomplete provider data can cause differences. Runtime never overrides stronger identity evidence.

## Cast/crew overlap

Useful features:
- director exact identity;
- writer overlap;
- lead-cast overlap;
- producer/company overlap;
- cinematographer/composer where relevant.

Beware repeated director/actor collaborations and large shared franchise casts.

# Dub vs remake classifier

This classification must never depend only on title/language.

### Likely dub / same Work
- same underlying footage/production;
- same director/production identity;
- localized audio cast/title;
- distributor/platform calls it dubbed version;
- same core runtime/edit with localized credits.

### Likely remake / separate Work
- new principal photography/animation production;
- different production team/cast;
- source/rights-holder calls it remake;
- separate production/release identity;
- adaptation recreates earlier film rather than merely localizing audio.

### Ambiguous multilingual production
Route to Version-vs-Work review using official production evidence.

# Person identity

## Candidate signals
- exact external IDs/authority IDs;
- native/stage/alternate names;
- birth date/place where lawfully sourced;
- occupation;
- overlapping filmography;
- agency/official profile;
- credited-as forms;
- known name changes.

## Never auto-merge solely on
- exact name;
- initials;
- same occupation;
- same country/language.

## Same-name collision safeguards

Before person auto-merge, require at least one strong identity anchor or several independent contextual signals. Conflicting birth dates/filmographies or simultaneous distinct credits can block merge.

# Organization identity

Signals:
- official corporate/brand identity;
- external IDs;
- website/domain;
- known legal/brand aliases;
- address/jurisdiction when appropriate;
- filmography/role overlap.

Do not automatically merge:
- similarly named banners;
- label and parent company;
- distributor and production subsidiary;
- renamed successor company without evidence.

Support relationships:
- renamed_to/from;
- subsidiary_of;
- parent_of;
- acquired_by;
- brand_of.

# Series/season/episode identity

## Series
Use:
- original title;
- broadcaster/platform;
- premiere period;
- creators/lead cast;
- external IDs;
- continuity/reboot evidence.

A reboot/revival can be same or separate Series depending official continuity. Ambiguous cases require review.

## Season
Provider season numbers are mappings, not identity.

Signals:
- parent Series;
- provider IDs;
- official label/title;
- episode membership;
- release window;
- part/volume semantics.

## Episode
Signals:
- parent Series;
- official/provider ID;
- episode title;
- release date;
- season/order position;
- runtime;
- production code.

Episode numbering alone is not identity because providers disagree on specials/order.

# Version identity

Create/link Versions using:
- explicit edition/cut name;
- version-specific runtime;
- certification;
- language/dub identity;
- restoration/remaster source;
- distributor/home-media/platform evidence;
- separate release history.

Do not create new Versions simply because:
- resolution differs;
- bitrate/file codec differs;
- one platform has a different thumbnail;
- subtitles differ without version significance.

# ReleaseEvent identity

Potentially same event when:
- same Work/Version;
- same territory;
- same release type;
- same distributor/platform/venue context;
- dates are same or one clearly supersedes another schedule.

Distinct events when:
- theatrical vs streaming;
- original release vs re-release;
- festival vs general theatrical;
- materially different territory/version;
- separate festival screenings.

# External ID policy

`ExternalIdentifier` is strong evidence, not unquestionable truth.

Providers can:
- merge IDs;
- delete IDs;
- incorrectly map IDs;
- split entities.

Store:
- namespace;
- ID;
- status;
- valid interval;
- provider redirect/replacement;
- source/evidence.

If provider A merges records, do not auto-merge CAS entities until our evidence supports it.

# Match decision bands

## Auto-link / exact
Allowed when:
- trusted exact external mapping with no contradiction; or
- deterministic source-specific mapping previously validated; or
- multiple highly discriminative fields agree under locked rules.

## Auto-create new entity
Allowed when:
- no plausible candidate survives candidate search; and
- minimum identity fields/evidence threshold met.

## Human review
Required when:
- likely match but meaningful contradiction;
- dub vs remake unclear;
- multilingual production boundary unclear;
- person same-name collision;
- provider mappings disagree;
- historical titles have sparse evidence;
- project revival/reboot boundary unclear;
- merge would affect many downstream records.

# Merge mechanics

A merge must be reversible/auditable.

Required behavior:
- select survivor CAS ID;
- preserve retired CAS ID as redirect/tombstone;
- move/link claims without erasing original subject history;
- preserve external-ID provenance;
- deduplicate only when evidence supports;
- invalidate/rebuild search/canonical projections;
- record merger, reason, evidence and timestamp;
- support rollback/split workflow.

Never recycle retired IDs.

# Split mechanics

When one CAS entity is discovered to contain multiple real entities:
- create new CAS identity/identities;
- reassign claims/credits/releases/assets selectively;
- preserve original audit trail;
- update external mappings;
- re-run canonicalization;
- maintain redirects only where semantically correct;
- record impact and reviewer rationale.

Split is a first-class operation, not manual SQL surgery.

# Matching engine architecture

Recommended stages:

### 1. Normalizer
Produces searchable representations of names, dates, languages and source types.

### 2. Candidate Generator
Uses indexes/external IDs/search to return small candidate set.

### 3. Feature Extractor
Computes explainable features.

### 4. Rules/Model Scorer
Combines hard rules + weighted evidence/model.

### 5. Decision Policy
Maps result to link/create/review/block.

### 6. Review UI
Shows side-by-side evidence and affected downstream records.

### 7. Audit/Reconciliation
Executes reversible merge/split/link and triggers projection rebuilds.

## Explainability

Every automated match should retain reason codes such as:
- `EXTERNAL_ID_EXACT`
- `ORIGINAL_TITLE_EXACT`
- `DIRECTOR_MATCH`
- `YEAR_WITHIN_RELEASE_WINDOW`
- `LANGUAGE_MATCH`
- `CAST_OVERLAP_HIGH`
- `HARD_TYPE_CONTRADICTION`
- `REMAKE_EVIDENCE_PRESENT`

Reviewer should see why candidates matched.

## Machine learning policy

ML/embedding similarity may rank candidates later, but:
- training/evaluation corpus must exist;
- precision on auto-merge threshold must be extremely high;
- hard contradictions override ML;
- review explanations must remain available;
- ML is not allowed to infer unsupported identity as fact.

Start with deterministic/high-precision rules + human review before introducing ML complexity.

## Quality metrics

Track separately:
- auto-match precision;
- auto-match recall;
- false-merge rate;
- missed-duplicate rate;
- review acceptance rate;
- person-collision rate;
- dub/remake classification errors;
- external-ID conflict rate;
- merge rollback/split frequency.

**False-merge rate is the most dangerous metric and should have the strictest target.**

## Validation corpus identity challenges

Must include:
- same film with Telugu/native/English/transliterated titles;
- same title, same year, different languages;
- same title/year/language, genuinely distinct works;
- dubbed versions;
- remake networks;
- multilingual simultaneous productions;
- re-releases/restorations;
- TV specials numbered differently by providers;
- rebooted series;
- identical person names;
- stage-name changes;
- production-company aliases;
- working-title changes;
- cancelled/revived projects;
- sparse silent-film records;
- external provider ID merges/remaps.

## Lock criteria

Move to LOCKED only when:
- validation corpus has labeled ground truth for identity cases;
- auto-merge rules meet defined precision target;
- merges/splits are reversible;
- dub/remake/multilingual cases are handled correctly;
- person collision safeguards are tested;
- external-provider merge does not force CAS merge;
- review UX requirements are defined.
