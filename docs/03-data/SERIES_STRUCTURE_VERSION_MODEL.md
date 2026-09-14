# Series Structure Version Model

**Status: WORKING**  
**Derived from validation cases:** VC-0036, VC-0041, VC-0080, VC-0095..VC-0097

## Problem
A television/streaming title can be packaged differently by broadcaster, territory, platform or later remix. Provider-specific season/part/episode segmentation must not mutate the stable identity of the underlying Series or content.

## Core rule
**Series identity, content-unit identity and presentation structure are separate.**

## Concepts

### SeriesRun
The durable series-run identity defined by `SERIES_IDENTITY_SPEC`.

### ContentUnit
Episode/Special or other stable unit of program content where a distinct identity is justified.

### StructureEdition
A named provider/territory/version-specific organization of content units.

Possible contexts:
- original broadcaster structure;
- streaming international re-edit;
- home-media structure;
- remix/re-cut season;
- chronological/recommended arrangement.

### StructureEntry
Maps ContentUnit or derived content segment into the StructureEdition with order/label/season/part context.

## Important distinction from EpisodeOrder
An `EpisodeOrderEntry` can reorder stable Episodes without editing their boundaries.

A `StructureEdition` can also represent changed boundaries/segmentation where one provider cuts or combines material differently.

## Benchmark examples

### Money Heist
Original Spanish broadcast structure and Netflix international packaging can coexist. Provider `Part` numbering does not become universal truth.

### Arrested Development Season 4 / Fateful Consequences
A later remix reorganizes material into a different episodic presentation. Same Series lineage; alternate structural edition.

### Love, Death & Robots
Provider `Volume` naming is preserved without declaring that Volume is globally synonymous with Season.

### The Clone Wars
Chronological ordering is an OrderScheme, not necessarily a new StructureEdition, because Episode boundaries remain stable.

## Rules
1. Do not clone a Series merely because a provider changes segmentation.
2. Do not rewrite original-broadcast episode numbers when streaming numbering differs.
3. Each structure claim has provider/territory/time/source context.
4. Consumer UI should default to the appropriate local/canonical structure while allowing known alternate orders where useful.
5. Search for an episode title should resolve the stable content identity even if numbering differs by edition.
6. Where boundaries are genuinely different and mapping is partial, allow many-to-many mapping between source units/segments and presentation entries.

## V1 non-goal
No frame-level edit-decision list is required. V1 needs enough mapping to preserve identity, ordering, labels and major segmentation differences.

## V1 acceptance criteria
- same Series supports more than one provider structure;
- same content unit can have different labels/numbers;
- edited segmentation is representable without duplicate Series identity;
- original structure remains recoverable after later platform repackaging;
- structure choice is provenance-backed and reversible.
