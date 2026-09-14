#!/usr/bin/env python3
"""Print the exact remaining semantic-binding debt by case/assertion.

This report is diagnostic only. It does not change readiness or PASS status.
Run it after run_semantic_preflight.py so schema/overlay integrity has already
been validated.
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

from run_semantic_preflight import CONTRACT_PATH, SEMANTIC, VALIDATION, load_jsonl


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    operators = contract["operators"]

    cases: dict[str, dict] = {}
    for raw_path in sorted(glob.glob(str(VALIDATION / "corpus-tranche-*.jsonl"))):
        path = Path(raw_path)
        for _, case in load_jsonl(path):
            cases[case["case_id"]] = case

    overlays: dict[str, dict] = {}
    for raw_path in sorted(glob.glob(str(SEMANTIC / "bindings-*.jsonl"))):
        path = Path(raw_path)
        for _, overlay in load_jsonl(path):
            overlays[overlay["case_id"]] = overlay

    debt_by_case: defaultdict[str, list[dict]] = defaultdict(list)
    missing_totals: defaultdict[str, int] = defaultdict(int)

    for case_id, case in cases.items():
        overlay = overlays.get(case_id) or {}
        bindings_by_assertion = {
            binding.get("assertion_id"): binding
            for binding in overlay.get("bindings", [])
            if binding.get("assertion_id")
        }

        for assertion in case.get("assertions", []):
            operator = assertion.get("operator")
            if operator == "custom" or operator not in operators:
                continue

            effective = dict(assertion)
            overlay_binding = bindings_by_assertion.get(assertion.get("assertion_id"), {})
            for key in ("subject_ref", "object_ref", "predicate", "identity_scope"):
                if not effective.get(key) and overlay_binding.get(key):
                    effective[key] = overlay_binding[key]

            required = operators[operator].get("required_bindings", [])
            missing = [name for name in required if not effective.get(name)]
            if not missing:
                continue

            for name in missing:
                missing_totals[name] += 1

            debt_by_case[case_id].append(
                {
                    "assertion_id": assertion.get("assertion_id"),
                    "domain": assertion.get("domain"),
                    "operator": operator,
                    "missing": missing,
                }
            )

    assertion_count = sum(len(items) for items in debt_by_case.values())
    print("SEMANTIC_DEBT_REPORT")
    print(f"debt_cases={len(debt_by_case)}")
    print(f"debt_assertions={assertion_count}")
    print("missing_totals=" + json.dumps(dict(sorted(missing_totals.items())), sort_keys=True))

    for case_id in sorted(debt_by_case):
        case = cases[case_id]
        print(
            f"{case_id} | status={case.get('status')} | risk={case.get('risk_level')} | "
            f"title={case.get('title')}"
        )
        for item in debt_by_case[case_id]:
            missing = ",".join(item["missing"])
            print(
                f"  - {item['assertion_id']} | domain={item['domain']} | "
                f"operator={item['operator']} | missing={missing}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
