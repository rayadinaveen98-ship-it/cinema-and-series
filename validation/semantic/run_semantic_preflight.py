#!/usr/bin/env python3
"""Semantic preflight for Cinema and Series validation assertions.

This is deliberately NOT an engine-pass runner. It verifies that every assertion
uses a known semantic operator and measures whether the assertion has enough
structured bindings to be executed automatically once a runtime adapter exists.

A missing binding is reported as validation debt, never as PASS.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATION = ROOT / "validation"
CONTRACT_PATH = VALIDATION / "semantic" / "operator-contract-v0.1.json"


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

    manifest_paths = sorted(Path(p) for p in glob.glob(str(VALIDATION / "corpus-tranche-*.jsonl")))
    if not manifest_paths:
        print("FAIL_SEMANTIC_PREFLIGHT: no corpus manifests found")
        return 1

    errors: list[str] = []
    operator_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    readiness_counts: Counter[str] = Counter()
    missing_binding_counts: Counter[str] = Counter()
    missing_by_operator: defaultdict[str, Counter[str]] = defaultdict(Counter)
    assertion_total = 0
    case_total = 0

    for path in manifest_paths:
        for line_number, case in load_jsonl(path):
            case_total += 1
            case_id = case.get("case_id", f"{path.name}:{line_number}")
            entities = case.get("entities") or []
            entity_refs = {e.get("local_ref") for e in entities if e.get("local_ref")}
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

                operator_counts[operator] += 1
                domain_counts[domain] += 1

                required = operators[operator].get("required_bindings", [])
                missing = [name for name in required if not assertion.get(name)]

                for binding in missing:
                    missing_binding_counts[binding] += 1
                    missing_by_operator[operator][binding] += 1

                # If a case declares entities, any provided local refs must resolve.
                if entity_refs:
                    for ref_key in ("subject_ref", "object_ref"):
                        ref = assertion.get(ref_key)
                        if ref and ref not in entity_refs:
                            errors.append(
                                f"{case_id}/{assertion_id}: {ref_key}={ref!r} not present in case entities"
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
    print(f"cases={case_total}")
    print(f"assertions={assertion_total}")
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
