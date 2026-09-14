# Archival Preservation / Survival Model

**Status: WORKING**  
**Origin:** Validation Corpus finding F-01

## Why this exists

Historical cinema exposes a distinction modern movie APIs often blur:

> A Work can be well documented even when no complete film element survives.

`Alam Ara (1931)` is an important example: the Work, production, credits and historical release remain valid knowledge even though the film itself is lost. Likewise, many silent films survive only in fragments, incomplete prints, restorations or archival elements.

Therefore Cinema and Series must not infer `Work validity` from `media availability`.

## Core distinctions

### Work existence
Whether evidence supports that the creative Work existed/was produced/released.

### Survival status
What audiovisual material is known to survive today.

### Preservation state
What preservation/restoration activity or archival holdings are documented.

### Consumer media availability
Whether CAS currently has an approved poster/still/trailer/playback link or other display asset.

These are independent.

## Proposed survival vocabulary

Working values:
- `UNKNOWN`
- `SURVIVES_COMPLETE`
- `SURVIVES_SUBSTANTIALLY_COMPLETE`
- `SURVIVES_INCOMPLETE`
- `SURVIVES_FRAGMENT`
- `SURVIVES_STILLS_AUDIO_DOCUMENTATION_ONLY`
- `PRESUMED_LOST`
- `CONFIRMED_LOST`

Do not treat these as permanent enums until the validation corpus covers archival edge cases internationally.

## Evidence model

Survival/preservation status is claim-backed. A source can claim:
- an archive holds a print;
- only fragments survive;
- a film is considered lost;
- a restoration exists;
- a specific version/cut is preserved;
- preservation status is unknown.

Canonical survival status should record:
- subject Work/Version;
- status;
- as-of date;
- source/claim;
- archive/holding organization if relevant;
- known element type/format if available;
- notes on completeness;
- restoration/version linkage.

## Archive holding concept

Do not equate `archive holds item` with `archive owns rights` or `CAS can display/copy item`.

Potential future `ArchiveHolding` representation:
- Work/Version;
- archive/institution;
- holding/evidence reference;
- element type;
- completeness;
- format/gauge where relevant;
- preservation/restoration status;
- access notes;
- source;
- as-of date.

This may be implemented as structured claims first rather than a dedicated entity in V1 if the physical schema remains simpler.

## Restoration

A restoration generally does **not** create a new Work. It may create or correspond to a Version/Presentation with:
- restoration year;
- source elements;
- restored runtime/cut;
- restorer/archive/company;
- premiere/re-release event;
- technical presentation metadata.

## Quality/CAS Coverage rule

Historical Works must not be penalized as data-quality failures for facts that are genuinely unknowable or media that no longer survives.

Quality states must distinguish:
- `missing_from_CAS`;
- `unknown_in_sources`;
- `historically_unavailable/lost`;
- `not_applicable`.

CAS Coverage can report archival documentation as its own dimension rather than forcing modern metadata expectations onto silent/lost cinema.

## Consumer UX

Where useful, public Work pages may show clear archival labels such as:
- `Lost film`
- `Survives only in fragments`
- `Restored version available`

These labels must be source-backed and should expose an evidence/history affordance.

## Control Room

Entity Inspector should be capable of showing:
- survival/preservation claims;
- known archive holdings;
- conflicting survival reports;
- restoration relationships;
- last verified date.

## Evidence prompting this model

- Film Heritage Foundation, `Alam Ara (1931)`: https://filmheritagefoundation.co.in/alam-ara-1931-hindi-urdu-124-mins/
- Film Heritage Foundation preservation statistics: https://filmheritagefoundation.co.in/preserving-our-film-heritage/
- NFDC-NFAI digitized/restored film lists: https://nfai.nfdcindia.com/

## Decision

**WORKING ACCEPTED:** survival/preservation is a first-class data concern, separate from Work existence, media rights and consumer artwork availability.

Exact physical representation remains to be frozen after further archive-focused corpus cases.
