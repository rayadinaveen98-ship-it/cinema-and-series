# Episode Order & Release Partition Model

**Status: WORKING**  
**Derived from validation cases:** VC-0031..VC-0041

## Problem
Streaming services and broadcasters use `Season`, `Part`, `Volume`, `Batch`, `Chapter` and custom numbering inconsistently. Episode air order may also differ from chronological or production order.

A provider label must never silently redefine CAS identity.

## Core rules

1. **Season is a content/production grouping, not merely a release batch.**
2. **Part/Volume/Batch can be a release partition inside one Season.**
3. **Provider installment labels are preserved as source-facing labels.** They do not automatically map 1:1 to CAS Season numbers.
4. **Episode identity is stable and independent of ordering scheme.**
5. **Multiple ordering schemes may coexist.**
6. **Platform migration does not reset Series identity.**

## Conceptual objects

### Series
Durable series-run identity.

### Season
A season/installment grouping adjudicated by CAS from competent evidence.

### ReleasePartition
Optional child grouping used when a Season/installment is released in multiple batches.

Suggested fields:
- partition_id
- parent season/installment
- provider label (`Volume 1`, `Part 2`, etc.)
- sequence within release strategy
- release window/date
- territory/platform context
- source claims

### Episode
Stable episode identity.

### EpisodeOrderEntry
Maps an Episode into a named ordering scheme.

Suggested fields:
- episode_id
- order_scheme_id
- ordinal / season-local number as applicable
- display code (`216`, `S02E16`, etc.)
- source/effective context

### OrderScheme
Examples:
- `broadcast_order`
- `chronological_order`
- `production_order`
- `provider_order`
- `home_media_order`
- `creator_recommended_order`

## Benchmark rules

### Stranger Things Season 4
`Volume 1` and `Volume 2` are release partitions of one Season.

### The Crown Season 6
`Part 1` and `Part 2` remain one Season.

### Cobra Kai Season 6
Three parts remain one 15-episode Season.

### Bridgerton Season 3 / Ozark Season 4 / Manifest Season 4
Split release does not create artificial seasons.

### Money Heist
Netflix's `Part` vocabulary must be preserved without assuming that `Part == Season` globally.

### The Clone Wars
Air order and official chronological order coexist for the same Episode IDs.

## Platform/network history
A Series may change network/platform through time. Store relationships/events such as:
- original network/platform
- acquired/rescued by
- later distribution platform
- release territory/time

Do not generate a new Series solely because distribution changed.

## Review triggers
Human review is required when:
- provider season numbering conflicts across territories;
- one service repartitions episodes differently from original broadcaster;
- later home-media releases relabel season/part boundaries;
- `specials` are inserted into or outside normal season numbering;
- a revival may represent a new Series run rather than continuation (see SERIES_IDENTITY_SPEC).

## V1 acceptance criteria
- one Episode can carry at least two different order positions without duplicate identity;
- release Part/Volume can have dates without becoming Season;
- provider labels can be displayed exactly while CAS internal identity remains stable;
- moving a series from NBC/Fox/Syfy/YouTube to a streamer does not reset the Series ID unless independent identity evidence warrants it.
