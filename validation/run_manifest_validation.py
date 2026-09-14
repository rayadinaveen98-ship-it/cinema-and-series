#!/usr/bin/env python3
"""Cinema and Series pre-freeze corpus manifest validator.

Research/QA tooling only. This script does not implement product/domain behavior.
It validates JSONL corpus files against the versioned validation-case schema and
checks cross-file uniqueness invariants.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: jsonschema. Install with "
        "`python -m pip install -r validation/requirements.txt`."
    ) from exc


@dataclass(frozen=True)
class LoadedCase:
    path: Path
    line_number: int
    data: dict[str, Any]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_manifests(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.glob("*.jsonl")
        if p.is_file() and not p.name.startswith("results-")
    )


def load_jsonl(path: Path) -> Iterable[LoadedCase]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid JSON: {exc.msg} "
                    f"(column {exc.colno})"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(
                    f"{path}:{line_number}: each JSONL record must be an object"
                )
            yield LoadedCase(path=path, line_number=line_number, data=value)


def format_schema_error(error: Any) -> str:
    location = ".".join(str(part) for part in error.absolute_path)
    if location:
        return f"{location}: {error.message}"
    return error.message


def validate_case_invariants(case: LoadedCase) -> list[str]:
    errors: list[str] = []
    assertion_ids: set[str] = set()

    for assertion in case.data.get("assertions", []):
        assertion_id = assertion.get("assertion_id")
        if assertion_id in assertion_ids:
            errors.append(
                f"{case.path}:{case.line_number}: duplicate assertion_id "
                f"{assertion_id!r} in {case.data.get('case_id', '<unknown>')}"
            )
        assertion_ids.add(assertion_id)

    evidence_ids: set[str] = set()
    for evidence in case.data.get("evidence", []):
        evidence_id = evidence.get("evidence_id")
        if evidence_id in evidence_ids:
            errors.append(
                f"{case.path}:{case.line_number}: duplicate evidence_id "
                f"{evidence_id!r} in {case.data.get('case_id', '<unknown>')}"
            )
        evidence_ids.add(evidence_id)

    entity_refs = {
        entity.get("local_ref")
        for entity in case.data.get("entities", [])
        if entity.get("local_ref")
    }
    for assertion in case.data.get("assertions", []):
        for field in ("subject_ref", "object_ref"):
            ref = assertion.get(field)
            if ref is not None and entity_refs and ref not in entity_refs:
                errors.append(
                    f"{case.path}:{case.line_number}: assertion "
                    f"{assertion.get('assertion_id')!r} references unknown "
                    f"{field}={ref!r}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Cinema and Series JSONL validation manifests."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing schema and JSONL manifests (default: validation/)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Override validation schema path",
    )
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        default=[],
        help="Validate only the supplied JSONL file(s); may be repeated",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    schema_path = (
        args.schema.resolve()
        if args.schema is not None
        else root / "validation-case.schema.json"
    )

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL_MANIFEST: cannot load schema {schema_path}: {exc}", file=sys.stderr)
        return 2

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    manifests = [p.resolve() for p in args.manifest] or discover_manifests(root)
    if not manifests:
        print(f"FAIL_MANIFEST: no JSONL manifests found in {root}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    seen_case_ids: dict[str, tuple[Path, int]] = {}
    status_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    cohort_counts: dict[str, int] = {}
    total_assertions = 0
    total_cases = 0

    manifest_hashes = {str(path): sha256_file(path) for path in manifests}

    for path in manifests:
        try:
            cases = list(load_jsonl(path))
        except (OSError, ValueError) as exc:
            all_errors.append(str(exc))
            continue

        for case in cases:
            total_cases += 1
            case_id = case.data.get("case_id", "<missing>")

            prior = seen_case_ids.get(case_id)
            if prior is not None:
                all_errors.append(
                    f"{case.path}:{case.line_number}: duplicate case_id {case_id!r}; "
                    f"first seen at {prior[0]}:{prior[1]}"
                )
            else:
                seen_case_ids[case_id] = (case.path, case.line_number)

            schema_errors = sorted(
                validator.iter_errors(case.data), key=lambda err: list(err.absolute_path)
            )
            for error in schema_errors:
                all_errors.append(
                    f"{case.path}:{case.line_number}: schema: "
                    f"{format_schema_error(error)}"
                )

            all_errors.extend(validate_case_invariants(case))

            status = str(case.data.get("status", "<missing>"))
            status_counts[status] = status_counts.get(status, 0) + 1
            risk = str(case.data.get("risk_level", "<missing>"))
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            total_assertions += len(case.data.get("assertions", []))
            for cohort in case.data.get("cohorts", []):
                cohort_counts[cohort] = cohort_counts.get(cohort, 0) + 1

    if all_errors:
        print("FAIL_MANIFEST")
        for error in all_errors:
            print(f"- {error}")
        print(f"\n{len(all_errors)} validation error(s).", file=sys.stderr)
        return 1

    print("PASS_MANIFEST")
    print(f"schema={schema_path}")
    print(f"schema_sha256={sha256_file(schema_path)}")
    print(f"manifests={len(manifests)}")
    print(f"cases={total_cases}")
    print(f"assertions={total_assertions}")
    print("status_counts=" + json.dumps(status_counts, sort_keys=True))
    print("risk_counts=" + json.dumps(risk_counts, sort_keys=True))
    print("cohort_counts=" + json.dumps(cohort_counts, sort_keys=True))
    print("manifest_sha256=" + json.dumps(manifest_hashes, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
