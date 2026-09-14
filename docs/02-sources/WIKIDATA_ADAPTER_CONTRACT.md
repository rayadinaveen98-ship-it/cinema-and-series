# Wikidata Adapter Contract — Cinema and Series V1

**Status: LOCKED FOR V1 IMPLEMENTATION**  
**Date: 2026-09-14**

## Purpose

This contract defines exactly how Wikidata may feed Cinema and Series production ingestion. It closes the gap between the high-level Source Registry and real implementation behavior.

Wikidata is an **open evidence source and identity graph**, not CAS canonical truth.

# 1. Approved source scope

Approved production source:
- Wikidata structured entity data from namespaces covered by Wikidata's CC0 structured-data policy.

Primary access methods:
1. recommended Wikidata entity **JSON dump** for full baseline/reconciliation;
2. Wikidata **incremental/add-change dumps** for change discovery once technically validated;
3. targeted Wikibase REST/EntityData/Action API entity retrieval for bounded refresh/verification;
4. WDQS/SPARQL for research, benchmark construction and targeted queries only.

WDQS is **not** the bulk-catalogue production dependency.

Official source documentation reviewed:
- `https://www.wikidata.org/wiki/Wikidata:Database_download`
- `https://www.wikidata.org/wiki/Wikidata:Data_access`
- `https://www.wikidata.org/wiki/Wikidata:Licensing`

# 2. Licensing boundary

Structured Wikidata data in the applicable entity namespaces is CC0 and may be used commercially.

The adapter must not assume the same licence for:
- arbitrary linked webpages;
- Wikimedia Commons media;
- Wikipedia article prose;
- external reference documents;
- media files linked from Wikidata.

A reference URL can support provenance/discovery without granting CAS permission to copy the referenced content.

# 3. Raw ingestion unit

The raw source unit is a Wikidata entity revision/snapshot with:
- QID/PID as provider external ID;
- revision/entity version where available;
- labels/descriptions/aliases;
- statements;
- statement rank;
- qualifiers;
- references;
- retrieval/dump timestamp;
- adapter/parser version;
- payload checksum.

QIDs/PIDs remain **ExternalIdentifiers**. They never become CAS primary IDs.

# 4. Initial allowlisted semantic domains

The adapter may produce candidate Observations/Claims for:
- Work/entity type signals;
- titles, labels and aliases;
- original/native/localized title candidates where the statement semantics support them;
- language(s);
- country/countries of origin;
- dates with precision and qualifiers;
- cast/crew/person relationships;
- production/distribution organizations;
- Series/Season/Episode relationships when explicit enough;
- sequel/prequel/remake/adaptation/franchise relationships;
- people/organization identity attributes useful for reconciliation;
- external identifiers;
- source references and qualifiers.

Every property mapping must live in a versioned adapter mapping table/configuration. Unknown/new properties fail closed into raw evidence/discovery until mapped.

# 5. Claim creation rules

A Wikidata statement becomes a CAS Claim only after:
1. entity type/context is compatible with the target CAS domain;
2. the property has an approved semantic mapping;
3. value datatype parses safely;
4. qualifiers needed for meaning are preserved;
5. rank/reference metadata is retained;
6. identity resolution maps or proposes the correct CAS entity.

A statement must **not** directly update canonical projection tables.

# 6. Rank/reference policy

Wikidata rank is an input, not truth.

- preferred rank can influence candidate selection inside the adapter;
- normal/preferred rank does not override stronger first-party/authority evidence in CAS;
- deprecated statements remain useful historical evidence when retention is appropriate, but should not become current canonical truth merely because they exist;
- referenced statements receive stronger source-quality treatment than unsourced community statements when field policy considers that relevant.

The exact canonical outcome remains controlled by CAS source trust + canonicalization rules.

# 7. Qualifier preservation

Do not flatten qualifiers away.

Important examples include:
- start/end/effective dates;
- territory/country context;
- series ordinal/sequence;
- point-in-time;
- determination method;
- language/version context.

If a property cannot be interpreted safely without a qualifier that the parser does not understand, the observation must be held for review rather than simplified incorrectly.

# 8. Identity behavior

A QID match is strong external evidence but not an irreversible CAS identity operation.

Rules:
- one Wikidata entity may map to one active CAS entity per appropriate entity class, subject to redirects/history;
- one CAS entity may hold many external IDs;
- a Wikidata merge/redirect does not force a destructive CAS merge;
- QID redirects/replacements are recorded in ExternalIdentifier history;
- conflicting QID mappings create an IdentityReview task;
- automatic CAS entity merges are prohibited by the general automation policy.

# 9. Refresh strategy

## Full reconciliation
Use the recommended JSON entity dump on a regular cadence aligned with Wikidata publication, initially weekly when operationally practical.

## Incremental changes
Use daily add/change dumps only after an adapter validation proves that change/deletion/revision semantics are handled correctly.

## Targeted refresh
High-priority upcoming/recent/conflicted entities may be refreshed directly through a bounded entity API path.

No adapter may hammer WDQS as a pseudo-bulk API.

# 10. Change/history behavior

When an upstream statement changes or disappears:
- preserve the prior CAS Claim/history subject to retention policy;
- create/update source observation state;
- re-run canonicalization for affected semantic slots;
- do not mutate historical CanonicalDecision records;
- do not delete the CAS entity solely because Wikidata removed/merged a QID.

# 11. Error/vandalism resilience

Wikidata is community maintained. The adapter must therefore support:
- outlier detection;
- property/type consistency checks;
- sudden high-impact change review;
- references/authority comparison;
- previous-revision comparison where useful;
- source health monitoring;
- adapter kill switch.

Examples that should escalate rather than auto-apply include a sudden birth/death-date change, WorkKind mutation, or relationship change that would merge/split identity.

# 12. Descriptions and prose

Wikidata descriptions may be used as sourced short structured labels/context only where the CC0 structured-data licence applies and product policy permits. They are **not** a substitute for a rights-cleared/CAS-authored synopsis.

Wikipedia article text must never be silently copied through the Wikidata adapter.

# 13. Media boundary

Wikidata/Commons file references are discovery signals only.

Every image/video/publication decision goes through the Asset Engine and per-asset rights state. A Commons/Wikidata link never bypasses the artwork publication contract.

# 14. Adapter Definition of Done

The production adapter is not complete until tests prove:
- dump checksum/download/retry safety;
- resumable/idempotent import;
- property allowlist enforcement;
- qualifier/reference/rank preservation;
- QID redirect/history handling;
- no direct canonical writes;
- source revision/checksum provenance;
- reprocessing with newer parser version;
- bounded incremental refresh;
- kill switch;
- regression cases from the validation corpus pass.

# 15. Failure mode

If Wikidata is unavailable or materially changes policy:
- stop affected acquisition;
- retain CAS identities;
- mark source freshness/health degraded;
- continue serving supported canonical facts where policy permits;
- resume/reconcile after source recovery/review.

Wikidata is a major baseline source, but Cinema and Series must remain a database with its **own identity, provenance and truth model**.
