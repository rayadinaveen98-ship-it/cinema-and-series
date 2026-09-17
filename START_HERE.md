# START HERE — Cinema and Series

This repository is the authoritative source of truth for **Cinema and Series**.

## Current execution state

Production implementation is active.

The original research foundation and long-form architecture remain preserved as historical/future-platform references, but the current active implementation contract is:

`docs/10-execution/PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

Where an older research or Fast-Track document conflicts with that active roadmap, the active roadmap wins for current product execution unless a newer LOCKED decision explicitly supersedes it.

## Required reading order for active implementation

1. `README.md`
2. `docs/10-execution/PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`
3. `docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md` — historical Fast-Track context
4. `docs/10-execution/CATALOGUE_QUALITY_V1.md`
5. relevant current execution/milestone document for the slice being worked on
6. relevant source/data/architecture specifications when the slice depends on them

For deep future-platform architecture work, also read:

- `docs/00-charter/PRODUCT_VISION.md`
- `docs/00-charter/PRODUCT_PHILOSOPHY.md`
- `docs/02-sources/SOURCE_CONSTITUTION.md`
- `docs/03-data/DATA_CONSTITUTION.md`
- `docs/05-architecture/ARCHITECTURE_CONSTITUTION.md`
- `docs/10-execution/MASTER_ROADMAP.md`

## Decision states

Every important specification must use one of these states:

- **LOCKED** — accepted as a durable project decision; changes require a documented decision record.
- **WORKING** — current preferred direction, still under research or validation.
- **OPEN** — unresolved and must not be silently assumed.
- **REJECTED** — deliberately excluded, with rationale preserved.

## Non-negotiable working discipline

1. Research/prove external data assumptions before production enrichment.
2. Preserve evidence and licensing constraints alongside source decisions.
3. Never silently replace disputed metadata; preserve provenance.
4. Never call a field complete without a measurable definition.
5. Never merge uncertain identities without a confidence/review path.
6. Never treat artwork rights as equivalent to metadata rights.
7. Never allow an AI-generated unsupported claim to become canonical metadata.
8. Production mutations must be explicit, defensive and auditable.
9. Keep quality regression gates clean after catalogue mutations.
10. Keep this repository updated before implementation diverges from the specification.

## Current product direction

Cinema & Series is an India-first cinema discovery and release-intelligence product with three active promises:

1. personalized discovery and recommendations,
2. trustworthy release intelligence,
3. a premium cinematic web/Android experience.

## Current milestone

**Phase P1 — Recommendation Metadata Foundation**

Goal: create the shared genre/person/credit metadata layer required for real personalization before building onboarding/recommendation UI.

Immediate execution sequence:

1. inspect current Movie + Series identity coverage,
2. design shared genre/person/credit schema,
3. build read-only Wikidata genre/director/cast resolver,
4. measure production-catalogue coverage,
5. review quality/yield,
6. only then authorize production migration/enrichment.
