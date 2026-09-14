#!/usr/bin/env python3
"""Validate Cinema and Series search benchmark JSONL manifests.

Research/QA tooling only. This validates search-query records, query-id uniqueness,
and basic benchmark invariants. It does not implement search ranking.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: jsonschema. Install with "
        "`python -m pip install -r validation/requirements.txt`."
    ) from exc

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "search-query.schema.json"


def main() -> int:
    try:
        schema: dict[str, Any] = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL_SEARCH_MANIFEST: cannot load schema: {exc}", file=sys.stderr)
        return 2

    manifests = sorted(ROOT.glob("queries-*.jsonl"))
    if not manifests:
        print("FAIL_SEARCH_MANIFEST: no queries-*.jsonl files found", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    seen_ids: dict[str, tuple[Path, int]] = {}
    query_class_counts: Counter[str] = Counter()
    script_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    derivation_counts: Counter[str] = Counter()
    total = 0

    for path in manifests:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, start=1):
                raw = raw.strip()
                if not raw or raw.startswith("#"):
                    continue
                total += 1
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}:{line_number}: invalid JSON: {exc}")
                    continue

                schema_errors = sorted(
                    validator.iter_errors(record), key=lambda err: list(err.absolute_path)
                )
                for error in schema_errors:
                    loc = ".".join(str(p) for p in error.absolute_path)
                    errors.append(
                        f"{path}:{line_number}: schema {loc or '<root>'}: {error.message}"
                    )

                query_id = record.get("query_id")
                if query_id in seen_ids:
                    first = seen_ids[query_id]
                    errors.append(
                        f"{path}:{line_number}: duplicate query_id {query_id}; "
                        f"first seen at {first[0]}:{first[1]}"
                    )
                elif query_id:
                    seen_ids[query_id] = (path, line_number)

                derivation = record.get("derivation")
                query_class = record.get("query_class")
                if derivation == "generated_search_only" and query_class in {
                    "native_exact", "latin_exact", "sourced_alias"
                }:
                    errors.append(
                        f"{path}:{line_number}: generated search-only query cannot be "
                        f"classified as sourced/exact ({query_class})"
                    )

                if record.get("expected", {}).get("max_rank", 999) == 1 and record.get(
                    "query_class"
                ) == "same_title_collision":
                    errors.append(
                        f"{path}:{line_number}: ambiguous same-title collision must not "
                        "require a single target at rank 1"
                    )

                query_class_counts[str(query_class)] += 1
                derivation_counts[str(derivation)] += 1
                if record.get("script_code"):
                    script_counts[str(record["script_code"])] += 1
                if record.get("language_code"):
                    language_counts[str(record["language_code"])] += 1

    if errors:
        print("FAIL_SEARCH_MANIFEST")
        for error in errors:
            print(f"- {error}")
        print(f"{len(errors)} validation error(s).", file=sys.stderr)
        return 1

    print("PASS_SEARCH_MANIFEST")
    print(f"manifests={len(manifests)}")
    print(f"queries={total}")
    print("query_class_counts=" + json.dumps(query_class_counts, sort_keys=True))
    print("derivation_counts=" + json.dumps(derivation_counts, sort_keys=True))
    print("script_counts=" + json.dumps(script_counts, sort_keys=True, ensure_ascii=False))
    print("language_counts=" + json.dumps(language_counts, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
