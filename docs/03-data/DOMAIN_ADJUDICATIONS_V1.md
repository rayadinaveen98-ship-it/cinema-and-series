# Domain Adjudications — V1 Identity Edge Cases

**Status: LOCKED**  
**Date: 2026-09-14**

These decisions resolve high-impact Work/Version/Series boundaries exposed by the validation corpus. They are semantic rules for Cinema and Series, not attempts to mimic any one external provider.

# Rule A — Director's cut of the same production is normally a Version

## Zack Snyder's Justice League

**Decision:** model as a materially distinct **Version** of the underlying `Justice League` Work, with its own Version title, credits/credit differences, runtime and 2021 ReleaseEvent.

**Reasoning:** Warner/HBO Max officially announced it as Zack Snyder's **director's cut of Justice League**. CAS therefore preserves one underlying creative-production Work identity while representing the 2021 realization as a strongly distinct Version.

This does not mean the UI must hide its standalone marketed identity. Search/detail pages may prominently surface the Version title `Zack Snyder's Justice League` and its independent release history.

**General rule:** marketing a director's/extended/restored cut as a standalone title does not by itself create a new Work when the competent evidence describes it as a cut/realization of the same production.

# Rule B — A combined presentation of multiple independently released Works is a distinct Combined Work

## Kill Bill: The Whole Bloody Affair

**Decision:** create a distinct Work of kind `COMBINED_PRESENTATION` / `COMPILATION_DERIVATIVE` linked to:
- `Kill Bill: Volume 1`;
- `Kill Bill: Volume 2`.

Relationships:
- `COMPILATION_CONTAINS` / `COMBINES_WORK` Volume 1;
- `COMPILATION_CONTAINS` / `COMBINES_WORK` Volume 2;
- `DERIVED_FROM` both released Works.

The original volumes retain permanent independent Work identities.

**Reasoning:** Lionsgate describes The Whole Bloody Affair as a single film that **unites Volume 1 and Volume 2**, presented as a complete unrated director's cut, with additional/new material. Because the source inputs are two independently released Works rather than one Work with one alternate edit, CAS must not attach the combined cut as a Version of only one volume.

**General rule:** a combined presentation spanning multiple existing Work identities receives its own Combined/Compilation Work identity unless evidence establishes a pre-existing single parent Work model that can unambiguously own the Version.

# Rule C — Independently perspective-structured films can remain separate Works even when sold as 'versions'

## The Disappearance of Eleanor Rigby: Him / Her / Them

**Decision:**
- `Him` = separate Work;
- `Her` = separate Work;
- `Them` = separate derived/re-edited Work;
- all grouped under one project/collection identity.

Relationships:
- `Him` and `Her` -> `ALTERNATE_PERSPECTIVE_OF` each other;
- `Them` -> `DERIVED_FROM` Him + Her / `COMBINES_MATERIAL_FROM` both.

**Reasoning:** production/distribution material describes HIM and HER as two movies told from different perspectives and also promotes all three as versions. CAS favors Work identity for HIM/HER because they are independently structured films with distinct perspective, titles and runtimes. THEM is an independently released re-edit/combination rather than merely a technical cut of one of them.

**General rule:** 'version' in marketing language does not automatically map to CAS `Version`. CAS asks whether there is one underlying Work realization or independently structured audiovisual Works.

# Rule D — Long-gap revival runs may use separate Series Work identities linked by continuity

## Doctor Who classic / 2005 revival

**Decision:**
- Classic run = Series Work A;
- 2005 revival/new-series run = Series Work B;
- both belong to one `Doctor Who` franchise/program lineage;
- Series B `REVIVAL_OF` / `CONTINUES` Series A.

**Reasoning:** the official Doctor Who material distinguishes the Classic Era and the show's 2005 return/revival. Separate Series-run identities avoid season/episode numbering collisions while preserving continuity.

**General rule:** a revival with a major production-era break and reset structural numbering may receive a separate Series Work while remaining explicitly linked to the same program lineage.

# Rule E — A separately commissioned limited event continuation is a separate Series Work

## Twin Peaks / The Return-era limited event series

**Decision:**
- original Twin Peaks (1990-91) = Series Work A;
- 2017 SHOWTIME limited event series = Series Work B;
- Series B `CONTINUES` Series A and belongs to same franchise/program lineage.

**Reasoning:** SHOWTIME officially described 2017 Twin Peaks as a **new 18-part limited event series**, while separately referring to the original two seasons. The new series picks up twenty-five years later.

The consumer UI may group them under the same Twin Peaks lineage, but canonical Series IDs remain distinct.

# Rule F — Provider-specific recuts/repartitioning do not create a new Series Work

## La Casa de Papel / Money Heist original vs Netflix structure

**Decision:** one core Series Work with multiple **StructureEdition** representations.

At minimum:
- original Antena 3 broadcast StructureEdition;
- Netflix international recut/Part StructureEdition;
- later Netflix-produced continuation episodes remain in the same Series Work, with their own episode identities and release grouping.

The original episode identities and Netflix recut content units are mapped through explicit `ContentUnitMapping` / structure-edition relationships rather than forcing one numbering scheme to overwrite the other.

**Reasoning:** Antena 3 documents the original Spanish run as 15 broadcast episodes, while Netflix presents the series in Parts. Strong secondary/reference evidence documents the original 15 episodes being recut into 22 shorter international streaming episodes. This is a structural re-edit/distribution representation of the same series, not a different fictional/production series identity.

**General rule:** a platform recut that changes episode boundaries/order does not reset Series identity. Store provider-specific structure editions.

# Rule G — Character graph is bounded in V1

**Decision:** V1 does not require exhaustive first-class Character identity for every role.

V1 supports:
- character/role text on Credit;
- optional first-class `Character` entity where useful and confidently resolved;
- multiple role/character strings per performance when sourced.

No title is considered incomplete because its characters have not been globally entity-resolved.

This avoids spending V1 identity effort on a second enormous fictional-entity database before audiovisual identity is stable.

# Rule H — Adaptation source works use a bounded first-class ExternalCreativeWork

**Decision:** V1 supports a durable `ExternalCreativeWork` concept for source material such as:
- novel;
- play;
- comic/graphic work;
- game;
- short story;
- prior non-audiovisual source.

CAS does not attempt to become a complete book/comic/game database in V1.

Fields remain minimal:
- CAS source-work ID;
- type;
- names;
- creator(s) where evidenced;
- external identifiers;
- provenance.

Audiovisual Works can use `ADAPTATION_OF` / `BASED_ON` relationships to it.

# Rule I — Film music model is first-class in V1 capability

**Decision:** lock the bounded music model:
- `MusicalWork`;
- `MusicRecording`;
- `MusicContribution`;
- `AudiovisualMusicUsage`;
- soundtrack Release mappings.

Full soundtrack completeness is not mandatory for every movie, but the schema and API must support song-level composer, lyricist and playback-vocal metadata where evidence exists.

MusicBrainz CC0 core is an approved identity/evidence source, not the sole authority.

# Cross-case invariants

1. A provider's UI grouping never determines CAS Work identity by itself.
2. Marketing words such as `version`, `part`, `season`, `director's cut`, `event series` and `remake` are evidence signals, not automatic schema mappings.
3. Independent public release history matters when deciding Work identity.
4. Versions belong to one Work; if a presentation combines multiple independently identified Works, use a Combined/Derived Work.
5. Provider episode recuts are StructureEditions, not duplicate Series.
6. Series lineage and Series-run identity are separate concepts.
7. Consumer grouping can be friendlier/broader than canonical identity without corrupting IDs.

# Validation consequences

The corpus must include executable assertions for every rule above before V1 freeze. Any future case that contradicts these rules goes to human review and may trigger a superseding domain decision; it is never silently forced to fit.