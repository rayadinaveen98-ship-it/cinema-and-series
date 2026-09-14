# Wikidata Adapter Contract — V1

**Status: LOCKED FOR INITIAL IMPLEMENTATION**  
**Date: 2026-09-14**

## Mission

The Wikidata adapter provides a broad, open, multilingual evidence stream into Cinema and Series while preserving Wikidata's statements, qualifiers, ranks, references and external IDs as evidence—not truth.

# Access strategy

## Bulk baseline
Use the official recommended weekly Wikidata JSON entity dump.

Reason:
- stable documented interface;
- complete entity records;
- line-oriented entity parsing;
- qualifiers/references/ranks retained;
- avoids making our bulk pipeline dependent on WDQS availability.

## Incremental refresh
Use official add/change incremental dumps after technical validation. Incremental processing must be idempotent and checkpointed.

## Targeted fetch
REST/entity/API retrieval is allowed for:
- urgent refresh of upcoming/high-volatility entities;
- conflict review;
- identity resolution;
- validation-corpus work.

WDQS/SPARQL remains useful for discovery/research but is not the authoritative bulk ingestion transport.

# Scope filtering

Do not ingest every Wikidata item into CAS.

The adapter uses type/relationship filters to identify candidate audiovisual Works, Series, Episodes, People, Organizations, creative source works and music entities relevant to our scope.

A candidate may remain outside canonical catalogue until Identity Resolution and minimum-evidence rules pass.

# Statement preservation

For every imported Wikidata statement used by CAS preserve where available:
- Wikidata QID;
- property ID;
- value/object;
- statement rank;
- qualifiers;
- references/reference URLs/IDs;
- statement GUID when available;
- dump/source timestamp;
- adapter/parser version;
- source policy version.

Preferred rank is a Wikidata source signal, not a CAS canonicalization command.

# Labels and aliases

Import labels/aliases with:
- language code;
- script derived where deterministic;
- source role (`LABEL`, `ALIAS`);
- QID;
- source timestamp.

Do not automatically classify an English label as an official English release title. CAS Name semantics must be resolved separately.

# External IDs

External IDs from Wikidata are high-value identity signals.

Rules:
- every external ID remains an `ExternalIdentifier` mapping;
- never use IMDb/TMDB/TheTVDB/QID as CAS primary identity;
- conflicting external-ID mappings create identity-review signals;
- redirects/merges upstream do not silently merge CAS entities.

# References and source independence

When Wikidata provides a reference, retain it as evidence lineage metadata where practical.

Multiple Wikidata statements that all trace to the same underlying source must not be counted as multiple independent confirmations.

A referenced Wikidata statement may create:
1. a claim sourced to Wikidata, with reference lineage;
2. optionally a follow-up discovery lead to the underlying source if that source is independently approved.

# Safety against vandalism / weak statements

No important P0/P1 fact is automatically promoted solely because:
- a Wikidata statement exists;
- it has preferred rank;
- many aliases exist;
- it agrees with another community database that copied the same source.

Risk signals include:
- recent unexplained statement churn;
- missing reference for high-risk identity relationship;
- impossible chronology;
- conflicting external IDs;
- work-type mismatch;
- suspicious mass changes;
- conflict with direct authority.

These feed the Quality and Review engines.

# Import states

Each Wikidata-derived observation must result in one of:
- `CLAIM_CREATED`;
- `DISCOVERY_LEAD_ONLY`;
- `IDENTITY_REVIEW_REQUIRED`;
- `REJECTED_OUT_OF_SCOPE`;
- `REJECTED_BAD_VALUE`;
- `IGNORED_UNSUPPORTED_PROPERTY`.

# Initial property families

The precise property map is versioned configuration. Initial families include:
- instance/type;
- labels/aliases;
- publication/release dates;
- country of origin;
- original language/language of work;
- cast member;
- director;
- screenwriter/creator/producer/cinematography/editor/music roles where modeled;
- production/distribution companies;
- part-of/series/season/episode relationships;
- sequel/prequel/remake/adaptation/source-work relationships;
- external identifiers;
- person aliases/names and identity-supporting dates;
- organization identity/ownership/successor signals where explicit.

Unsupported/new properties are not silently mapped.

# Update semantics

If a statement disappears or changes:
- previous CAS Claim remains historical unless retention policy says otherwise;
- a new observation records the new source state;
- claim status may become superseded/retracted/source-removed;
- canonicalization recalculates affected slots;
- no destructive overwrite occurs.

# Full reconciliation

A periodic full-dump reconciliation must detect:
- missing/deleted upstream entities;
- redirects/merges;
- statement changes missed by incrementals;
- parser-version drift;
- external-ID conflicts;
- stale mappings.

# Performance rule

The adapter must stream/decode dumps incrementally rather than requiring the entire dump in memory.

Processing is resumable with checkpoints and content/dump identifiers.

# Quality acceptance before production

The Wikidata adapter is production-ready only after:
1. at least 200 validation-corpus cases involving Wikidata signals are exercised;
2. zero known critical automatic false merges occur;
3. native-script names survive round-trip correctly;
4. qualifiers/references/date precision are retained;
5. full refresh is resumable;
6. incremental replay is idempotent;
7. provider loss does not delete CAS entities;
8. source-policy kill switch is tested.
