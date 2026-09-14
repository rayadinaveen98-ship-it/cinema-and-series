#!/usr/bin/env python3
"""Execute structurally bound assertions against curated semantic reference states.

This is the first executable semantic benchmark layer. It does NOT test production
engines. It tests that our evidence-derived expected assertions are internally
consistent with an independently structured reference graph.

Assertions without a reference-state fixture are outside this runner. Unsupported
operators are NOT_IMPLEMENTED, never PASS.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation"
SEMANTIC = VALIDATION / "semantic"
CONTRACT_PATH = SEMANTIC / "operator-contract-v0.1.json"
BINDING_SCHEMA_PATH = SEMANTIC / "semantic-binding.schema.json"
REFERENCE_SCHEMA_PATH = SEMANTIC / "reference-state.schema.json"


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line_number, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                yield line_number, json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def load_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {}
    for name in sorted(glob.glob(str(VALIDATION / "corpus-tranche-*.jsonl"))):
        path = Path(name)
        for _, case in load_jsonl(path):
            cases[case["case_id"]] = case
    return cases


def load_overlays(errors: list[str]) -> dict[str, dict]:
    schema = json.loads(BINDING_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    overlays: dict[str, dict] = {}
    for name in sorted(glob.glob(str(SEMANTIC / "bindings-*.jsonl"))):
        path = Path(name)
        for line_number, overlay in load_jsonl(path):
            for err in validator.iter_errors(overlay):
                errors.append(f"{path.name}:{line_number}: {err.message}")
            case_id = overlay["case_id"]
            if case_id in overlays:
                errors.append(f"multiple binding overlays for {case_id}")
            overlays[case_id] = overlay
    return overlays


def load_reference_states(errors: list[str]) -> dict[str, dict]:
    schema = json.loads(REFERENCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    states: dict[str, dict] = {}
    for name in sorted(glob.glob(str(SEMANTIC / "reference-state-*.jsonl"))):
        path = Path(name)
        for line_number, state in load_jsonl(path):
            for err in validator.iter_errors(state):
                errors.append(f"{path.name}:{line_number}: {err.message}")
            case_id = state["case_id"]
            if case_id in states:
                errors.append(f"multiple reference states for {case_id}")
            states[case_id] = state
    return states


def effective_assertion(assertion: dict, overlay: dict | None) -> dict:
    result = dict(assertion)
    if not overlay:
        return result
    binding = next(
        (b for b in overlay.get("bindings", []) if b.get("assertion_id") == assertion.get("assertion_id")),
        None,
    )
    if not binding:
        return result
    for key in ("subject_ref", "object_ref", "predicate", "identity_scope"):
        if not result.get(key) and binding.get(key):
            result[key] = binding[key]
    return result


def state_indexes(state: dict):
    entities = {e["local_ref"]: e for e in state.get("entities", [])}
    relationships = {
        (r["subject_ref"], r["predicate"], r["object_ref"])
        for r in state.get("relationships", [])
    }
    fields = {
        (f["subject_ref"], f["predicate"]): f["value"]
        for f in state.get("fields", [])
    }
    preserved_claims = {
        (c["subject_ref"], c["predicate"]): c["values"]
        for c in state.get("preserved_claims", [])
    }
    guards = {
        (g["subject_ref"], g["predicate"])
        for g in state.get("non_overwrite_guards", [])
    }
    review_routes = set(state.get("review_routes", []))
    search_resolutions = set(state.get("search_resolutions", []))
    return entities, relationships, fields, preserved_claims, guards, review_routes, search_resolutions


def evaluate(assertion: dict, state: dict) -> tuple[str, object]:
    operator = assertion["operator"]
    subject = assertion.get("subject_ref")
    obj = assertion.get("object_ref")
    predicate = assertion.get("predicate")
    scope = assertion.get("identity_scope")

    entities, relationships, fields, claims, guards, review_routes, search_resolutions = state_indexes(state)

    if operator in {"same_identity", "different_identity"}:
        if subject not in entities or obj not in entities:
            return "FAIL_DATA", {"reason": "missing_reference_entity", "subject": subject, "object": obj}
        if operator == "different_identity":
            same = entities[subject]["exact_identity_key"] == entities[obj]["exact_identity_key"]
            return ("PASS" if not same else "FAIL_DATA"), {
                "identity_scope": "exact_entity",
                "subject_key": entities[subject]["exact_identity_key"],
                "object_key": entities[obj]["exact_identity_key"],
            }

        scope_to_key = {
            "exact_entity": "exact_identity_key",
            "underlying_work": "underlying_work_key",
            "series_lineage": "series_lineage_key",
        }
        key_name = scope_to_key.get(scope)
        if not key_name:
            return "NOT_IMPLEMENTED", {"reason": "unknown_or_missing_identity_scope", "scope": scope}
        left = entities[subject].get(key_name)
        right = entities[obj].get(key_name)
        if not left or not right:
            return "FAIL_DATA", {"reason": "missing_identity_scope_key", "scope": scope}
        return ("PASS" if left == right else "FAIL_DATA"), {
            "identity_scope": scope,
            "subject_key": left,
            "object_key": right,
        }

    if operator == "has_relationship":
        observed = (subject, predicate, obj) in relationships
        return ("PASS" if observed else "FAIL_DATA"), {
            "relationship": [subject, predicate, obj],
            "observed": observed,
        }

    if operator == "does_not_have_relationship":
        observed = (subject, predicate, obj) in relationships
        return ("PASS" if not observed else "FAIL_DATA"), {
            "relationship": [subject, predicate, obj],
            "observed": observed,
        }

    if operator == "has_value":
        key = (subject, predicate)
        if key not in fields:
            return "FAIL_DATA", {"reason": "field_missing", "field": [subject, predicate]}
        return "PASS", {"value": fields[key]}

    if operator == "does_not_overwrite":
        observed = (subject, predicate) in guards
        return ("PASS" if observed else "FAIL_DATA"), {
            "guard": [subject, predicate],
            "observed": observed,
        }

    if operator == "preserves_claims":
        values = claims.get((subject, predicate))
        observed = isinstance(values, list) and len(values) >= 2
        return ("PASS" if observed else "FAIL_DATA"), {
            "claim_values": values,
            "minimum_required": 2,
        }

    if operator == "supports_multiple":
        field_value = fields.get((subject, predicate))
        if isinstance(field_value, list) and len(field_value) >= 2:
            return "PASS", {"field_values": field_value}
        rel_count = sum(1 for s, p, _ in relationships if s == subject and p == predicate)
        if rel_count >= 2:
            return "PASS", {"relationship_count": rel_count}
        return "FAIL_DATA", {"field_values": field_value, "relationship_count": rel_count}

    if operator == "routes_to_review":
        observed = subject in review_routes
        return ("PASS" if observed else "FAIL_DATA"), {"routed": observed, "subject": subject}

    if operator == "resolves_search":
        observed = subject in search_resolutions
        return ("PASS" if observed else "FAIL_DATA"), {"resolved": observed, "subject": subject}

    if operator == "custom":
        return "NOT_IMPLEMENTED", {"reason": "specialized_evaluator_required"}

    return "NOT_IMPLEMENTED", {"reason": f"operator_not_supported:{operator}"}


def main() -> int:
    errors: list[str] = []
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    cases = load_cases()
    overlays = load_overlays(errors)
    states = load_reference_states(errors)

    for case_id in states:
        if case_id not in cases:
            errors.append(f"reference state points to unknown case {case_id}")

    if errors:
        print("FAIL_REFERENCE_SEMANTICS")
        for error in errors:
            print(f"- {error}")
        return 1

    result_counts: Counter[str] = Counter()
    executed_cases = 0
    executed_assertions = 0
    failure_details: list[dict] = []

    for case_id, state in sorted(states.items()):
        case = cases[case_id]
        overlay = overlays.get(case_id)
        executed_cases += 1

        for assertion in case.get("assertions", []):
            effective = effective_assertion(assertion, overlay)
            operator = effective["operator"]
            required = contract["operators"][operator].get("required_bindings", [])
            missing = [key for key in required if not effective.get(key)]
            if missing:
                result = "NOT_IMPLEMENTED"
                observed = {"reason": "missing_binding", "missing": missing}
            else:
                result, observed = evaluate(effective, state)
            result_counts[result] += 1
            executed_assertions += 1
            if result.startswith("FAIL_"):
                failure_details.append(
                    {
                        "case_id": case_id,
                        "assertion_id": assertion.get("assertion_id"),
                        "operator": operator,
                        "expected": assertion.get("expected"),
                        "observed": observed,
                        "result": result,
                    }
                )

    print("PASS_REFERENCE_SEMANTICS" if not failure_details else "FAIL_REFERENCE_SEMANTICS")
    print(f"reference_cases={executed_cases}")
    print(f"reference_assertions={executed_assertions}")
    print("result_counts=" + json.dumps(dict(sorted(result_counts.items())), sort_keys=True))
    print("adapter=reference_graph_v0.1")
    if failure_details:
        print("failures=" + json.dumps(failure_details, ensure_ascii=False, sort_keys=True))
        return 1
    print(
        "NOTE: PASS here means the assertion is consistent with the curated reference graph; "
        "it is not yet a production-engine pass."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
