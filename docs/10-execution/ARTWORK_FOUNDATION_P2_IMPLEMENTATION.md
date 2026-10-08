# Artwork Foundation P2 — P2.1 Implementation

**Status:** P2.1 IMPLEMENTED — SCHEMA + SELECTOR; PRODUCTION POPULATION NOT ACTIVATED  
**Date:** 2026-10-08

## Scope

P2.1 converts the locked P2 artwork contract into a shared implementation boundary for Movies and Series.

Implemented:

- canonical `artwork_assets` evidence/publication table;
- canonical `title_artwork_links` exact Movie/Series identity links;
- closed publication/rights/hosting vocabularies;
- fail-closed schema invariants for public states, attribution, validity and dimensions;
- deterministic rights-first selector;
- first-class premium fallback state;
- selector contract tests.

Not activated:

- artwork discovery;
- rights approval;
- D1 artwork population;
- public artwork publication;
- consumer migration from legacy Movie artwork columns.

## Selector order

The implementation preserves the locked order:

`exact title links -> public eligibility -> role -> territory -> locale -> rights/source preference -> visual suitability -> stable tie-break`

The selector never lets visual quality override eligibility.

## Canonical identity

Artwork links preserve:

- `media_type` (`movie` or `series`);
- `source_table`;
- `source_id`;
- exact asset ID;
- presentation role;
- locale and territory, with empty strings representing neutral scope.

Title text is never used as artwork identity.

## Public eligibility

The selector requires:

- one of the five canonical public states;
- matching rights basis;
- renderable hosting mode;
- clear takedown status;
- rights verification evidence no later than selection time;
- validity window;
- territory eligibility;
- HTTPS delivery;
- required attribution.

Unknown/malformed/unsafe states fall back rather than render.

## Fallback

If no eligible candidate exists for a role, selection returns:

- `url: null`;
- `assetId: null`;
- `attribution: null`;
- `isFallback: true`.

The public projection exposes `hasPublishablePoster`, `hasPublishableBackdrop`, and `isFallback`.

## Production sequencing

P2.1 is an implementation gate, not a population gate. The next P2 step is the read-only Movie + Series coverage audit using the already-prepared snapshot builder/audit contract. Only after that audit is reviewed should a bounded production population plan be created.
