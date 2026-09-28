#!/usr/bin/env python3
"""Build a deterministic, read-only P2 artwork coverage audit snapshot.

The builder combines an exact title-identity export with already-normalized
artwork candidate evidence. It performs no discovery, rights approval, network
request, D1 query, SQL generation, or production mutation.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from scripts import p2_artwork_coverage_audit as audit
except ModuleNotFoundError:  # direct `python scripts/...py` execution
    import p2_artwork_coverage_audit as audit


def _canonical_record(record: dict[str, Any]) -> str:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _load_records(path: Path, key: str) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {key}:
        raise ValueError(f"{path} must contain exactly one top-level field: {key}")
    records = payload.get(key)
    if not isinstance(records, list):
        raise ValueError(f"{path}: {key} must be a list")
    if any(not isinstance(record, dict) for record in records):
        raise ValueError(f"{path}: every {key} record must be an object")
    return records


def build_snapshot(
    titles: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    *,
    territory: str,
    evaluated_at: str,
) -> dict[str, Any]:
    """Assemble and validate a deterministic audit snapshot.

    Candidate duplicates are intentionally preserved. The downstream audit
    reports their frequency; this builder must never silently deduplicate
    evidence or merge distinct rights records.
    """
    title_rows = [deepcopy(record) for record in titles]
    candidate_rows = [deepcopy(record) for record in candidates]

    title_keys: set[tuple[str, str, str]] = set()
    for record in title_rows:
        key = audit.title_identity(record)
        if key in title_keys:
            raise ValueError(f"duplicate title identity: {key}")
        title_keys.add(key)

    for record in candidate_rows:
        key = audit.title_identity(record)
        if key not in title_keys:
            raise ValueError(f"candidate references unknown title identity: {key}")
        audit.validate_candidate_record(record)

    title_rows.sort(key=lambda record: (*audit.title_identity(record), _canonical_record(record)))
    candidate_rows.sort(
        key=lambda record: (
            *audit.title_identity(record),
            *audit.candidate_identity(record),
            _canonical_record(record),
        )
    )

    snapshot = {
        "snapshot_version": audit.SNAPSHOT_VERSION,
        "audit_context": {
            "territory": territory,
            "evaluated_at": evaluated_at,
        },
        "titles": title_rows,
        "candidates": candidate_rows,
    }

    # Run the same contract validation used by the report. This remains fully
    # offline and read-only while preventing the builder and auditor from
    # drifting into incompatible snapshot shapes.
    audit.build_report(snapshot)
    return snapshot


def render_snapshot(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--titles", required=True, type=Path, help="JSON object containing titles list")
    parser.add_argument(
        "--candidates", required=True, type=Path, help="JSON object containing candidates list"
    )
    parser.add_argument("--territory", required=True, help="uppercase two-letter audit territory")
    parser.add_argument(
        "--evaluated-at", required=True, help="UTC RFC3339 audit timestamp: YYYY-MM-DDTHH:MM:SSZ"
    )
    parser.add_argument("--output", required=True, type=Path, help="normalized snapshot output path")
    args = parser.parse_args()

    titles = _load_records(args.titles, "titles")
    candidates = _load_records(args.candidates, "candidates")
    snapshot = build_snapshot(
        titles,
        candidates,
        territory=args.territory,
        evaluated_at=args.evaluated_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_snapshot(snapshot), encoding="utf-8")

    report = audit.build_report(snapshot)
    print(
        "P2 artwork audit snapshot: "
        f"{len(snapshot['titles'])} titles, {len(snapshot['candidates'])} candidates, "
        f"territory={report['audit_context']['territory']}, "
        f"evaluated_at={report['audit_context']['evaluated_at']}, "
        f"sha256={report['input_attestation']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
