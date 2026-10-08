# Artwork Foundation P2 — Status

**Status:** P2.2 READ-ONLY COVERAGE AUDIT COMPLETE — PRODUCTION POPULATION BLOCKED PENDING RIGHTS-QUALIFIED SOURCES  
**Date:** 2026-10-08

## Completed gates

### P2.1 — Shared artwork foundation

Merged on `main` via PR #72, merge commit `6663f8c62da2b5f14e0b869e111c53dd23397834`.

Implemented:

- shared `artwork_assets` evidence/publication schema;
- shared `title_artwork_links` Movie + Series identity model;
- deterministic rights-first selector;
- fail-closed eligibility checks;
- first-class fallback projection;
- selector contract tests.

P1 was formally closed before this migration was introduced.

### P2.2 — Production coverage audit

Merged via PR #73.

The final read-only audit completed successfully:

- workflow run: `37733154311`
- evaluation time: `2026-10-08T05:36:38Z`
- territory: `IN`
- current production identity scope: **24,644**
  - exact-day Movie identities: **3,546**
  - year-precision Movie identities not duplicated by exact-day Movies: **10,428**
  - Series identities: **10,670**
- legacy artwork candidates discovered: **8**
- publication-eligible candidates: **0**
- fallback-only titles: **24,644**
- audit input SHA-256: `482976b1d08959d2cf88a3d61d3898e2140f7b8758af5093b1442b3b03992156`
- immutable audit artifact: `11530343815`
- artifact SHA-256: `ad6807f93517f4e018118933a08ed695ff7a68462f212484a9877a86ffca0f48`

## Interpretation

The audit deliberately does **not** treat existing legacy URLs as publishable artwork. The eight discovered candidates were normalized as discovery/reference evidence without a verified rights basis, so the selector correctly rejected them for public rendering.

This means P2 should **not** bulk-copy the legacy Movie artwork columns into the new tables.

## Next step

P2.3 is the bounded source-adapter and rights-qualified population design:

1. choose admissible artwork sources;
2. define source-specific provenance and rights evidence;
3. define image-quality validation;
4. generate a bounded candidate set;
5. review coverage before any public publication;
6. populate only approved assets;
7. run the selector/fallback gate;
8. then migrate Movie + Series consumers to the shared artwork projection.

No production artwork population is authorized by this audit alone.


## P2.3 adapter-contract checkpoint — 2026-10-08

Implemented versioned read-only source adapter contracts for `wikimedia_commons_v1` and `internet_archive_v1`. Candidate normalization is deterministic and requires HTTPS source allowlisting, asset-level license identification, and rights-evidence URL. Publication remains fail-closed until source review is `APPROVED` and publication enablement is explicitly true. No discovery run or artwork publication has been executed.
