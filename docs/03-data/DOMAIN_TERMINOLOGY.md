# Domain Terminology — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

This glossary defines the words Cinema and Series will use internally. These definitions exist to prevent source providers, UI labels, marketing terms, and developer assumptions from changing the meaning of our data model.

When external sources use different terminology, adapters map into this vocabulary while preserving the source's original wording.

## Foundational concepts

### Entity
A durable thing with a Cinema and Series identity.

Examples: Work, Person, Organization, Version, ReleaseEvent, Season, Asset, Source.

An entity can continue to exist even when all external provider mappings change.

### Work
The canonical creative audiovisual production identity.

A Work is the level at which we normally mean "this movie", "this series", "this episode", or "this special" independent of a particular market release, dub, restoration, or cut.

Examples:
- one feature film;
- one television/streaming series;
- one episode;
- one special;
- one short film.

A Work may have multiple Versions and ReleaseEvents.

A remake is normally a separate Work.

### WorkKind
Normalized classification of a Work.

Initial vocabulary:
- `FEATURE_FILM`
- `SHORT_FILM`
- `TV_MOVIE`
- `SERIES`
- `LIMITED_SERIES`
- `EPISODE`
- `SPECIAL`
- `ANTHOLOGY_SEGMENT` where independent identity is justified
- `OTHER_AUDIOVISUAL` only as controlled escape hatch pending classification

The source's original title type should also be preserved in source observations.

### Series
A Work whose structure contains episodes, normally grouped into seasons/parts or another release order.

A revival/reboot is not automatically the same Series. Identity resolution must consider official continuity and production identity.

### Season
A structural grouping of Episodes within a Series.

Season is not assumed to be a creative Work in its own right. It receives a durable CAS entity ID because numbering, titles, release windows, artwork and provider mappings may require independent identity.

A platform's "Part 1" or "Volume 2" should not be forced into a Season unless the source/product semantics actually support that mapping.

### Episode
A Work that is structurally linked to a Series and optionally a Season.

Episodes need their own CAS identities because titles, credits, runtimes, release dates, versions and external IDs can differ independently.

### Special
A standalone or series-related audiovisual Work that does not fit normal episode/feature classification. Relationship to a Series is explicit rather than implied by title type.

## Version and manifestation concepts

### Version
A materially identifiable realization of a Work that requires separate metadata from the base Work or another realization.

Examples can include:
- director's cut;
- extended cut;
- censored cut;
- international cut;
- festival cut;
- restored version;
- remastered version;
- materially distinct dubbed/localized version;
- simultaneously shot language realization where one Work identity is still appropriate.

A Version should be created only when there is meaningful version-specific data or evidence. We do not create unnecessary version rows for every technical encoding.

### VersionKind
Initial controlled vocabulary:
- `ORIGINAL_RELEASE_VERSION`
- `LANGUAGE_VERSION`
- `DUBBED_VERSION`
- `ALTERNATE_CUT`
- `DIRECTORS_CUT`
- `EXTENDED_CUT`
- `CENSORED_CUT`
- `INTERNATIONAL_CUT`
- `FESTIVAL_CUT`
- `RESTORATION`
- `REMASTER`
- `OTHER_DOCUMENTED_VERSION`

More than one classification may apply through attributes/relationships; do not distort reality merely to fit one enum.

### Dub
A language adaptation of an existing audiovisual Work in which dialogue/audio is replaced or localized while the underlying production remains substantially the same.

Default rule: a dub is **not a new Work**.

It may be represented as:
- version/language-track metadata on the Work; or
- a Version when release, cast/voice credits, runtime/edit, certification or other version-specific data justify separate identity.

### Simultaneous multilingual production
A production intentionally created in multiple languages as part of the same production process, potentially using separate takes, dialogue, performers, edits or scenes.

This is **not automatically a dub** and **not automatically multiple independent Works**.

Identity decision is evidence-based:
- same production/narrative identity with language-specific realizations -> one Work plus Versions/production-language metadata;
- independently produced adaptation/remake -> separate Works with relationship.

Marketing labels such as "bilingual", "multilingual", or "pan-India" are insufficient by themselves.

### Remake
A newly produced Work that recreates/adapts an earlier audiovisual Work.

A remake always receives its own Work ID and links to the source Work through a provenance-backed relationship.

### Reboot
A new Work or Series continuity that restarts/reinterprets an earlier property. It is not merely a new Version.

### Restoration
A later preservation/restoration realization of an existing Work. It normally remains the same Work but can receive a Version ID because restoration date, organization, runtime, scan, grading, audio and release history may differ.

### Remaster
A new technical master of an existing Work, typically without the creative/repair scope of a restoration. Create a Version only when it matters to product data/release history.

### Encoding / file rendition
A technical file representation such as 1080p H.264 or 4K HEVC.

This is **not** a Work or creative Version by default. Streaming/file renditions belong to delivery/media infrastructure if ever needed.

## Release concepts

### ReleaseEvent
A documented occurrence or planned occurrence in which a Work or Version is presented/released to a defined audience/market through a defined release type.

A Work can have unlimited ReleaseEvents.

A ReleaseEvent can include:
- territory;
- sub-territory/market;
- Version;
- language context;
- release type;
- venue/platform/distributor;
- announced/scheduled date;
- actual date;
- precision/timezone where needed;
- status;
- evidence.

### ReleaseType
Initial vocabulary:
- `WORLD_PREMIERE`
- `FESTIVAL_SCREENING`
- `THEATRICAL`
- `LIMITED_THEATRICAL`
- `PREVIEW`
- `BROADCAST`
- `STREAMING_SUBSCRIPTION`
- `DIGITAL_RENTAL`
- `DIGITAL_PURCHASE`
- `PHYSICAL_MEDIA`
- `RE_RELEASE`
- `RESTORATION_SCREENING`
- `EDUCATIONAL_ARCHIVAL_SCREENING`
- `OTHER_DOCUMENTED_RELEASE`

World premiere should be derived/claimed carefully rather than assumed from earliest known date.

### Scheduled date
A date publicly planned for a release before it occurs.

It is a claim/event state, not proof the release happened.

### Actual release date
A date supported by evidence that the release/screening actually occurred.

### Announcement date
When a future release/project/title/status was announced. This is separate from scheduled/actual release.

### Re-release
A new ReleaseEvent of an existing Work/Version after an earlier release. It is not a new Work.

### AvailabilityOffer
A temporal observation that a Work/Version can be watched/acquired from a provider in a territory under an offer type.

Examples: subscription, rent, buy, free-with-ads.

AvailabilityOffer is **not** a permanent title property.

## Localization and naming concepts

### TitleName
A named form associated with a Work/Version/Series/Season/Episode.

Attributes can include:
- text;
- language;
- script;
- territory;
- type;
- preferred flag;
- validity interval;
- source/evidence.

### Original title
The source-language/native title of the Work as established by authoritative evidence.

There can be legitimate multi-original-title cases for multilingual productions; the schema must support this without overwriting one title.

### Localized title
A title deliberately used for another language/territory/market.

### Translated title
A semantic translation of a title. It may or may not have been officially used for a release.

### Transliteration / romanization
A representation of a title/name from one script into another, usually Latin script.

A transliteration is not automatically an official release title.

### Alternate title / AKA
Any documented alternate naming form not better represented by a more specific type.

### Working title
A name used during development/production before the final title. Preserve historically after replacement.

## Geography and language

### Country of production
Country/countries materially associated with production. Not inferred from language or release market.

### Territory
A geographic market/jurisdiction relevant to release, availability, certification or rights.

Territory may be country-level or a controlled sub-territory where product value justifies it.

### Market
A commercial/cultural release context that can sometimes differ from political geography. Use only when a normalized Territory does not express the needed concept.

### Original language
Language(s) in which the Work was originally created/performed as part of production.

### Audio/dialogue language
Language present in a particular Work/Version/audio track.

### Subtitle language
Language of a subtitle/caption offering, normally version/availability-specific.

### Script
Writing system used for a name/title, such as Telugu, Tamil, Devanagari, Latin, Bengali, etc.

Language and script are separate.

## Production lifecycle

### Lead
A possible future Work discovered from weak/preliminary evidence. A Lead is not yet a public canonical Work unless minimum existence criteria are satisfied.

### Announced
A production publicly announced by competent evidence.

### Pre-production
Production is credibly in planning/preparation after announcement/greenlight.

### Filming / production
Principal photography/active production is underway.

### Post-production
Principal production is substantially complete and post-production is underway.

### Completed
Work is materially complete but not necessarily released.

### Release scheduled
At least one future release has a sufficiently supported scheduled ReleaseEvent.

### Released
At least one qualifying public ReleaseEvent is supported as having occurred.

### On hold
Production/release is paused with potential continuation.

### Shelved
Project is not currently proceeding/releasing despite prior development/production, but not necessarily formally cancelled.

### Cancelled
Competent evidence indicates the project will not proceed in its then-current form.

### Unknown
Evidence cannot support a more precise current lifecycle state.

Lifecycle is event history, not merely one mutable enum.

## People, organizations and credits

### Person
A real individual with a durable CAS identity independent of spelling, credited name or role.

### PersonName
A canonical, native, stage, alternate, former or transliterated name attached to a Person with provenance/context.

### CreditedAs
The exact name form under which a Person is credited for a particular Work/Version/Episode.

### Organization
A company, studio, production banner, broadcaster, distributor, label, archive, festival, regulator or other durable organization.

Organization identity is separate from its role on a Work.

### Credit
A sourced assertion that a Person or Organization performed a defined job/role in relation to a Work/Version/Episode.

Credit can contain:
- department;
- normalized job;
- source wording;
- character;
- credited-as name;
- order/billing;
- credited/uncredited status;
- scope;
- evidence.

### Character
A fictional/represented role that may recur across Works and be performed/voiced by Persons. Character entity depth is P2; character-name strings remain supported in V1 credits.

## Relationships

### WorkRelationship
A typed, directional, evidence-backed link between Works.

Examples:
- sequel_of;
- prequel_of;
- remake_of;
- reboot_of;
- spin_off_of;
- adaptation_of;
- crossover_with;
- part_of_franchise/universe;
- segment_of.

### VersionRelationship
A relationship between Versions or between Version and Work.

Examples:
- dubbed_version_of;
- restoration_of;
- extended_from;
- censored_from;
- remaster_of.

### Franchise
A named grouping/continuity/brand containing related Works. Franchise identity should not be inferred merely because Works share a character/actor/title word.

### Universe
A continuity/shared-world grouping where documented. It is not automatically equivalent to franchise.

## Evidence concepts

### Source
A registered provider, institution, publication, website, API, archive, document origin or first-party channel from which observations can be obtained.

### SourceSnapshot
Immutable record of what was observed/retrieved from a Source at a particular time, subject to rights/storage policy.

### EvidenceLocator
A stable pointer within/to source evidence: URL, provider record ID, document page, timestamp, certificate number, video timecode, archive accession, etc.

### Observation
Structured content extracted from a SourceSnapshot before full semantic acceptance.

### Claim
A normalized statement that a subject has a value/relationship under specified context, backed by evidence.

Example:
`Work X --scheduled theatrical release in India--> 2027-08-14`

Claims can agree, conflict, be superseded, or be rejected.

### Canonical projection
The current Cinema and Series representation selected/derived from active Claims under canonicalization rules.

It is a projection, not evidence itself.

### Derived fact
A value deterministically computed from canonical/evidenced data rather than directly claimed by a source.

Example: display year derived from a chosen premiere/release policy.

Derived fields must record derivation rule/version.

## Evidence-state terminology

### Official
Direct competent authority supports the fact.

### Confirmed
Strong evidence supports the fact without material conflict.

### Strongly supported
Good evidence exists but with non-critical limitations.

### Unverified
Evidence is preliminary/weak.

### Conflicting
Credible material sources disagree.

### Unknown
Insufficient evidence.

## Certification concepts

### Certification
A rating/classification decision issued by a defined authority in a jurisdiction for a defined Work/Version.

Certification can include:
- rating/classification;
- certificate number;
- issue date;
- certified runtime/length;
- authority;
- territory;
- advisories;
- Version;
- evidence.

A certification does not necessarily describe all versions/releases of a Work.

## Asset concepts

### Asset
A media object/reference associated with an entity and governed by its own rights/provenance state.

Examples: poster, still, portrait, logo, trailer reference.

### Rights basis
The explicit legal/contractual/open-license reason Cinema and Series may render/host/embed an Asset.

No rights basis -> no public publication.

## Data-quality concepts

### Missing
A field has not yet been populated/researched.

### Unknown
Research/evidence exists but cannot establish a value.

### Not applicable
The field does not conceptually apply.

### Conflicting
Two or more credible claims materially disagree.

### Unverified
A value exists only at a weak evidence level.

These states must not all collapse to SQL NULL in product semantics.

## Identity rules summary

### Normally the same Work
- dubbed language release;
- theatrical re-release;
- restoration;
- remaster;
- director's/extended/censored cut;
- different territory release;
- streaming release;
- physical-media release.

These may have separate Versions/ReleaseEvents.

### Normally a separate Work
- remake;
- rebooted film/series;
- sequel/prequel/spin-off;
- new adaptation of the same novel;
- independently produced language remake;
- episode within a series;
- separate short/feature adaptation.

### Requires evidence-based review
- simultaneously shot multilingual films;
- radically re-edited international versions;
- anthology segments released independently;
- pilot reworked into feature;
- feature recut into episodic series or vice versa;
- split/combined film releases;
- alternate endings with independent commercial identity.

## Rule for unresolved cases

When identity boundaries are uncertain, Cinema and Series must prefer **temporary separation + explicit possible-match relationship/review queue** over a destructive merge.

False duplicates are inconvenient. False merges corrupt history, credits, releases and every downstream feature.
