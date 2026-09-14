# Split & Combined Work Model

**Status: WORKING**  
**Derived from validation cases:** VC-0061..VC-0064, VC-0098..VC-0099

## Purpose
Cinema history contains projects that are filmed or conceived together but released as multiple Works, as well as later presentations that recombine, re-edit or compile existing Works. Cinema and Series must not solve these cases by destructive merging.

## Core rule
**Release identity and production lineage are related but not identical.**

A project may produce multiple independently released Works. A later combined presentation may itself be a Version, compilation Work, or other derivative entity depending on evidence and user-facing identity.

## Relationship vocabulary
Working relationships:
- `part_of_cycle`
- `split_from_project`
- `companion_to`
- `combined_from`
- `compilation_of`
- `re_edit_of`
- `derived_from`
- `alternate_version_of`

All imported relationship claims require provenance.

## Separate Works by default when
Evidence establishes that the parts:
- received independent public releases;
- carry independent title/credits/certification identities;
- can be distributed or referenced independently;
- are treated by competent sources as separate films/episodes/works.

Examples:
- `Kill Bill: Vol. 1` and `Kill Bill: Vol. 2`;
- `Gangs of Wasseypur – Part 1` and `Part 2`;
- other multi-film parts released separately.

Their common production origin is represented through relationships, not one shared primary ID.

## Combined presentation decision
A later combined presentation can be modeled as either:

### Combined Version
Use when evidence and product behavior indicate the presentation is fundamentally a recombination/edition of existing Works and does not need an independently durable creative identity beyond the source Works.

### Compilation/Derivative Work
Use when the combined presentation has a stable independent title, editorial structure, materially new content, credits, certification/distribution history, or enduring catalogue identity that users and sources treat as its own Work.

## No universal automatic rule
Cases such as `Kill Bill: The Whole Bloody Affair` and `The Disappearance of Eleanor Rigby: Them` must support explicit adjudication. The schema must not force a false answer merely to preserve a simple table structure.

## Component mapping
Where a combined presentation reuses source Works, retain mappings such as:
- source_work_id;
- sequence/order;
- source version/cut if known;
- editorial transformations;
- newly added material;
- omitted material;
- source evidence.

Exact shot-level mapping is outside V1 scope.

## Search/UI rules
- searching a combined title can reach the combined presentation;
- source Works remain independently searchable;
- UI explains `combined from`, `part of`, or `alternate presentation of` rather than implying remake/sequel where inappropriate;
- release dates remain attached to the correct independent Work/Version.

## V1 acceptance criteria
1. separate released parts never lose their IDs when a combined edition appears;
2. combined presentation can link to more than one source Work;
3. relationship decision is provenance-backed and reversible;
4. compilation does not overwrite source credits/releases;
5. ambiguous Work-vs-Version decisions can remain `HUMAN REVIEW` without blocking source observation storage.
