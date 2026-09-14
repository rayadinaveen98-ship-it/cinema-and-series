# Restoration & Source Element Model

**Status: WORKING**  
**Derived from validation cases:** VC-0001..VC-0002, VC-0020, VC-0065..VC-0070

## Core rule
A restoration/reconstruction is not merely `better artwork` or a new release date. It is a provenance-rich Version/preservation event derived from specific surviving source elements.

## Separation of concerns

### Work
The historical creative identity.

### PreservationState
What is known to survive or be lost.

### SourceElement
A known physical/digital source used or potentially usable for preservation/restoration.

Examples:
- original camera negative;
- duplicate negative;
- release print;
- archival print;
- interpositive/internegative;
- soundtrack element;
- fragment;
- scan/master supplied by another archive.

### RestorationProject
The documented preservation/restoration/reconstruction activity.

### Restored Version
A Version produced by the restoration project when a distinct distributable presentation results.

### ReleaseEvent
Festival/theatrical/streaming/home-media presentation of that restored Version.

## Suggested SourceElement facts
- element_id
- work/version relation
- element_kind
- gauge/format where known
- language/audio context where relevant
- completeness/survival state
- physical condition notes
- holding institution where publishable
- date/provenance
- source claim

Sensitive storage/location detail is not required for public exposure.

## Suggested RestorationProject facts
- project_id
- Work/Version target
- participating archives/organizations
- restoration year/range
- restoration method/notes
- source elements used
- resulting Version(s)
- funding/support where documented
- source/evidence

## Rules
1. Missing original negative does not mean the Work is lost if other elements survive.
2. A partially surviving Work remains a valid Work.
3. Restoration must not overwrite the characteristics of the historical release Version.
4. Restored runtime/color/audio can differ and belongs to the restored Version.
5. A restoration premiere is a ReleaseEvent, not the Work's original release date.
6. Reconstruction choices are provenance-bearing claims, especially for incomplete/variant historical material.
7. Asset/media usage rights remain separate from the fact that an archive holds or restored the material.

## Benchmark examples
- `Alam Ara` — Work exists even though the film is considered lost.
- early Indian silent-film cases — fragmentary/incomplete survival.
- `Napoléon (1927)` — extensive reconstruction from variant materials.
- `The Apu Trilogy` — fire-damaged original elements and modern restoration.
- `Kummatty`, `Thamp̄`, `Ishanou` — Indian restoration projects using surviving elements.
- `The Other Side of the Wind` — unfinished historical production later completed/restored; production completion and preservation work must both remain visible.

## V1 acceptance criteria
1. original Work and restored Version have different IDs/types of identity;
2. source elements can be referenced without becoming consumer-facing Works;
3. restoration project can cite multiple elements and organizations;
4. loss/fragment status does not lower data quality as though CAS simply forgot metadata;
5. original and restoration ReleaseEvents coexist without date overwrite.
