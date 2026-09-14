# ADR-016 — Deterministic, Versioned Canonicalization Rule Engine

**Status: ACCEPTED / LOCKED FOR V1**  
**Date: 2026-09-14**

## Context
`CANONICALIZATION_CONFLICT_SPEC.md` defines how Claims become the current Cinema and Series projection. The implementation mechanism itself remained open.

A black-box AI scorer or opaque third-party rules product would violate core product requirements:
- every canonical fact must be explainable;
- rule changes must be auditable;
- the same eligible claim set + rule version must reproduce the same proposal;
- high-risk ambiguity must route to human review rather than be guessed.

## Decision
V1 canonicalization uses a **deterministic, versioned rule engine implemented in typed application code**, with field/context policies expressed as explicit version-controlled rule modules/configuration.

The initial implementation is TypeScript and lives in a framework-independent domain package shared by API and workers.

We explicitly reject an external enterprise rules engine/DSL for V1 unless validation later proves typed code insufficient.

## Inputs
A canonicalization evaluation receives an immutable evaluation context containing, at minimum:
- semantic slot definition;
- eligible active Claims;
- source policy status/version;
- field-specific source trust/competence;
- source-lineage/independence signals;
- temporal/effective-time context;
- entity/Version/territory/language context;
- current/prior CanonicalDecision where applicable;
- rule-set version;
- volatile-field freshness/TTL state.

It does not fetch random web data inside a rule evaluation.

## Outputs
The engine returns a **DecisionProposal**, not an uncontrolled database mutation.

Proposal contains:
- outcome (`SELECTED`, `SELECTED_WITH_SUPPORT`, `SELECTED_SUPERSEDING_PRIOR`, `CONFLICT_REVIEW_REQUIRED`, `CANONICAL_CONFLICT`, `UNKNOWN`, `NOT_APPLICABLE`);
- selected Claim IDs/value(s);
- excluded/competing Claim IDs;
- deterministic reason codes;
- evidence label;
- review-routing requirement;
- trace/explanation data;
- rule-set version.

An application command persists the immutable CanonicalDecision + projection transactionally and emits the outbox event under ADR-012.

## Rule organization
Rules are separated into:

### Universal eligibility/context rules
Examples:
- source not approved for field;
- wrong entity/Version/territory;
- unsupported extraction;
- stale volatile observation.

### Domain field-policy rules
Examples:
- certification authority for its own certificate;
- future release date supersession;
- final credits vs announced credits;
- runtime separated by Version;
- multi-valued production countries;
- availability TTL.

### Review-routing rules
Examples:
- high-authority unresolved conflict;
- identity-sensitive relationship;
- dub vs remake ambiguity;
- manual override of strong result.

Field policies are explicit. There is no one global numeric confidence threshold that decides every data domain.

## Versioning
Every deployed rule set has a stable version, e.g. semantic version + Git commit/hash.

CanonicalDecision stores the exact rule-set version used.

Changing a rule does **not** mutate old CanonicalDecisions. It can trigger reevaluation and a new superseding decision.

## Explainability trace
Each proposal records machine-readable reason steps such as:
- `CLAIM_ELIGIBLE`
- `SOURCE_APPROVED_FOR_FIELD`
- `CONTEXT_MATCH_VERSION`
- `DIRECT_AUTHORITY`
- `NEWER_SCHEDULE_SUPERSEDES`
- `INDEPENDENT_CORROBORATION`
- `HIGH_AUTHORITY_CONFLICT_REVIEW`

Control Room can render these into human-readable explanation.

No unexplained `confidence = 0.82` is sufficient.

## Determinism
For the same:
- normalized Claims;
- source policy/trust inputs;
- evaluation time/freshness context;
- rule-set version;

the engine must produce the same DecisionProposal.

Time-dependent rules receive an explicit evaluation timestamp so tests are reproducible.

## Multi-valued slots
The engine supports set-valued decisions instead of forcing every field to one scalar.

Examples:
- original languages;
- production countries;
- credits;
- aliases;
- organizations.

Absence in one source is not negative evidence unless an explicit negative Claim exists.

## Human decisions
A human reviewer can:
- accept a proposal;
- choose supported competing Claim(s);
- mark unresolved conflict;
- split context/Version;
- reject wrong-entity/bad-evidence Claims;
- create an explicit manual Claim with evidence/rationale when authorized.

Human action creates an immutable CanonicalDecision and audit record. It never deletes the losing evidence merely to make the projection clean.

A later rule/source change may flag the human decision for review, but cannot silently erase its history.

## AI boundary
AI/LLMs may assist with:
- extracting candidate Observations from permitted text;
- suggesting source lineage;
- explaining a rule trace in natural language;
- proposing likely duplicate/relationship candidates;
- prioritizing review queues.

AI/LLM output may **not**:
- create unsupported canonical facts;
- be the sole authority deciding a high-risk conflict;
- bypass deterministic field policies;
- silently merge identities;
- invent reason codes/evidence.

Any AI-derived Observation must carry extractor/model provenance and remain subject to evidence validation.

## Persistence / concurrency
When a DecisionProposal is committed:
- verify the relevant Claim/slot version has not changed since evaluation;
- use optimistic concurrency/revision check;
- if stale, reevaluate instead of applying an outdated decision;
- persist CanonicalDecision + projection + outbox atomically where possible.

## Re-evaluation triggers
As defined in the domain spec:
- new/changed Claim;
- source policy/trust update;
- identity merge/split;
- Version/context change;
- volatile expiry;
- human decision;
- rule-set version deployment.

Re-evaluation jobs are queued through ADR-008 and are idempotent.

## Testing contract
Each field policy has:
- unit tests;
- table-driven edge cases;
- validation-corpus assertions;
- regression cases for every production incident.

Critical benchmark policy: **known false automatic merges are unacceptable**. Ambiguity should route to review.

The machine-readable validation manifest exercises outcomes without depending on exact class/function names.

## Rejected alternatives
### LLM chooses canonical truth
Rejected: nondeterministic, difficult to audit, unsupported-fact risk.

### One weighted confidence score for all fields
Rejected: authority and semantics differ by field/context.

### External business-rules platform in V1
Rejected: unnecessary operational/authoring complexity before rule corpus proves need.

### Hard-coded logic hidden in controllers/importers
Rejected: rules must be centralized/versioned/testable.

## Consequences
Canonicalization remains explainable and reproducible, at the cost of writing explicit field policies. That cost is intentional: the rules are part of the core intellectual/product value of Cinema and Series.
