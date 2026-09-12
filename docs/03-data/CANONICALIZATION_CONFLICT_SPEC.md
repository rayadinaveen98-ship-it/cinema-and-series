# Canonicalization & Conflict Resolution Specification — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Canonicalization turns evidence-backed Claims into the current Cinema and Series representation used by clients. It must select useful answers without pretending disagreements never existed.

## Core rules

1. **Claims are evidence; canonical values are projections.**
2. **No claim, no non-derived canonical fact.**
3. **Canonicalization is field/context-specific.**
4. **No single source globally wins.**
5. **Temporal supersession is different from contradiction.**
6. **Credible unresolved conflict is allowed to remain visible.**
7. **Human decisions are audited and reversible.**
8. **Unknown is preferable to unsupported certainty.**

## Canonical slot

Claims compete only when they address the same semantic slot.

A slot is defined by:
- subject entity;
- predicate/field;
- relevant context dimensions.

Examples:

```text
Work X + ORIGINAL_TITLE + language Telugu
Version V + RUNTIME
Work X + THEATRICAL_RELEASE + territory India + Version Telugu
Person P + DATE_OF_BIRTH
```

A US release date and an India release date are different slots and never conflict merely because dates differ.

## Decision pipeline

```text
active claims
 -> policy/legality filter
 -> identity/context validation
 -> temporal interpretation
 -> authority/trust comparison
 -> independence/corroboration
 -> conflict classification
 -> automatic decision OR review
 -> CanonicalDecision
 -> materialized projection
```

## Step 1 — Policy eligibility

Exclude from production canonicalization claims that are:
- from prohibited/unapproved source use;
- bad extraction;
- wrong entity;
- retracted/invalidated where policy requires exclusion;
- unsupported AI output;
- outside the field/context allowed for that source adapter.

Do not delete excluded claims if retention is allowed; preserve audit state.

## Step 2 — Context compatibility

Before comparing claims ensure:
- same Work/Person/etc.;
- same Version where material;
- same territory/jurisdiction;
- same language/name type;
- same release/certification context;
- same temporal question.

Many apparent conflicts disappear when context is modeled correctly.

## Step 3 — Temporal interpretation

Classify relation between claims:
- contemporaneous agreement;
- later update/supersession;
- historical state change;
- correction/retraction;
- true unresolved contradiction.

Example: two official future release dates issued months apart usually represent rescheduling, not two mutually exclusive historical claims.

## Step 4 — Authority/trust

Use `SOURCE_TRUST_MODEL.md`.

Evaluate:
- direct authority;
- specificity;
- version match;
- freshness;
- documentary quality;
- source historical reliability;
- source independence.

Do not reduce all factors to a magic public percentage.

## Step 5 — Corroboration and lineage

Independent corroboration strengthens a claim.

Syndicated/repeated claims do not count as fully independent when source lineage is known.

Example:
- Studio post = original source
- 15 outlets quote same post = secondary propagation
- independent certification record matches date/version = genuinely independent corroboration

## Decision outcomes

### SELECTED
One claim/value clearly satisfies policy and evidence rules.

### SELECTED_WITH_SUPPORT
Multiple independent claims agree.

### SELECTED_SUPERSEDING_PRIOR
New evidence updates a temporally changing fact; old state remains historical.

### CONFLICT_REVIEW_REQUIRED
Credible claims disagree beyond automatic policy.

### CANONICAL_CONFLICT
Conflict remains unresolved after review; public projection may expose dispute.

### UNKNOWN
No eligible evidence is strong enough.

### NOT_APPLICABLE
Field does not apply to this entity/context.

## Evidence labels

Map decisions to human-readable labels:
- OFFICIAL
- CONFIRMED
- STRONGLY_SUPPORTED
- UNVERIFIED — normally not ordinary canonical display for critical facts
- CONFLICTING
- UNKNOWN

A label is derived deterministically from source authority/decision state.

## Field policy examples

### Certification
Issuing authority wins for the certificate it issued unless evidence shows data-entry/version mismatch. A general database does not override regulator data.

### Future release date
Newest competent first-party distributor/studio/platform claim normally supersedes an older planned date, while history retains both.

### Actual release occurrence
An old plan does not win merely because it was official. Actual screening/release evidence determines whether occurrence happened.

### Historical premiere
Archive/primary contemporary evidence can outweigh a modern provider. Two credible archives may remain conflicting.

### Cast/crew
Final on-screen credits/official final credits normally supersede pre-release announced participation for final-credit projection, while announcement history remains.

### Runtime
Compare only matching Versions. A certificate runtime may be canonical for a certified cut, while a streaming Version legitimately has another runtime.

### Original language
Do not infer from country/title. Use production/credits/archive evidence. Genuine multilingual works may have multiple original languages.

### Streaming availability
Newest eligible current observation wins only within TTL. When stale, projection becomes UNKNOWN/stale rather than remaining indefinitely true.

## Multi-valued fields

Not all slots choose exactly one value.

Examples:
- production countries;
- original languages;
- genres;
- cast/crew;
- aliases;
- production companies.

Canonicalization can produce a set where each member has supporting claims and contextual state.

Set reconciliation must distinguish:
- missing source coverage from negative evidence;
- announced vs final credits;
- duplicates/aliases;
- role/context differences.

Absence from one provider is not evidence that a credit is false.

## Negative claims

Explicit negative evidence can exist:
- studio says actor is no longer involved;
- release is cancelled;
- source retracts a prior report.

Negative claim semantics must be explicit. Do not infer `NOT_X` merely because X is missing in another source.

## Human-review policy

Review required for:
- T5 vs T5 conflict without temporal explanation;
- high-impact identity conflicts;
- ambiguous dub/remake/version relationship;
- disputed historical date/credit;
- manual override of strong automatic result;
- source-policy exception;
- high-impact relationship claims.

Reviewer UI must show:
- all competing claims;
- source authority/policy;
- evidence locator;
- temporal history;
- source lineage;
- affected downstream data;
- suggested decision and reason codes.

## Manual decision types

- ACCEPT_CLAIM
- PREFER_CLAIM_FOR_CONTEXT
- MARK_SUPERSEDED
- MARK_CONFLICT_UNRESOLVED
- REJECT_WRONG_ENTITY
- REJECT_BAD_EVIDENCE
- SPLIT_CONTEXT/VERSION
- REQUEST_IDENTITY_REVIEW
- TEMPORARY_OVERRIDE

Every decision records reviewer, timestamp, reason and evidence.

## CanonicalDecision versioning

A decision is immutable. A later decision supersedes it.

Store:
- decision ID;
- semantic slot;
- prior decision nullable;
- selected claim(s);
- excluded competing claims and reasons;
- rule-set version;
- mode (automatic/human);
- evidence label;
- resulting value/set;
- timestamp;
- reviewer/rationale.

## Rules engine

Canonicalization should be deterministic for rule-based cases.

Rules are versioned, testable configuration/code, not hidden UI behavior.

Example reason codes:
- `DIRECT_AUTHORITY_NEWER_SCHEDULE`
- `FINAL_CREDIT_SUPERSEDES_ANNOUNCED`
- `VERSION_CONTEXT_SEPARATES_RUNTIME`
- `INDEPENDENT_CORROBORATION`
- `SOURCE_NOT_APPROVED_FOR_FIELD`
- `HIGH_AUTHORITY_CONFLICT_REVIEW`
- `VOLATILE_VALUE_STALE`

## Derived projections

Canonical data should materialize common reads:
- preferred title by locale;
- current production status;
- primary release year;
- current India theatrical date;
- principal cast/crew;
- current streaming offers;
- evidence badge.

Projection tables/cache are rebuildable from Claims + decisions/rules.

## Recalculation triggers

Recompute affected slots when:
- new Claim arrives;
- Claim status changes;
- source trust/policy changes;
- identity merge/split occurs;
- Version context changes;
- manual decision entered;
- volatile value expires;
- canonicalization rule version changes.

## Source outage behavior

A source outage does not delete supported stable facts.

Volatile fields use TTL and stale state.

Contract/policy termination follows source-specific retention rules and can trigger projection recalculation.

## Conflict UX

Examples:

### Unresolved historical date
```text
Premiere: Date disputed
12 Mar 1954 — Archive A
19 Mar 1954 — Archive B
```

### Rescheduled future release
```text
India theatrical: 14 Aug 2027 · Official
Previously scheduled: 7 Aug 2027
```

### Runtime by version
```text
India theatrical cut: 151 min
Streaming version: 156 min
```

Do not flatten these into one unexplained value.

## Quality invariants

- no canonical important field without supporting claim/derivation;
- no active decision pointing to wrong-entity claim;
- no volatile value remains current beyond configured TTL without verification;
- no decision silently crosses territory/version context;
- no manual override lacks audit reason;
- no newer rule version silently rewrites history without new CanonicalDecision/audit event;
- unresolved high-authority conflict cannot be labelled CONFIRMED.

## Validation tests

1. one strong claim;
2. three independent agreeing sources;
3. one official + many copies;
4. official future date updated;
5. official planned date that never happened;
6. regulator vs general provider conflict;
7. historical archive disagreement;
8. runtime differences resolved by Version;
9. announced actor absent from final credits;
10. stale streaming offer;
11. source becomes prohibited;
12. provider record mapped to wrong Work;
13. multi-valued country/genre/credits;
14. negative cancellation/retraction claim;
15. human unresolved conflict.

## Lock criteria

Move to LOCKED only when:
- field policies exist for all V1 P0/P1 domains;
- rules are deterministic/testable;
- validation corpus conflicts produce expected decisions;
- canonical projections can be rebuilt from evidence;
- conflict UI/admin requirements are defined;
- source-policy changes safely trigger recalculation.
