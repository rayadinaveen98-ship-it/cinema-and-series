# START HERE — Cinema and Series

This repository is the authoritative source of truth for **Cinema and Series**.

## Mandatory rule

Do **not** begin production implementation until the V1 specification package is explicitly marked **FROZEN**.

This includes Android, web, backend, database migrations, ingestion workers, and production UI. Small disposable research prototypes are permitted only when a specification document explicitly authorizes them for validation.

## Required reading order

1. `README.md`
2. `docs/00-charter/PRODUCT_VISION.md`
3. `docs/00-charter/PRODUCT_PHILOSOPHY.md`
4. `docs/00-charter/SCOPE_V1.md`
5. `docs/00-charter/NON_GOALS_V1.md`
6. `docs/01-research/RESEARCH_FOUNDATION_V0.1.md`
7. `docs/02-sources/SOURCE_CONSTITUTION.md`
8. `docs/03-data/DATA_CONSTITUTION.md`
9. `docs/05-architecture/ARCHITECTURE_CONSTITUTION.md`
10. `docs/10-execution/MASTER_ROADMAP.md`

Documents that do not yet exist are planned deliverables of Research Foundation v0.1 and must be created before the V1 contract can be frozen.

## Decision states

Every important specification must use one of these states:

- **LOCKED** — accepted as a durable project decision; changes require a documented decision record.
- **WORKING** — current preferred direction, still under research or validation.
- **OPEN** — unresolved and must not be silently assumed.
- **REJECTED** — deliberately excluded, with rationale preserved.

## Non-negotiable working discipline

1. Research before implementation.
2. Preserve evidence and licensing constraints alongside source decisions.
3. Never make an external provider's ID our canonical identity.
4. Never silently replace disputed metadata; preserve claims and provenance.
5. Never call a field "complete" without a measurable definition.
6. Never merge uncertain identities without a confidence/review path.
7. Never treat artwork rights as equivalent to metadata rights.
8. Never allow an AI-generated unsupported claim to become canonical metadata.
9. Record important architecture/product changes through ADRs or equivalent decision records.
10. Keep this repository updated before implementation diverges from the specification.

## Current milestone

**Research Foundation v0.1**

Goal: establish the product constitution, competitor/gap research, source/licensing strategy, data constitution, architecture constitution, engine boundaries, UX information architecture, data quality model, and execution roadmap.

Exit condition: enough evidence exists to freeze the V1 specification without relying on assumptions that could invalidate the product later.
