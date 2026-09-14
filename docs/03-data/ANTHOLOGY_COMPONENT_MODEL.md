# Anthology Component Model

**Status: WORKING**  
**Derived from validation cases:** VC-0042..VC-0045

## Problem
Anthology films and anthology series contain creative components that often have their own titles, directors, writers, cast, runtime and themes. Flattening all credits onto the parent incorrectly implies every creator worked on every segment; modeling each segment as unrelated loses the released anthology identity.

## Core distinction

### Anthology parent
The released film/series/season identity that packages components for consumers.

### Anthology component
A creative sub-work/segment contained by the anthology parent. It may have enough metadata to deserve its own stable CAS identity even when it was not separately distributed.

## Working relationship vocabulary
- `contains_component`
- `component_of`
- `anthology_segment_of`
- `episode_of` when the component is actually distributed as an Episode

Do not use `sequel_of`, `remake_of` or generic franchise membership to represent simple anthology containment.

## Parent-type examples

### Anthology film
`Lust Stories` / `Ajeeb Daastaans`
- one parent Movie Work and ReleaseEvent;
- four component Works/Segments;
- component-specific directors/writers/cast;
- parent-level producer/distributor/overall credits where evidence supports them.

### Anthology series
`Navarasa`
- one Series/limited-series identity;
- individually titled Episodes, which may also behave as anthology creative components;
- episode-specific credits.

## Credits rule
A credit applies only at the level supported by evidence.

Examples:
- Segment director -> component credit only.
- Anthology producer -> parent credit unless source says otherwise.
- Actor appearing in one segment -> component cast credit; may be discoverable through parent aggregation but is not stored as `acted in every segment`.

## Search/display
Users should be able to:
- search a component title and reach the component;
- see its parent anthology;
- open parent and browse all components;
- aggregate cast/crew for discovery without losing component provenance.

## Release rule
A component without independent distribution can inherit/derive parent release context for display, but CAS should not fabricate an independent ReleaseEvent unless a source establishes one.

If a segment later receives standalone festival/theatrical/streaming distribution, that event may attach to the component Work itself.

## Identity rule
Do not create duplicate component identities when the same short is later packaged elsewhere. Identity resolver should compare component title, creators, runtime, production and source IDs, then relate multiple parent containments/releases to the same component where evidence warrants.

## V1 acceptance criteria
- parent and component can each have stable IDs;
- segment-specific credits remain segment-specific;
- one anthology ReleaseEvent does not automatically become four fabricated releases;
- component search resolves through native/localized titles;
- parent UI can aggregate components without mutating stored credit semantics.
