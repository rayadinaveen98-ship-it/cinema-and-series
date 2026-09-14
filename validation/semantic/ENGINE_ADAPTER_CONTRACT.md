# Production Engine Semantic Adapter Contract

Status: FROZEN-CANDIDATE VALIDATION CONTRACT

This contract defines how future Cinema and Series engines expose observed state to the validation harness. It does **not** authorize production implementation before the V1 freeze gate.

## Purpose

The evidence corpus must be able to test the real Identity, Relationship, Release, Canonicalization, Review-Routing and Search implementations without coupling the benchmark to internal database tables or framework choices.

The adapter therefore exports a neutral observation document conforming to `engine-observation.schema.json`.

## Hard separation from reference fixtures

Production/implementation adapters MUST NOT:

- read `reference-state-*.jsonl` while calculating engine output;
- derive expected answers from corpus `expected_outcome` fields;
- modify engine results to make assertions pass;
- translate `NOT_IMPLEMENTED` into `PASS`;
- use test-only identity keys as production CAS IDs.

Reference states are an independent oracle for benchmark development. Production observations must come only from the implementation under test and its seeded test data.

## Required adapter metadata

Every observation records:

- adapter name;
- adapter version;
- source-code revision / commit SHA;
- generation timestamp;
- case ID.

This makes every benchmark result reproducible and prevents an unversioned engine response from becoming acceptance evidence.

## Local refs

The benchmark uses case-local references such as `work_jersey_telugu_2019`.

A production adapter is responsible for mapping those test fixture references to actual seeded CAS entities. The observation may additionally expose the actual `cas_entity_id`, but benchmark assertions must remain valid even if CAS UUIDs change between disposable test databases.

## Set-aware assertion bindings

A semantic binding always retains the existing singular anchors `subject_ref` and, where required by the operator, `object_ref`.

For assertions that genuinely describe more than one subject or object, bindings may additionally provide:

- `subject_refs` — additional subjects governed by the same assertion;
- `object_refs` — additional objects governed by the same assertion.

These arrays are **additive**, not replacements for required singular bindings. This preserves backward compatibility while allowing the benchmark to test complete groups instead of choosing a convenient representative pair.

Set-aware evaluation rules are strict:

- `same_identity` requires every bound entity to agree at the requested identity scope;
- `different_identity` requires every bound entity to have a distinct exact identity;
- `has_relationship` requires every bound subject/object pair in the assertion to exist;
- `does_not_have_relationship` requires none of those subject/object pairs to exist;
- field, non-overwrite, claim-preservation, search and review assertions with additional subjects must hold for every bound subject;
- a partially satisfied set is a failure, never a partial PASS.

This capability exists specifically for cases such as merger predecessors, combined presentations, three-work identity boundaries and restoration properties that apply across a collection. It must not be used to broaden an assertion beyond what its evidence supports.

The observation schema itself remains normalized: adapters emit individual entities, relationships, fields, claims and guards. Set semantics are evaluated by the benchmark against those normalized observations.

## Identity outputs

For every relevant entity, emit:

- `exact_identity_key` — stable within the observation and equal only when two refs resolve to the same durable entity;
- `underlying_work_key` — equal for Versions/manifestations that belong to the same Work;
- `series_lineage_key` — optional lineage key for explicitly linked program/revival families.

A Version and Work must never share `exact_identity_key` merely because they share `underlying_work_key`.

## Relationship outputs

Emit normalized triples:

`subject_ref + predicate + object_ref`

Predicates must use benchmark/domain vocabulary, for example:

- `remake_of`
- `adaptation_of`
- `based_on`
- `version_of`
- `revival_or_continuation_of`
- `release_of_version`
- `produced_by`
- `distributed_by`
- `formed_from`
- `integrated_from`

An adapter may translate internal relation names into this vocabulary, but the translation table must be version-controlled.

## Field/canonical outputs

Fields are emitted as:

`subject_ref + predicate + value`

Values may be scalar, object or array. Precision must be preserved. A year-only release window cannot be exported as a fabricated date.

## Claim/canonicalization outputs

Where an assertion tests preserved disagreement/history, the adapter exports `preserved_claims` rather than only a chosen canonical value.

Non-overwrite invariants are exported as `non_overwrite_guards`. These communicate that a newer event/version/claim did not erase an older independent fact.

## Review routing

If the real engine determines a candidate must enter human review, the affected local ref is emitted in `review_routes`.

A result that should route to review but is silently auto-merged is a benchmark failure.

## Search

Search observations use `search_resolutions` for semantic case assertions. The separate 500-query search benchmark remains the authoritative ranking/recall gate.

## Failure classification

The comparison harness classifies a mismatch according to evidence and implementation state:

- `FAIL_MODEL` — expected behavior cannot be represented by the frozen-candidate model;
- `FAIL_ENGINE` — model supports it but implementation behavior is wrong;
- `FAIL_DATA` — fixture/ingested observation lacks or contradicts required data;
- `BLOCKED_EVIDENCE` — evidence is insufficient to adjudicate;
- `NOT_IMPLEMENTED` — required engine path/evaluator does not exist;
- `PASS` — observed behavior satisfies the assertion.

No failure class may be silently converted into a weaker success state.

## CI rollout

1. Reference-graph benchmark remains active now.
2. When disposable engine implementations exist, an engine adapter exports observations.
3. Observation schema validation runs first.
4. The same semantic assertions are executed against those observations.
5. Reference and production-engine result counts are reported separately.
6. V1 freeze requires the acceptance thresholds defined by the QA/data-readiness specifications, not merely a green reference benchmark.
