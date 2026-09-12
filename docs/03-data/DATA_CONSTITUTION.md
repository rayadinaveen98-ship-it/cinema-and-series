# Data Constitution

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Core rule

Cinema and Series does not merely store "the answer." It stores source observations and claims, then derives or selects current canonical representations under explicit rules.

## Canonical identity

Every durable entity receives an internal Cinema and Series ID. External provider IDs are mappings only.

Planned identity families include, at minimum:

- title/work
- series
- season
- episode
- person
- company/organization
- release event
- asset
- source
- claim

The exact ID format remains OPEN pending implementation design, but external IDs will never be primary identity.

## Claims and canonical projection

For important fields, the conceptual model is:

`Source Snapshot -> Extracted Observation -> Claim -> Reconciliation -> Canonical Projection`

A claim should be capable of recording:

- subject entity
- field/predicate
- value/object
- source
- source snapshot or evidence reference
- observation/retrieval time
- source publication/effective time where known
- parser/extractor version
- confidence/reliability inputs
- status (active, superseded, disputed, rejected, etc.)

Canonical values must be explainable from claims and rules.

## Identity versus manifestation

The data model must distinguish a creative work from manifestations/releases where needed. A dubbed release is not automatically a separate movie. A remake is not a dub. A re-release is not a new work. An alternate cut may be a distinct version/manifestation rather than a distinct underlying work.

Exact work/version/edition boundaries remain a major research topic and must be tested against difficult real examples.

## Localization

The model must separate:

- original/native title
- alternate title
- localized title
- transliteration/romanization
- original language
- dialogue/audio language(s)
- dubbed language/version
- production country
- market/territory
- release territory

No single `language` field is sufficient for the product vision.

## Release events

A title may have many release events. Release events must be capable of expressing:

- territory/market
- language/version
- release type
- platform/distributor where relevant
- announced/scheduled date
- actual date
- status
- provenance
- reschedule history

The final schema must not rely on a single global `release_date` field as truth.

## Production lifecycle

Production state changes must be historical events or otherwise auditable. The working state vocabulary includes:

- discovered/candidate
- announced
- pre-production
- filming
- post-production
- completed
- release scheduled
- released
- on hold
- shelved
- cancelled
- unknown

"Rumoured" should remain candidate/evidence state rather than being silently promoted to canonical announced production.

## Relationships

The relationship model must support directional and typed links such as:

- sequel_of
- prequel_of
- spin_off_of
- remake_of
- reboot_of
- adaptation_of
- based_on
- part_of_franchise
- part_of_universe
- alternate_version_of
- crossover_with
- anthology relationships

Relationships require provenance where imported or disputed.

## Credits

Credits must not be flattened into a cast list plus one director. The model should be capable of preserving department, job, character/role, ordering/billing where available, credited-as names, and source provenance.

For Indian cinema, high-visibility craft categories should include director, writing/screenplay/dialogue, cinematography, editing, music/background score, lyrics, playback singing, choreography, production design/art, action/stunts, costume, sound, and VFX where data is available.

## Assets

Media assets require their own provenance/rights record, including source, creator/rightsholder where known, license/usage basis, attribution, retrieved time, checksum, and review/usage status.

## Change history

Important canonical changes must preserve:

- previous value/state
- new value/state
- reason/rule
- evidence/claim references
- actor/process responsible
- timestamp

## Quality and completeness

The database should distinguish missing, unknown, not applicable, conflicting, and unverified values.

A future `CAS Coverage` model should measure completeness across dimensions such as identity, core metadata, credits, release history, localization, sources/provenance, and artwork rather than outputting a single misleading "complete/incomplete" flag.

## Prohibited simplifications

The frozen schema must not collapse these distinctions:

- original vs dub vs remake
- work vs release event
- current value vs source claim
- country vs language vs market
- title identity vs external provider ID
- upcoming status vs release date
- metadata rights vs artwork rights
- unknown vs empty/missing
