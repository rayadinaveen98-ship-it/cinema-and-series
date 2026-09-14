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
- predicates required by an operator.

Bindings are additive. They may not contradict an inline binding already present in a corpus case.

### Operator contract

`operator-contract-v0.1.json` defines the runtime-neutral meaning and minimum bindings for each assertion operator.

Examples:

- `same_identity` / `different_identity`: subject + object;
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

**Runtime-ready does not mean PASS.** It only means a future runtime adapter has enough structured references to execute the assertion.

## Runtime result contract

A real engine/reference-fixture adapter must emit one of:

- `PASS`
- `FAIL_MODEL`
- `FAIL_ENGINE`
- `FAIL_DATA`
- `BLOCKED_EVIDENCE`
- `NOT_IMPLEMENTED`

`NOT_IMPLEMENTED` must never be converted into `PASS`.

Every result must identify:

1. `case_id`;
2. `assertion_id`;
3. evaluator/adapter version;
4. observed state used for comparison;
5. expected state;
6. result classification;
7. reason code / explanation.

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

## Current milestone

The first binding overlay (`bindings-001.jsonl`) covers VC-0156..VC-0165. CI confirmed the overlay mechanism raises runtime readiness without mutating evidence manifests.
