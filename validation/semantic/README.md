# Semantic Validation

This directory turns the evidence-backed validation corpus into an executable semantic benchmark without rewriting the historical evidence manifests.

## Separation of responsibilities

### Corpus manifests

`validation/corpus-tranche-*.jsonl` contain:

- evidence;
- expected CAS outcome;
- assertion operators;
- adjudication/evidence status.

They are the truth/evidence layer and should not be rewritten merely to satisfy a runtime implementation.

### Binding overlays

`validation/semantic/bindings-*.jsonl` add runtime-local structure:

- local entity references;
- assertion subject/object bindings;
- predicates required by an operator;
- identity scope where identity semantics would otherwise be ambiguous.

Bindings are additive. They may not contradict an inline binding already present in a corpus case.

### Operator contract

`operator-contract-v0.1.json` defines the runtime-neutral meaning and minimum bindings for each assertion operator.

Identity assertions explicitly distinguish:

- `exact_entity` — both refs resolve to the same durable CAS entity;
- `underlying_work` — refs may be different entity kinds, such as Work and Version, but belong to the same creative Work;
- `series_lineage` — refs participate in the same program/franchise lineage without asserting exact identity.

A Version and its parent Work must never be assigned the same exact CAS identity merely because `underlying_work` is shared.

Other examples:

- relationship assertions: subject + predicate + object;
- field/canonicalization assertions: subject + predicate;
- review/search assertions: subject;
- `custom`: requires a named specialized evaluator and is never auto-passed by the generic runner.

### Preflight

`run_semantic_preflight.py` checks whether assertions are structurally executable.

It reports:

- `runtime_ready`;
- `needs_binding`;
- `manual_or_specialized`.

**Runtime-ready does not mean PASS.** It only means an evaluator has enough structured references to execute the assertion.

### Reference states

`reference-state-*.jsonl` are independently structured, evidence-derived semantic graphs used to test the assertion model itself.

`run_reference_semantics.py` executes supported assertions against those graphs.

A reference PASS means:

> the assertion and independently structured reference state agree.

It does **not** mean a production engine is correct.

Production engines must never read reference-state files to calculate their output.

### Future production-engine observations

`engine-observation.schema.json` and `ENGINE_ADAPTER_CONTRACT.md` define the neutral output expected from future Identity, Relationship, Release, Canonicalization, Review-Routing and Search implementations.

The implementation under test exports observed state. The benchmark then evaluates the same semantic assertions against that output.

Reference results and real-engine results must always be reported separately.

## Runtime result contract

An evaluator emits one of:

- `PASS`
- `FAIL_MODEL`
- `FAIL_ENGINE`
- `FAIL_DATA`
- `BLOCKED_EVIDENCE`
- `NOT_IMPLEMENTED`

`NOT_IMPLEMENTED` must never be converted into `PASS`.

Every real engine result must identify:

1. `case_id`;
2. `assertion_id`;
3. evaluator/adapter version;
4. implementation revision;
5. observed state used for comparison;
6. expected state;
7. result classification;
8. reason code / explanation.

## Migration policy

Binding migration is risk-led, not convenience-led.

Priority order:

1. critical identity and merge/split cases;
2. release chronology and precision;
3. canonicalization/source conflicts;
4. Work/Version/restoration semantics;
5. people/credit identity;
6. organization/rightsholder identity;
7. series/episode structure;
8. lower-risk representation cases.

Do not pad semantic readiness by binding easy assertions while leaving critical identity cases descriptive.

Evidence status remains independent from binding completeness. An `evidence_upgrade_needed` case does not become gold merely because it has executable bindings.

## Current accepted milestone

At the first executable semantic milestone:

- corpus: 165 cases / 371 assertions;
- search: 213/500 pre-freeze queries;
- structurally runtime-ready: 76 assertions;
- first reference benchmark: 12 cases / 33 assertions / 33 PASS;
- production-engine benchmark: not implemented yet.

The reference benchmark is a validation-foundation milestone, not permission to open the production implementation gate.
