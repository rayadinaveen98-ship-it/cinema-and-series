#!/usr/bin/env python3
"""Offline, read-only preflight for one reviewed P1 V3 recommendation operation.

This utility validates the immutable reviewed V3 artifact before a future quota day.
It performs no network calls and cannot mutate Cloudflare D1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_ATTESTATION_SHA256 = "8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986"
EXPECTED_PROJECTION_SHA256 = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
EXPECTED_GRAPH_SHA256 = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"
EXPECTED_PARENT_PARTITIONS = [0, 8]
EXPECTED_REMAINING_PHYSICAL_SHARDS = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
ALLOWED_OPERATIONS = ["topup", *[str(value) for value in EXPECTED_REMAINING_PHYSICAL_SHARDS]]
DEFAULT_MAX_ROWS_WRITTEN = 80_000
DEFAULT_FREE_DAILY_ROWS_WRITTEN_LIMIT = 100_000

STATEMENT_KEYS = {
    "genre_upserts": "INSERT INTO genres",
    "people_upserts": "INSERT INTO people",
    "recommendation_titles": "INSERT INTO recommendation_titles",
    "title_credits": "INSERT OR IGNORE INTO title_credits",
    "title_genres": "INSERT OR IGNORE INTO title_genres",
}


class PreflightError(RuntimeError):
    """Raised when the immutable V3 artifact fails a preflight invariant."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PreflightError(f"missing required artifact file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"unable to read JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PreflightError(f"artifact JSON must be an object: {path}")
    return payload


def _require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise PreflightError(f"{label} mismatch: expected={expected!r} actual={actual!r}")


def preflight_operation(
    artifact_dir: Path,
    operation: str,
    *,
    expected_attestation_sha256: str = EXPECTED_ATTESTATION_SHA256,
    expected_projection_sha256: str = EXPECTED_PROJECTION_SHA256,
    expected_graph_sha256: str = EXPECTED_GRAPH_SHA256,
    max_rows_written: int = DEFAULT_MAX_ROWS_WRITTEN,
    free_daily_rows_written_limit: int = DEFAULT_FREE_DAILY_ROWS_WRITTEN_LIMIT,
) -> dict[str, Any]:
    """Validate and summarize one immutable reviewed V3 operation.

    Optional expected-* arguments exist for deterministic unit testing. The CLI does not
    expose them and therefore always uses the locked P1 production fingerprints.
    """

    operation = str(operation).strip()
    if operation not in ALLOWED_OPERATIONS:
        raise PreflightError(
            f"unsupported V3 operation {operation!r}; allowed={','.join(ALLOWED_OPERATIONS)}"
        )
    if max_rows_written <= 0:
        raise PreflightError("max_rows_written must be positive")
    if free_daily_rows_written_limit <= 0:
        raise PreflightError("free_daily_rows_written_limit must be positive")

    root = Path(artifact_dir)
    attestation_path = root / "artifact-attestation-v3.json"
    if not attestation_path.is_file():
        raise PreflightError(f"missing V3 attestation: {attestation_path}")

    attestation_bytes = attestation_path.read_bytes()
    attestation_sha256 = _sha256_bytes(attestation_bytes)
    _require_equal(
        "artifact attestation SHA-256",
        attestation_sha256,
        expected_attestation_sha256,
    )
    attestation = _read_json(attestation_path)

    _require_equal(
        "projection SHA-256",
        str(attestation.get("projection_sha256") or ""),
        expected_projection_sha256,
    )
    _require_equal(
        "global graph SHA-256",
        str(attestation.get("global_materialization_sha256") or ""),
        expected_graph_sha256,
    )
    _require_equal(
        "parent partition reuse",
        attestation.get("already_present_parent_partitions") or [],
        EXPECTED_PARENT_PARTITIONS,
    )
    _require_equal(
        "remaining physical shard plan",
        attestation.get("remaining_full_physical_shards") or [],
        EXPECTED_REMAINING_PHYSICAL_SHARDS,
    )

    executable_dir = root / "executable"
    if operation == "topup":
        entry = attestation.get("existing_shard_0_topup") or {}
        executable_path = executable_dir / "existing-shard-0-topup.sql"
        cost_path = executable_dir / "existing-shard-0-topup-cost.json"
        shard_number: int | None = None
    else:
        shard_number = int(operation)
        entries = {
            int(row.get("shard")): row
            for row in (attestation.get("physical_shards") or [])
            if isinstance(row, dict) and row.get("shard") is not None
        }
        if shard_number not in entries:
            raise PreflightError(f"physical shard {shard_number} absent from V3 attestation")
        if shard_number not in (attestation.get("remaining_full_physical_shards") or []):
            raise PreflightError(f"physical shard {shard_number} is not an authorized V3 write")
        entry = entries[shard_number]
        executable_path = executable_dir / f"physical-shard-{shard_number}.sql"
        cost_path = executable_dir / f"physical-shard-{shard_number}-cost.json"

    if not executable_path.is_file():
        raise PreflightError(f"missing reviewed executable: {executable_path}")
    executable_sha256 = _sha256_bytes(executable_path.read_bytes())
    expected_executable_sha256 = str(entry.get("executable_sql_sha256") or "")
    _require_equal(
        "selected executable SHA-256",
        executable_sha256,
        expected_executable_sha256,
    )

    estimated_rows_written = int(entry.get("estimated_rows_written") or 0)
    if estimated_rows_written <= 0:
        raise PreflightError("reviewed estimated_rows_written must be positive")
    if estimated_rows_written > max_rows_written:
        raise PreflightError(
            "operation exceeds conservative P1 write ceiling: "
            f"{estimated_rows_written}>{max_rows_written}"
        )
    if estimated_rows_written > free_daily_rows_written_limit:
        raise PreflightError(
            "operation exceeds configured free daily rows-written limit: "
            f"{estimated_rows_written}>{free_daily_rows_written_limit}"
        )

    cost = _read_json(cost_path)
    _require_equal(
        "cost manifest projection SHA-256",
        str(cost.get("expected_projection_sha256") or ""),
        expected_projection_sha256,
    )
    _require_equal(
        "cost manifest executable SHA-256",
        str(cost.get("executable_sha256") or ""),
        executable_sha256,
    )
    _require_equal(
        "cost manifest estimated_rows_written",
        int(cost.get("estimated_rows_written") or 0),
        estimated_rows_written,
    )

    statement_counts = cost.get("statement_counts") or {}
    if not isinstance(statement_counts, dict):
        raise PreflightError("cost manifest statement_counts must be an object")
    normalized_statement_counts = {
        label: int(statement_counts.get(sql_key) or 0)
        for label, sql_key in STATEMENT_KEYS.items()
    }
    if any(value < 0 for value in normalized_statement_counts.values()):
        raise PreflightError("cost manifest contains a negative statement count")

    data_statement_count = int(cost.get("data_statement_count") or 0)
    if sum(normalized_statement_counts.values()) != data_statement_count:
        raise PreflightError(
            "cost manifest data_statement_count mismatch: "
            f"sum={sum(normalized_statement_counts.values())} manifest={data_statement_count}"
        )

    if shard_number is not None:
        _require_equal(
            "attested candidate title count",
            normalized_statement_counts["recommendation_titles"],
            int(entry.get("candidate_titles") or 0),
        )
        _require_equal(
            "attested title-genre relation count",
            normalized_statement_counts["title_genres"],
            int(entry.get("genre_relations") or 0),
        )
        _require_equal(
            "attested title-credit relation count",
            normalized_statement_counts["title_credits"],
            int(entry.get("credit_relations") or 0),
        )

    reviewed_free_limit = int(cost.get("free_daily_rows_written_limit") or 0)
    if reviewed_free_limit:
        _require_equal(
            "reviewed free daily rows-written limit",
            reviewed_free_limit,
            free_daily_rows_written_limit,
        )
    expected_headroom = free_daily_rows_written_limit - estimated_rows_written
    reviewed_headroom = int(cost.get("free_daily_rows_written_headroom") or 0)
    if reviewed_headroom:
        _require_equal("reviewed free daily headroom", reviewed_headroom, expected_headroom)

    result: dict[str, Any] = {
        "schema_version": "p1-v3-offline-operation-preflight-v1",
        "operation": operation,
        "physical_shard": shard_number,
        "attestation_sha256": attestation_sha256,
        "projection_sha256": expected_projection_sha256,
        "graph_sha256": expected_graph_sha256,
        "executable": str(executable_path),
        "executable_sha256": executable_sha256,
        "cost_manifest": str(cost_path),
        "estimated_rows_written": estimated_rows_written,
        "conservative_max_rows_written": max_rows_written,
        "conservative_headroom": max_rows_written - estimated_rows_written,
        "free_daily_rows_written_limit": free_daily_rows_written_limit,
        "free_daily_headroom": expected_headroom,
        "data_statement_count": data_statement_count,
        "statement_counts": normalized_statement_counts,
        "authorized_parent_partitions_not_rewritten": EXPECTED_PARENT_PARTITIONS,
        "state": "preflight_ok",
        "production_mutation": False,
    }
    if shard_number is not None:
        result["materialization_sha256"] = str(entry.get("materialization_sha256") or "")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only preflight for one immutable reviewed P1 V3 operation."
    )
    parser.add_argument(
        "--artifact-dir",
        required=True,
        type=Path,
        help="Directory containing artifact-attestation-v3.json and executable/.",
    )
    parser.add_argument(
        "--operation",
        required=True,
        choices=ALLOWED_OPERATIONS,
        help="Reviewed V3 operation to validate.",
    )
    parser.add_argument(
        "--max-rows-written",
        type=int,
        default=DEFAULT_MAX_ROWS_WRITTEN,
        help="Conservative P1 per-operation ceiling; default 80000.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Optional path for the deterministic preflight JSON report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = preflight_operation(
            args.artifact_dir,
            args.operation,
            max_rows_written=args.max_rows_written,
        )
    except PreflightError as exc:
        raise SystemExit(f"P1_V3_OPERATION_PREFLIGHT_FAILED={exc}") from exc

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload, encoding="utf-8")
    print("P1_V3_OPERATION_PREFLIGHT_OK=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
