# Entity Model & Conceptual ERD — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

This document defines the conceptual entities Cinema and Series needs before any SQL schema is written. It is intentionally implementation-neutral. Table names, indexes, partitioning and physical storage are postponed until the domain model survives validation-corpus testing.

## Design rules

1. Canonical entities have Cinema and Series IDs independent of external providers.
2. Provenance is not optional metadata bolted on later; claims/evidence are part of the core model.
3. Work, Version, ReleaseEvent and AvailabilityOffer are separate.
4. Names/titles are multi-valued/localized entities, not one string column.
5. Credits are structured relationships, not JSON blobs.
6. Historical uncertainty and conflicting claims are representable.
7. Series/Season/Episode structure is first-class.
8. Assets and rights are separate from metadata.
9. Provider-specific raw data remains outside the canonical domain model.
10. Search indexes are derived projections, not authoritative storage.

# 1. Core audiovisual entities

## Work

Represents a canonical creative audiovisual work.

Key conceptual attributes:
- `work_id`
- `work_kind`
- `lifecycle_current_state` — derived/current projection, not sole history
- `original_release_year` — derived display convenience, nullable
- `is_adult`/content-policy marker only if product later requires it
- created/updated/audit metadata

Most descriptive facts such as title, language, country, runtime, genre, status and relationships should be evidenced through claims/related entities rather than uncontrolled columns.

### Work subtypes are logical, not necessarily physical tables

- Film/Short/TV Movie
- Series/Limited Series
- Episode
- Special
- Anthology Segment

The physical schema may use one Work table plus subtype structures rather than inheritance tables.

## SeriesStructure

Represents structural data specific to Series Works.

Conceptual fields:
- `series_work_id`
- ordering/numbering policies
- series status projection
- default episode order policy

## Season

Structural grouping within a Series.

Conceptual fields:
- `season_id`
- `series_work_id`
- canonical season number nullable
- season type (`STANDARD`, `SPECIALS`, `PART`, `VOLUME`, `OTHER`)
- display order

Season names and release data use normal Name/Claim/Release structures.

## EpisodeMembership

Links an Episode Work into a Series and optionally a Season.

Fields/concepts:
- `episode_work_id`
- `series_work_id`
- `season_id` nullable
- aired number nullable
- absolute number nullable
- production number nullable
- part/volume number nullable
- ordering source/policy
- evidence

Do not force a single episode numbering system.

## Version

Represents a materially identifiable realization of a Work that needs version-specific metadata.

Conceptual fields:
- `version_id`
- `work_id`
- `version_kind`
- parent/source version nullable
- primary language context nullable
- creation/restoration/remaster date precision
- version label/name through Name model
- status

Possible examples:
- original theatrical version
- Tamil simultaneously shot version
- Hindi dub with distinct voice cast/certification
- director's cut
- restored 4K version

Not every audio track/file rendition becomes a Version.

## VersionRelationship

Typed relationship between Versions/Work and Versions.

Fields:
- subject Version
- predicate/type
- object Work/Version
- claim/evidence

Examples:
- `DUBBED_VERSION_OF`
- `RESTORATION_OF`
- `EXTENDED_FROM`
- `CENSORED_FROM`
- `REMASTER_OF`

# 2. Naming and localization entities

## Name

Reusable localized naming record attached to Work, Version, Season, Person, Organization, Franchise, Character, etc.

Conceptual fields:
- `name_id`
- owner entity ID/type
- `text`
- `name_type`
- `language_code`
- `script_code`
- `territory_id` nullable
- `is_preferred`
- validity interval nullable
- evidence/claim link

Name types include:
- ORIGINAL
- CANONICAL_DISPLAY
- LOCALIZED_RELEASE
- TRANSLATED
- TRANSLITERATION
- ROMANIZATION
- ALTERNATE
- WORKING_TITLE
- FORMER_NAME
- STAGE_NAME
- CREDITED_NAME

Canonical display names are projections selected by locale rather than one immutable text field.

## Language
Reference vocabulary for languages. Prefer standards-compatible codes but support languages lacking simple ISO 639-1 codes.

Fields:
- internal language ID
- ISO 639-1 nullable
- ISO 639-2/3 where appropriate
- canonical name
- native name
- status/aliases

## Script
Reference vocabulary for writing systems, preferably ISO 15924 compatible.

## Territory
Hierarchical geographic/jurisdiction entity.

Fields:
- territory ID
- type (country, subdivision, market grouping where approved)
- parent territory nullable
- ISO codes where available

Country, release territory and rights market should reference this vocabulary rather than free text.

# 3. People, characters and organizations

## Person

Durable real-person identity.

Core fields should be minimal:
- `person_id`
- identity status
- created/updated metadata

Names, dates, biographies, occupations and external IDs are separate/evidenced facts.

## PersonName
Implemented through generic Name relation or specialized projection.

## Character

Optional/P2 durable fictional/represented character identity.

Fields:
- `character_id`
- names
- franchise/universe associations when evidenced

V1 can store character text in credits even before full Character graph coverage.

## Organization

Durable organization identity.

Organization kinds can include:
- production company
- studio
- production banner
- distributor
- broadcaster/network
- streaming platform
- music label
- post-production/VFX company
- archive
- festival
- certification authority
- rights holder
- agency
- other

The kind describes the organization; its role on a Work is represented separately.

## OrganizationRole / CompanyCredit

Links Organization to Work/Version/ReleaseEvent with role.

Examples:
- produced_by
- presented_by
- distributed_by
- financed_by
- broadcast_by
- streaming_original_of
- music_released_by
- restored_by
- VFX_by

# 4. Credit model

## Credit

Represents a sourced professional contribution by a Person or Organization.

Conceptual fields:
- `credit_id`
- `work_id`
- `version_id` nullable
- `episode_scope` naturally handled because Episode is a Work
- `person_id` or organization ID
- `department_id`
- `job_id`
- `source_job_text`
- `credited_as_name_id/text`
- `character_id/text` nullable
- `billing_order` nullable
- `is_uncredited` nullable
- `credit_status` (`ANNOUNCED`, `FINAL`, `REMOVED`, `DISPUTED`, etc.)
- claim/evidence

A pre-release announced cast member and a final on-screen credit are not automatically equivalent states.

## Department
Normalized grouping such as:
- Acting
- Directing
- Writing
- Production
- Camera
- Editing
- Music
- Lyrics
- Playback Vocals
- Choreography
- Action/Stunts
- Art/Production Design
- Costume/Makeup
- Sound
- VFX
- Post-production
- Other

## Job
Normalized role vocabulary within Department.

Keep source wording so normalization never destroys the original credit label.

# 5. Production and lifecycle entities

## ProductionEvent

Append-only historical event describing development/production state.

Conceptual fields:
- `production_event_id`
- `work_id`
- state/event type
- event date/date precision
- effective-from/effective-to where applicable
- location/company context optional
- claim/evidence

Examples:
- ANNOUNCED
- GREENLIT
- PRE_PRODUCTION_STARTED
- PRINCIPAL_PHOTOGRAPHY_STARTED
- FILMING_COMPLETED
- POST_PRODUCTION_STARTED
- COMPLETED
- ON_HOLD
- SHELVED
- CANCELLED

Current lifecycle state is derived from accepted events.

## ProductionAliasEvent

Can be represented through Name validity/history and claims; no separate table required unless validation proves useful.

# 6. Release and availability entities

## ReleaseEvent

Core entity representing planned or actual release/screening.

Conceptual fields:
- `release_event_id`
- `work_id`
- `version_id` nullable
- `territory_id`
- `release_type`
- venue/platform/distributor organization refs nullable
- language context nullable
- scheduled date + precision nullable
- actual date + precision nullable
- timezone/local-time context nullable
- status
- sequence/edition metadata nullable
- evidence/claims

ReleaseEvent status vocabulary:
- ANNOUNCED
- SCHEDULED
- POSTPONED
- CANCELLED
- OCCURRED
- UNCERTAIN

A reschedule can be modeled through claims/history/events without destroying the old scheduled date.

## ReleaseDateClaim

Can use generic Claim rather than special entity unless physical schema optimization later requires one.

## AvailabilityOffer

Temporal provider/territory offer.

Conceptual fields:
- `availability_offer_id`
- `work_id`
- `version_id` nullable
- `provider_organization_id`
- `territory_id`
- offer type (`SUBSCRIPTION`, `RENT`, `BUY`, `FREE`, `ADS`, `CHANNEL`, etc.)
- quality/audio/subtitle details where known
- observed start/end
- last verified at
- source/evidence

Availability records expire/stale independently of title metadata.

# 7. Certification and technical metadata

## Certification

Conceptual fields:
- `certification_id`
- `work_id`
- `version_id` nullable
- authority organization
- territory
- rating/code
- certificate number nullable
- issue date/date precision
- certified length/runtime nullable
- advisory/reason nullable
- claim/evidence

## RuntimeObservation / RuntimeClaim

Runtime should use generic claims with context:
- Work/Version
- runtime duration
- measurement/source
- release/certification context

Canonical runtime displayed in UI must specify/select context rather than silently average conflicting values.

## TechnicalSpecification

P2 entity/claim family for:
- color process
- aspect ratio
- sound format
- capture/film format
- stereoscopy
- frame rate

Only source when product value justifies it; never infer from posters or playback files.

# 8. Relationships, franchises and adaptations

## EntityRelationship

Generic typed relationship with provenance.

Conceptual fields:
- `relationship_id`
- subject entity type/id
- predicate
- object entity type/id
- directional flag
- validity/effective period nullable
- relationship status
- claim/evidence

Work predicates include:
- SEQUEL_OF
- PREQUEL_OF
- SPIN_OFF_OF
- REMAKE_OF
- REBOOT_OF
- ADAPTATION_OF
- BASED_ON
- CROSSOVER_WITH
- SEGMENT_OF
- COMPILATION_CONTAINS
- CONTINUES
- RELATED_TO (restricted fallback, not preferred)

## Franchise

Durable grouping identity with names/aliases and evidence-backed Work membership.

## Universe

May be separate entity or franchise attribute only after validation. Do not over-model before corpus tests.

## SourceWork / LiteraryWork

Adaptation source works (novel, play, comic, game etc.) are architecturally desirable but can be represented initially through an ExternalCreativeWork entity/P2 relationship until scope is frozen.

# 9. Genre, taxonomy and descriptive entities

## Genre
Cinema and Series controlled taxonomy.

Provider genres map to our genre vocabulary through explicit mappings/versioned rules.

## WorkGenre
Relationship between Work and Genre with evidence/normalization basis.

## Keyword / Theme
P2/Later controlled terms. Do not import proprietary provider keyword sets without rights.

## Synopsis

Conceptually a content object with:
- `synopsis_id`
- Work/Version
- locale/language
- text
- origin (`LICENSED_PROVIDER`, `RIGHTS_CLEARED_OFFICIAL`, `CAS_EDITORIAL`)
- source/evidence references
- author/process
- rights/publication status

Do not store arbitrary copied descriptions as canonical text.

# 10. Source, evidence and claim entities

## Source
Registered source definition from Source Registry.

## SourcePolicyVersion
Optional but recommended record of terms/licence/access policy observed for a source.

## SourceSnapshot
Immutable observed source payload/document reference, subject to storage rights.

Fields conceptually include:
- snapshot ID
- source ID
- provider record/URL
- retrieved at
- source publication/effective time if known
- content/payload hash
- storage/reference mode
- HTTP/provider metadata where permitted
- terms/policy version

## EvidenceLocator
Points to the precise support:
- page/line/section
- certificate number
- provider field
- JSON path
- video timestamp
- archive accession
- publication paragraph

## Observation
Parser/extractor output prior to canonical semantic resolution.

## Claim
Normalized evidence-backed proposition. Detailed in `CLAIM_PROVENANCE_MODEL.md`.

## ClaimLink
Supports relations between claims:
- corroborates
- contradicts
- supersedes
- derived_from
- duplicates
- quotes/propagates

This helps detect non-independent sources.

## CanonicalDecision
Records why a particular claim/value became current canonical projection.

# 11. External identity entities

## ExternalIdentifier

Conceptual fields:
- `external_id_record_id`
- owner CAS entity type/id
- provider/system
- identifier namespace
- external identifier
- status
- valid from/to
- redirected/replaced-by mapping
- source/evidence

Examples:
- IMDb title/name IDs
- TMDB movie/TV/person IDs
- TheTVDB IDs
- Wikidata QIDs
- EIDR IDs
- ISAN
- MusicBrainz IDs
- archive accession/catalog IDs
- platform IDs

Uniqueness is namespace-scoped and must tolerate provider merges/remaps.

# 12. Asset entities

## Asset
Defined in `ARTWORK_MEDIA_RIGHTS_STRATEGY.md`.

## AssetRelation
Links an Asset to Work/Version/Person/Organization/Season/etc. with usage type.

## AssetRightsRecord
May be separate physical entity if multiple licences/territories/terms apply to one asset.

# 13. Audit and review entities

## ReviewTask
Human-review queue entry.

Types:
- identity merge
- identity split
- high-authority conflict
- version classification
- historical date conflict
- person collision
- relationship verification
- source-policy review
- asset-rights review
- canonical override review

## ManualDecision
Immutable reviewer action with rationale/evidence.

## AuditEvent
System/user change event for canonical data, source policy, merges, splits, rights state and destructive/administrative operations.

# 14. Data-quality entities/projections

## CoverageMetric
Derived measurement over an entity or catalogue slice.

Dimensions:
- identity
- core metadata
- credits
- releases
- localization
- provenance
- relationships
- assets
- freshness

## QualityIssue
Detected anomaly:
- missing P0 field
- unsupported canonical fact
- stale volatile field
- orphan external ID
- duplicate candidate
- impossible date ordering
- conflicting country/language rules
- version/release mismatch

# Conceptual ERD

```text
                                +------------------+
                                |      Source      |
                                +--------+---------+
                                         |
                                         v
                                +------------------+
                                |  SourceSnapshot  |
                                +--------+---------+
                                         |
                                         v
                                +------------------+
                                |    Observation   |
                                +--------+---------+
                                         |
                                         v
                                +------------------+
                                |      Claim       |
                                +---+----------+---+
                                    |          |
                             supports|          |resolves into
                                    v          v
+---------+       +---------+   +------------------+    +-------------------+
| Person  |<----->| Credit  |-->|       Work       |<-->| EntityRelationship|
+----+----+       +---------+   +--+----+----+-----+    +-------------------+
     |                              |    |    |
   Names                         Versions |  Series/Episode structure
     |                              |    |    |
     v                              v    |    v
+---------+                   +---------+| +--------+
|  Name   |<------------------| Version || | Season |
+---------+                   +----+----+| +---+----+
                                    |     |     |
                                    v     |     v
                              +-----------+ +------------------+
                              |ReleaseEvent| |EpisodeMembership|
                              +-----+-----+ +------------------+
                                    |
                                    v
                              +-------------+
                              |Availability |
                              |    Offer    |
                              +-------------+

Work/Version/Person/Organization/Season/etc.
        |          |         |
        +----------+---------+------> ExternalIdentifier
        +---------------------------> Asset / AssetRights
        +---------------------------> Certification
        +---------------------------> CanonicalDecision / AuditEvent
```

# Cardinality highlights

- Work `1 -> many` Names
- Work `1 -> many` Versions
- Work `1 -> many` ReleaseEvents
- Work `1 -> many` Credits
- Work `many <-> many` Organizations through roles
- Work `many <-> many` Works through typed relationships
- Series Work `1 -> many` Seasons
- Series Work `1 -> many` Episode Works via EpisodeMembership
- Work/Version `1 -> many` Certifications
- Work/Version `1 -> many` AvailabilityOffers
- Any canonical entity `1 -> many` ExternalIdentifiers
- Any claimable subject `1 -> many` Claims
- Claim `many -> one/many` evidence locations/snapshots depending physical design
- Canonical value `1 -> one/many` supporting Claims

# Important anti-patterns prohibited

Do not create a single `movies` table with columns such as:

```text
id, tmdb_id, title, language, release_date, poster_url,
cast_json, crew_json, ott_platform, imdb_rating
```

That schema cannot correctly represent our product.

Do not:
- make TMDB/IMDb IDs primary keys;
- store all aliases in comma-separated strings;
- serialize canonical cast/crew as provider JSON;
- use one release date;
- put OTT provider directly on Work;
- put certification directly on Work without territory/version;
- overwrite old status/release dates;
- treat a dub/remaster/re-release as automatically new Work;
- attach unsupported artwork URLs directly to titles;
- mix source raw payloads with canonical entities.

# Physical-schema principles to validate later

Likely implementation choices after freeze:
- PostgreSQL UUID/ULID-style internal IDs;
- normalized core entities;
- JSONB allowed for provider raw snapshots and low-value extensible attributes, not core identity;
- append-only claims/history where practical;
- database constraints for canonical invariants;
- temporal/index strategy for volatile availability/release data;
- trigram/full-text indexes for early search;
- partitioning only when measured scale demands it.

These are architecture directions, not permission to create migrations yet.

# Stress cases the model must survive

Before locking this entity model, test at least:
- silent/lost films;
- one Work with uncertain year;
- same title/language/year but different films;
- simultaneous Telugu/Tamil production;
- Hindi/Telugu/Tamil dubbed release of one film;
- cross-language remake network;
- director's cut/restoration/re-release;
- one certification per different cut;
- one film with different India/US release dates;
- Netflix series released all-at-once;
- weekly broadcast series;
- split season/Part 1 + Part 2;
- anthology series;
- standalone special;
- pilot converted to feature;
- cancelled announced film;
- person with identical name to another person;
- actor stage-name change;
- production company rename/merger;
- conflicting historical credits;
- streaming provider removal/re-addition;
- title with no legally publishable artwork.

# Lock criteria

This model can move from WORKING to LOCKED only after:
1. validation corpus exposes no fundamental missing entity class;
2. identity-resolution specification can operate on it without destructive shortcuts;
3. claim model can evidence every important property;
4. release/version model handles India-specific test cases;
5. series structure handles multiple numbering/release patterns;
6. source/licensing model can attach evidence without copying prohibited content;
7. architecture review confirms efficient PostgreSQL implementation is feasible.
