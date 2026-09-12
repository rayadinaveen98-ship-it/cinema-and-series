# Claim & Provenance Model — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Claims are the evidentiary foundation of Cinema and Series. The canonical catalogue must be explainable as a projection over sourced claims, not as a collection of silently overwritten fields.

## Core pipeline

```text
Source
  -> SourceSnapshot
  -> Observation
  -> Claim
  -> Reconciliation / Identity Resolution
  -> CanonicalDecision
  -> Canonical Projection
```

Each stage has a different purpose and should remain distinguishable.

## Source

A registered origin of evidence governed by the Source Registry and Licensing Matrix.

A Source describes the provider/institution/channel and its policies. It is not an individual fetched page/record.

## SourceSnapshot

An immutable record of what we observed from a Source at a specific time, subject to permitted storage.

Conceptual fields:
- `snapshot_id`
- `source_id`
- provider record ID / URL / request key
- retrieval timestamp
- source publication timestamp where known
- effective date/time where known
- response/document metadata
- content hash
- raw storage location or reference mode
- source-policy version
- acquisition adapter version
- status

### Storage modes

Because rights differ, a snapshot may be:
- `FULL_PAYLOAD_STORED`
- `STRUCTURED_PERMITTED_FIELDS_STORED`
- `HASH_AND_LOCATOR_ONLY`
- `MANUAL_EVIDENCE_REFERENCE`
- `EXTERNAL_DOCUMENT_REFERENCE`

We do not store prohibited copies merely for provenance convenience.

## EvidenceLocator

Points to the exact support within a SourceSnapshot/source record.

Examples:
- JSON pointer `/release_dates/india/0/date`;
- certificate number and search record;
- archive accession number;
- webpage section/heading;
- PDF page/entry where permitted;
- YouTube video ID + timestamp;
- official post ID;
- provider field name.

Conceptual fields:
- `evidence_locator_id`
- snapshot/source ID
- locator type
- locator value
- quoted/extracted text only if rights permit
- evidence note

## Observation

Raw/normalized parser output that has not yet been accepted as a claim about a canonical entity.

Why this layer exists:
- parser may extract wrong field;
- entity may not yet be resolved;
- provider type may need normalization;
- several observations may map to one claim;
- source value may need locale/date parsing.

Conceptual fields:
- `observation_id`
- snapshot ID
- source entity identifier
- raw field key
- raw value or permitted normalized representation
- parsed type/value
- parser/extractor version
- extraction method (`API_FIELD`, `STRUCTURED_DATA`, `RULE_PARSER`, `MANUAL`, `AI_ASSISTED`)
- extraction confidence/status
- target entity candidate(s)

AI-assisted extraction is allowed here, but the resulting Observation still requires evidence and normal claim validation.

## Claim

A normalized proposition about a canonical or candidate entity.

Generic shape:

```text
(subject, predicate, object/value, context, evidence, temporal scope, status)
```

Examples:

```text
Work CAS123 -- ORIGINAL_TITLE --> "RRR"
Work CAS456 -- ORIGINAL_LANGUAGE --> Telugu
Person CASP17 -- CREDITED_AS(actor, Work CAS123) --> "..."
Work CAS789 -- SCHEDULED_THEATRICAL_RELEASE(India) --> 2027-08-14
Work CAS789 -- PRODUCTION_STATE --> FILMING
Version CASV3 -- RUNTIME --> 03:01:22
Work CAS111 -- REMAKE_OF --> Work CAS222
```

## Claim conceptual fields

### Identity
- `claim_id`
- claim schema/predicate version

### Subject
- subject entity type
- subject CAS ID or candidate identity

### Predicate
- normalized predicate ID
- field/domain

### Object/value
One of:
- scalar typed value;
- entity reference;
- date/interval with precision;
- duration;
- localized text;
- structured small value where schema permits.

### Context
Optional dimensions:
- Version
- Territory
- Language
- Script
- ReleaseEvent
- certification authority
- role/job
- platform/provider
- season/order system

### Evidence
- one or more EvidenceLocators
- SourceSnapshot/source
- source-specific record ID

### Time
- observed/retrieved at
- source publication time
- effective from/to
- claim date precision

### Process
- adapter/parser version
- extraction method
- normalization rule version
- creator (`SYSTEM`, `IMPORT`, `HUMAN`)

### State
- evidence tier/trust inputs
- claim status
- validation status
- conflict group ID nullable
- superseded-by claim ID nullable
- rejection reason nullable

## Claim status vocabulary

- `CANDIDATE`
- `ACTIVE`
- `CORROBORATED`
- `SUPERSEDED`
- `CONTRADICTED`
- `DISPUTED`
- `REJECTED_BAD_EXTRACTION`
- `REJECTED_WRONG_ENTITY`
- `REJECTED_UNRELIABLE`
- `RETRACTED_BY_SOURCE`
- `INVALIDATED_BY_POLICY` — source may no longer be usable for new processing; legal retention behavior depends on policy

Status is not the same as whether the source is legally ingestible.

## Claim temporal semantics

A fact can change without the old claim becoming false.

Example:

```text
2026-01-10 official announcement:
release scheduled for 2026-08-07

2026-04-11 official announcement:
release moved to 2026-08-14
```

The first claim becomes historically superseded for current scheduling but remains valid evidence that August 7 was once announced.

This is crucial for:
- release changes;
- project titles;
- production status;
- cast announcements/removals;
- streaming availability;
- company names;
- certification versions.

## Date values and precision

Never manufacture missing precision.

A date value can contain:
- calendar system;
- year;
- month nullable;
- day nullable;
- time nullable;
- timezone nullable;
- precision (`YEAR`, `MONTH`, `DAY`, `TIME`);
- approximation flag/range;
- source wording where useful.

`1957` must not be stored semantically as `1957-01-01`.

## Claim groups

Claims can be grouped by semantic slot/context for conflict comparison.

Example conflict key:

```text
subject = Work X
predicate = THEATRICAL_RELEASE_DATE
territory = India
version = Telugu theatrical version
release_event = Event Y
```

Only claims addressing the same semantic slot should compete.

A US release date should not conflict with an India release date.

## ClaimLink

Typed link between claims:
- `CORROBORATES`
- `CONTRADICTS`
- `SUPERSEDES`
- `RETRACTS`
- `DERIVED_FROM`
- `PROPAGATES_FROM`
- `DUPLICATE_OF`

`PROPAGATES_FROM` is especially useful for source independence. A newspaper copying a studio press release should not count as wholly independent corroboration.

## CanonicalDecision

An immutable/replayable record describing why a canonical projection selected a value/state.

Conceptual fields:
- `decision_id`
- entity/semantic slot
- selected claim(s)
- competing claim(s)
- rule/policy version
- result value/reference
- evidence label (`OFFICIAL`, `CONFIRMED`, etc.)
- decision mode (`AUTOMATIC`, `HUMAN_REVIEW`)
- reviewer nullable
- rationale/code
- timestamp
- supersedes prior decision nullable

A canonical field should be able to answer:

> Why do we currently display this?

## DerivedFact

Some fields are computed rather than directly sourced.

Examples:
- primary display year;
- preferred locale title;
- current production-state projection;
- "releasing this week";
- CAS Coverage score;
- earliest confirmed public release.

Derived facts must have:
- derivation rule ID/version;
- input canonical facts/claims;
- calculation timestamp;
- invalidation dependencies.

Never disguise a derived heuristic as a sourced fact.

## Claim predicates

Predicates should be a controlled, versioned vocabulary rather than arbitrary strings.

Initial families:

### Identity/descriptive
- HAS_TITLE
- ORIGINAL_LANGUAGE
- PRODUCTION_COUNTRY
- HAS_GENRE
- HAS_SYNOPSIS

### Credits
- HAS_CREDIT
- PORTRAYS_CHARACTER
- CREDITED_AS

### Production
- PRODUCTION_STATE
- ANNOUNCED_AT
- FILMING_STARTED_AT
- FILMING_COMPLETED_AT

### Release
- RELEASE_SCHEDULED_FOR
- RELEASE_OCCURRED_AT
- RELEASE_POSTPONED
- RELEASE_CANCELLED

### Version
- HAS_RUNTIME
- HAS_AUDIO_LANGUAGE
- VERSION_KIND

### Certification
- HAS_CERTIFICATION
- CERTIFIED_RUNTIME

### Relationships
- REMAKE_OF
- SEQUEL_OF
- PREQUEL_OF
- SPIN_OFF_OF
- REBOOT_OF
- ADAPTATION_OF
- VERSION_OF

### External identity
- HAS_EXTERNAL_ID

The physical implementation can use domain tables for performance while retaining claim provenance semantics.

## Canonical projection strategy

Not every UI read should dynamically evaluate millions of claims.

Recommended architecture:

1. claims are authoritative evidence layer;
2. canonicalizer produces materialized/current canonical projections;
3. clients read projections;
4. source/evidence UI can trace projections back to decisions/claims;
5. changes invalidate/recompute only affected projections.

This gives both auditability and performance.

## Human-entered corrections

A human editor is not allowed to type an unsupported canonical value directly.

Editor workflow:
1. select/create evidence/source;
2. create corrected Claim;
3. explain identity/context if needed;
4. canonicalization/review decides projection;
5. audit event records action.

Exception: a first-party/rightsholder-authorized contributor may itself be represented as a Source under defined verification rules.

## Community contributions — future

If community edits are introduced later, contributions enter as Claims/Observations with contributor metadata and evidence. They do not mutate canonical tables directly.

Potential trust inputs:
- evidence quality;
- contributor history;
- domain expertise;
- conflict rate;
- moderator review.

## Source deletion / legal restrictions

If a provider contract ends or source material must be removed:
- follow the contract/policy for cached/raw content deletion;
- retain CAS entity identity and independently supported canonical facts where legally permitted;
- mark claims/evidence whose retained basis is no longer legally available;
- recompute projections when required;
- never fabricate replacement provenance.

This behavior must be source-specific.

## Provenance shown to users

V1 UI need not expose internal technical details, but should support a human-readable evidence drawer such as:

```text
Release date: 14 Aug 2027
Status: Official
Source: Producer announcement
Observed: 3 May 2027
Previously announced: 7 Aug 2027
```

For conflicting evidence:

```text
Premiere date: disputed
Archive A: 12 Mar 1954
Archive B: 19 Mar 1954
```

The goal is useful transparency, not overwhelming raw database internals.

## Required invariants

1. Every non-derived important canonical field has >=1 active/supporting Claim.
2. Every Claim has >=1 evidence reference or an explicitly verified first-party contributor source.
3. Every automated Claim records parser/normalizer version.
4. Claims never silently change value; corrections create new claim/history.
5. Canonical decisions are reproducible from stored rule version + claims where practical.
6. Context-specific claims cannot overwrite another context.
7. Claims from prohibited sources cannot enter production canonicalization.
8. AI-only output can never satisfy the evidence invariant.
9. Manual override has reason and audit event.
10. Deleting source raw content under policy does not silently invent new provenance.

## Test cases required before lock

- two agreeing independent claims;
- ten news copies of one original press release;
- old official release date superseded by new official date;
- official scheduled date but no actual release;
- two high-authority historical sources disagree;
- runtime differs by Version;
- title changes during production;
- cast member announced then absent from final credits;
- provider corrects an external ID;
- wrong-entity parser extraction;
- source later becomes prohibited/suspended;
- approximate historical year;
- manual evidence-only CBFC verification;
- AI extractor reads correct value but targets wrong film;
- canonical value becomes UNKNOWN after unsupported claim removal.

## Lock criteria

This model moves to LOCKED only when:
- physical schema can implement it without generic-EAV performance collapse;
- representative domains can round-trip provenance;
- source-policy deletion scenarios are proven;
- conflict/canonicalization tests pass;
- admin correction workflow never requires direct unsupported canonical edits.
