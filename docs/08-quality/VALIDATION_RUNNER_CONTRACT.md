# Validation Runner Contract — V1 Research Gate

**Status: LOCKED CONTRACT / IMPLEMENTATION ALLOWED AS RESEARCH TOOLING**  
**Date: 2026-09-14**

## Purpose

The validation runner turns the evidence corpus into repeatable pass/fail checks before production implementation is unlocked.

This is explicitly permitted pre-freeze tooling because it validates the frozen semantic specifications; it is not production backend code.

# Inputs

The runner consumes:
- `validation/validation-case.schema.json`;
- one or more `validation/*.jsonl` manifests;
- adjudication overrides where applicable;
- a semantic model adapter representing the system under test;
- optional search-query manifests;
- rule/version metadata.

# Phase 1 — Manifest validation

For every JSONL case:
1. parse one JSON object per line;
2. validate against the versioned JSON Schema;
3. verify unique `case_id`;
4. verify unique `assertion_id` within case;
5. verify evidence URLs/grades are present;
6. verify entity references used by assertions exist where the operator requires them;
7. reject unknown assertion operators/domains rather than ignoring them.

Manifest errors produce `FAIL_MANIFEST`, never a semantic PASS.

# Phase 2 — Evidence/adjudication state

The runner distinguishes:
- `seed`;
- `evidence_upgrade_needed`;
- `open_adjudication`;
- `gold_candidate`;
- `gold`.

Only `gold` cases count toward final freeze pass percentages.

`gold_candidate` can be executed for model feedback but does not satisfy the final evidence quota until promoted through evidence/adjudication review.

# Phase 3 — Semantic assertions

Supported V1 assertion families include:
- same/different entity identity;
- relationship presence/absence;
- Work/Version classification;
- title/name history;
- production lifecycle history;
- release-event history/context;
- multilingual/localization structure;
- credit/person identity;
- series/season/episode/StructureEdition structure;
- organization/corporate lineage;
- country/territory multiplicity;
- archival preservation state;
- canonicalization/review routing;
- search resolution/ranking.

The validation layer operates on CAS semantic concepts, not physical SQL table names.

# Result vocabulary

Every assertion produces exactly one result:
- `PASS`;
- `FAIL_MODEL` — locked ontology/domain representation cannot express expected truth;
- `FAIL_ENGINE` — model can express it but implementation/rule produced wrong behavior;
- `FAIL_DATA` — ingestion/source mapping produced wrong/missing supported data;
- `FAIL_SEARCH` — retrieval/ranking failed;
- `FAIL_POLICY` — automation/source/review policy violated;
- `BLOCKED_EVIDENCE` — expected truth is not sufficiently evidenced yet;
- `NOT_IMPLEMENTED` — runner/system-under-test does not yet implement domain;
- `SKIPPED_NOT_GOLD` — intentionally excluded from freeze score due evidence/adjudication state.

No generic `FAILED` result is allowed when a more specific classification can be determined.

# Case result

A case is:
- `PASS` only if every required gold assertion passes;
- `FAIL` if any required gold assertion fails;
- `BLOCKED` if no assertion failed but at least one required assertion is blocked by evidence;
- `NON_GOLD_EXECUTED` for seed/candidate research execution.

# Criticality

`critical` risk assertions cannot be averaged away.

Freeze condition:
- critical gold case failures = **0**;
- critical false automatic merge = **0**;
- critical false Work/Version relationship = **0**.

A 99.9% aggregate score does not pass if one critical destructive identity assertion fails.

# Adjudication overrides

Historical tranche markdown is never rewritten merely to hide previous uncertainty.

A versioned adjudication file can supersede:
- expected semantic outcome;
- status;
- evidence additions;
- controlling specification.

The runner resolves the newest valid adjudication before execution and records the adjudication version in results.

# Search assertions

Search manifests record:
- query text;
- query locale/script where known;
- target CAS entity/ref;
- expected maximum rank;
- query class (`native_exact`, `sourced_transliteration`, `generated_transliteration`, `fuzzy_typo`, `collision`, etc.);
- evidence/source for expected name/alias when required.

Search results record actual rank and timing.

# Performance recording

The runner records for relevant assertions:
- duration;
- dataset version;
- index/search configuration version;
- warm/cold classification where benchmarked;
- service/rule version.

Performance failures never change expected semantic truth.

# Reproducibility

Every validation run writes a machine-readable report containing:
- run ID;
- Git commit SHA;
- corpus manifest hashes;
- schema version;
- adjudication version;
- source snapshot/test-fixture version;
- rule-engine version;
- search-index version;
- timestamps;
- environment;
- per-assertion results;
- aggregate metrics by cohort/risk/language/domain.

# Output artifacts

Expected research artifacts:
- `validation/results/<run-id>.json`;
- human-readable summary Markdown;
- cohort pass table;
- critical-failure list;
- search ranking/latency summary;
- evidence-blocked list.

Results may later move to CI artifacts rather than being permanently committed, but a freeze-candidate run and summary must be preserved.

# Anti-gaming rules

The runner must not:
- ignore unknown operators;
- silently skip failing gold assertions;
- count non-gold cases as passing evidence;
- rewrite expected answers from actual engine output;
- choose a different entity target because the intended one ranked poorly;
- drop outlier latency results without documented benchmark policy;
- convert `BLOCKED_EVIDENCE` into PASS.

# Minimal research implementation

A pre-freeze runner may be implemented in Python for speed of research iteration. It should:
- use JSON Schema validation;
- keep operators in a versioned registry;
- emit deterministic JSON results;
- expose a model-adapter interface so tests can first run against fixtures/reference semantic graphs and later against the real backend.

Production language/runtime is not dictated by this research runner.

# Freeze acceptance

Gate F in `V1_FREEZE_READINESS.md` passes only when:
1. all gold cases are schema-valid and machine-readable;
2. runner handles every frozen V1 assertion domain/operator;
3. freeze-candidate execution is reproducible;
4. critical failures are zero;
5. blocked evidence is outside required gold quota or resolved;
6. failure classifications feed the readiness report rather than being manually waived without record.