#!/usr/bin/env python3
"""Semantic preflight for Cinema and Series validation assertions.

This is deliberately NOT an engine-pass runner. It verifies that every assertion
uses a known semantic operator and measures whether the assertion has enough
structured bindings to be executed automatically once a runtime adapter exists.

Bindings may live directly on corpus assertions or in additive binding overlays.
A missing binding is validation debt, never a PASS.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation"
SEMANTIC = VALIDATION / "semantic"
CONTRACT_PATH = SEMANTIC / "operator-contract-v0.1.json"
BINDING_SCHEMA_PATH = SEMANTIC / "semantic-binding.schema.json"


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


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    operators = contract["operators"]
    binding_schema = json.loads(BINDING_SCHEMA_PATH.read_text(encoding="utf-8"))
    binding_validator = Draft202012Validator(binding_schema)

    manifest_paths = sorted(Path(p) for p in glob.glob(str(VALIDATION / "corpus-tranche-*.jsonl")))
    binding_paths = sorted(Path(p) for p in glob.glob(str(SEMANTIC / "bindings-*.jsonl")))
    if not manifest_paths:
        print("FAIL_SEMANTIC_PREFLIGHT: no corpus manifests found")
        return 1

    errors: list[str] = []
    cases: dict[str, dict] = {}

    for path in manifest_paths:
        for line_number, case in load_jsonl(path):
            case_id = case.get("case_id", f"{path.name}:{line_number}")
            if case_id in cases:
                errors.append(f"duplicate case_id {case_id}")
            cases[case_id] = case

    overlays: dict[str, dict] = {}
    overlay_binding_total = 0
    for path in binding_paths:
        for line_number, overlay in load_jsonl(path):
            schema_errors = sorted(binding_validator.iter_errors(overlay), key=lambda e: list(e.path))
            for err in schema_errors:
                where = ".".join(str(p) for p in err.path) or "<root>"
                errors.append(f"{path.name}:{line_number}:{where}: {err.message}")

            case_id = overlay.get("case_id")
            if not case_id:
                continue
            if case_id not in cases:
                errors.append(f"{path.name}:{line_number}: overlay references unknown case {case_id}")
                continue
            if case_id in overlays:
                errors.append(f"multiple semantic overlays found for {case_id}")
                continue

            entity_refs = [e.get("local_ref") for e in overlay.get("entities", [])]
            if len(entity_refs) != len(set(entity_refs)):
                errors.append(f"{case_id}: duplicate entity local_ref in semantic overlay")

            assertion_ids = {a.get("assertion_id") for a in cases[case_id].get("assertions", [])}
            seen_binding_ids: set[str] = set()
            for binding in overlay.get("bindings", []):
                assertion_id = binding.get("assertion_id")
                overlay_binding_total += 1
                if assertion_id in seen_binding_ids:
                    errors.append(f"{case_id}: duplicate binding for assertion {assertion_id}")
                seen_binding_ids.add(assertion_id)
                if assertion_id not in assertion_ids:
                    errors.append(f"{case_id}: binding references unknown assertion {assertion_id}")
                for ref_key in ("subject_ref", "object_ref"):
                    ref = binding.get(ref_key)
                    if ref and ref not in entity_refs:
                        errors.append(f"{case_id}/{assertion_id}: {ref_key}={ref!r} not declared in overlay entities")

            overlays[case_id] = overlay

    operator_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    readiness_counts: Counter[str] = Counter()
    missing_binding_counts: Counter[str] = Counter()
    missing_by_operator: defaultdict[str, Counter[str]] = defaultdict(Counter)
    assertion_total = 0

    for case_id, case in cases.items():
        case_entities = case.get("entities") or []
        overlay = overlays.get(case_id) or {}
        overlay_entities = overlay.get("entities") or []
        entity_refs = {
            e.get("local_ref")
            for e in (case_entities + overlay_entities)
            if e.get("local_ref")
        }
        bindings_by_assertion = {
            b.get("assertion_id"): b for b in overlay.get("bindings", []) if b.get("assertion_id")
        }
        seen_assertions: set[str] = set()

        for assertion in case.get("assertions", []):
            assertion_total += 1
            assertion_id = assertion.get("assertion_id")
            operator = assertion.get("operator")
            domain = assertion.get("domain")

            if assertion_id in seen_assertions:
                errors.append(f"{case_id}: duplicate assertion_id {assertion_id}")
            seen_assertions.add(assertion_id)

            if operator not in operators:
                errors.append(f"{case_id}/{assertion_id}: unknown operator {operator!r}")
                continue

            effective = dict(assertion)
            overlay_binding = bindings_by_assertion.get(assertion_id, {})
            for key in ("subject_ref", "object_ref", "predicate"):
                overlay_value = overlay_binding.get(key)
                inline_value = assertion.get(key)
                if overlay_value and inline_value and overlay_value != inline_value:
                    errors.append(
                        f"{case_id}/{assertion_id}: overlay {key}={overlay_value!r} conflicts with inline {inline_value!r}"
                    )
                elif overlay_value and not inline_value:
                    effective[key] = overlay_value

            operator_counts[operator] += 1
            domain_counts[domain] += 1

            required = operators[operator].get("required_bindings", [])
            missing = [name for name in required if not effective.get(name)]

            for binding in missing:
                missing_binding_counts[binding] += 1
                missing_by_operator[operator][binding] += 1

            if entity_refs:
                for ref_key in ("subject_ref", "object_ref"):
                    ref = effective.get(ref_key)
                    if ref and ref not in entity_refs:
                        errors.append(
                            f"{case_id}/{assertion_id}: effective {ref_key}={ref!r} not present in declared entities"
                        )

            if operator == "custom":
                readiness_counts["manual_or_specialized"] += 1
            elif missing:
                readiness_counts["needs_binding"] += 1
            else:
                readiness_counts["runtime_ready"] += 1

    if errors:
        print("FAIL_SEMANTIC_PREFLIGHT")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS_SEMANTIC_PREFLIGHT")
    print(f"cases={len(cases)}")
    print(f"assertions={assertion_total}")
    print(f"binding_overlays={len(overlays)}")
    print(f"overlay_bindings={overlay_binding_total}")
    print("readiness_counts=" + json.dumps(dict(sorted(readiness_counts.items())), sort_keys=True))
    print("operator_counts=" + json.dumps(dict(sorted(operator_counts.items())), sort_keys=True))
    print("domain_counts=" + json.dumps(dict(sorted(domain_counts.items())), sort_keys=True))
    print("missing_binding_counts=" + json.dumps(dict(sorted(missing_binding_counts.items())), sort_keys=True))
    print(
        "missing_by_operator="
        + json.dumps(
            {op: dict(sorted(counts.items())) for op, counts in sorted(missing_by_operator.items())},
            sort_keys=True,
        )
    )
    print(
        "NOTE: runtime_ready means structurally executable once a runtime adapter exists; "
        "it does not mean the assertion has passed an engine."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
