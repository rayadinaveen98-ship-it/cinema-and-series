#!/usr/bin/env python3
"""Build one authoritative read-only snapshot of P1 production population state.

The workflow that calls this script performs only SELECT probes against D1 and
restores the immutable reviewed V3 artifact. This module then combines those
inputs into a compact JSON + Markdown checkpoint suitable for humans and CI.

It deliberately does not connect to Cloudflare or GitHub itself and cannot
mutate production state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

OPERATION_ORDER = ["topup", "1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15"]
EXPECTED_PROJECTION_SHA256 = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
EXPECTED_GRAPH_SHA256 = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"
EXPECTED_TARGET = {
    "recommendation_titles": 16380,
    "genres": 612,
    "people": 37964,
    "title_genres": 16489,
    "title_credits": 70551,
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def d1_rows(payload: Any) -> list[dict[str, Any]]:
    batches = payload if isinstance(payload, list) else [payload]
    rows: list[dict[str, Any]] = []
    for batch in batches:
        if isinstance(batch, dict):
            rows.extend(row for row in (batch.get("results") or []) if isinstance(row, dict))
    return rows


def exact_pairs(payload: Any) -> set[tuple[str, str]]:
    return {
        (str(row.get("id") or ""), str(row.get("wikidata_qid") or ""))
        for row in d1_rows(payload)
    }


def cleanup_state(movies: Any, catalogue: Any, series: Any) -> str:
    movie = exact_pairs(movies)
    catalogue_pairs = exact_pairs(catalogue)
    series_pairs = exact_pairs(series)

    before_movie = {("wd-Q3049630", "Q3049630")}
    before_catalogue = {("wd-Q3146368", "Q3146368")}
    before_series = {
        ("series-wd-Q3049630", "Q3049630"),
        ("series-wd-Q3146368", "Q3146368"),
    }
    after_series = {("series-wd-Q3146368", "Q3146368")}

    if movie == before_movie and catalogue_pairs == before_catalogue and series_pairs == before_series:
        return "needed"
    if not movie and not catalogue_pairs and series_pairs == after_series:
        return "complete"
    return "unsafe"


def operation_costs(attestation: dict[str, Any]) -> dict[str, int]:
    if attestation.get("projection_sha256") != EXPECTED_PROJECTION_SHA256:
        raise ValueError("V3 attestation projection fingerprint mismatch")
    if attestation.get("global_materialization_sha256") != EXPECTED_GRAPH_SHA256:
        raise ValueError("V3 attestation graph fingerprint mismatch")

    costs = {
        "topup": int((attestation.get("existing_shard_0_topup") or {}).get("estimated_rows_written") or 0)
    }
    for row in attestation.get("physical_shards") or []:
        shard = str(row.get("shard"))
        if shard in OPERATION_ORDER:
            costs[shard] = int(row.get("estimated_rows_written") or 0)
    if set(costs) != set(OPERATION_ORDER):
        missing = sorted(set(OPERATION_ORDER) - set(costs))
        raise ValueError(f"V3 attestation missing operation costs: {missing}")
    return costs


def read_operation_states(operation_dir: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(operation_dir)
    states: dict[str, dict[str, Any]] = {}
    for operation in OPERATION_ORDER:
        path = root / f"{operation}-result.json"
        if not path.exists():
            raise ValueError(f"missing status result for P1 operation {operation}")
        result = load_json(path)
        if result.get("projection_sha256") != EXPECTED_PROJECTION_SHA256:
            raise ValueError(f"operation {operation} status fingerprint mismatch")
        state = str(result.get("state") or "")
        if state not in {"complete", "not_started", "unsafe_partial", "unsafe_overfilled"}:
            raise ValueError(f"operation {operation} has unexpected state {state!r}")
        states[operation] = result
    return states


def plan_next_operation(states: dict[str, dict[str, Any]]) -> tuple[str, str]:
    """Return (overall_state, next_operation).

    Completed operations must form a strict prefix of the locked operation
    order. A partial/overfilled operation or a later completed operation after
    an earlier gap is fail-closed and reported as unsafe.
    """
    first_gap: str | None = None
    for operation in OPERATION_ORDER:
        state = str(states[operation]["state"])
        if state.startswith("unsafe_"):
            return "unsafe", operation
        if state == "not_started" and first_gap is None:
            first_gap = operation
        elif state == "complete" and first_gap is not None:
            return "unsafe_out_of_order", first_gap

    if first_gap is None:
        return "operations_complete", "complete"
    return "in_progress", first_gap


def single_count_row(payload: Any) -> dict[str, int]:
    rows = d1_rows(payload)
    if len(rows) != 1:
        raise ValueError(f"expected exactly one production-count row, got {len(rows)}")
    row = rows[0]
    keys = [
        "recommendation_titles",
        "genres",
        "people",
        "title_genres",
        "title_credits",
        "orphan_title_genres_title",
        "orphan_title_genres_genre",
        "orphan_title_credits_title",
        "orphan_title_credits_person",
        "invalid_provenance",
    ]
    return {key: int(row.get(key) or 0) for key in keys}


def guard_state(payload: Any) -> dict[str, Any]:
    rows = d1_rows(payload)
    if len(rows) > 1:
        raise ValueError("daily quota guard returned more than one row")
    if not rows:
        return {"state": "available", "row": None}
    row = rows[0]
    return {
        "state": "used",
        "row": {
            "utc_date": str(row.get("utc_date") or ""),
            "shard_index": int(row.get("shard_index") if row.get("shard_index") is not None else -1),
            "projection_sha256": str(row.get("projection_sha256") or ""),
            "workflow_run_id": str(row.get("workflow_run_id") or ""),
            "created_at": str(row.get("created_at") or ""),
        },
    }


def build_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    attestation = load_json(args.attestation)
    costs = operation_costs(attestation)
    states = read_operation_states(args.operation_dir)
    overall_state, next_operation = plan_next_operation(states)
    cleanup = cleanup_state(
        load_json(args.source_movies),
        load_json(args.source_catalogue),
        load_json(args.source_series),
    )
    counts = single_count_row(load_json(args.counts_json))
    guard = guard_state(load_json(args.guard_json))

    health_violations = {
        key: value
        for key, value in counts.items()
        if key.startswith("orphan_") or key == "invalid_provenance"
        if value != 0
    }
    if cleanup == "unsafe" or health_violations:
        overall_state = "unsafe"

    next_cost = None if next_operation == "complete" else costs[next_operation]
    completed = [op for op in OPERATION_ORDER if states[op]["state"] == "complete"]

    return {
        "schema_version": "p1-production-status-v1",
        "projection_sha256": EXPECTED_PROJECTION_SHA256,
        "target_graph_sha256": EXPECTED_GRAPH_SHA256,
        "target": EXPECTED_TARGET,
        "production_counts": counts,
        "source_cleanup_state": cleanup,
        "daily_quota_guard": guard,
        "overall_operation_state": overall_state,
        "completed_operations": completed,
        "completed_operation_count": len(completed),
        "total_operation_count": len(OPERATION_ORDER),
        "next_operation": next_operation,
        "next_operation_estimated_rows_written": next_cost,
        "operation_costs": costs,
        "operation_states": {
            op: {
                "state": states[op]["state"],
                "expected": states[op].get("expected") or {},
                "current": states[op].get("current") or {},
            }
            for op in OPERATION_ORDER
        },
        "health_violations": health_violations,
        "p1_exit_ready": (
            cleanup == "complete"
            and overall_state == "operations_complete"
            and not health_violations
            and all(counts.get(key) == value for key, value in EXPECTED_TARGET.items())
        ),
    }


def render_markdown(snapshot: dict[str, Any]) -> str:
    guard = snapshot["daily_quota_guard"]
    guard_text = "available"
    if guard["state"] == "used":
        row = guard.get("row") or {}
        guard_text = f"used by `{row.get('workflow_run_id', '')}`"

    next_operation = snapshot["next_operation"]
    if next_operation == "complete":
        next_text = "all write operations complete; final verification is next"
    else:
        next_text = (
            f"`{next_operation}` (~{snapshot['next_operation_estimated_rows_written']:,} D1 rows)"
        )

    counts = snapshot["production_counts"]
    lines = [
        "# P1 Production Status Snapshot",
        "",
        f"- source cleanup: **{snapshot['source_cleanup_state']}**",
        f"- operation state: **{snapshot['overall_operation_state']}**",
        f"- completed operations: **{snapshot['completed_operation_count']} / {snapshot['total_operation_count']}**",
        f"- next operation: {next_text}",
        f"- current UTC quota day: **{guard_text}**",
        f"- P1 exit ready: **{'yes' if snapshot['p1_exit_ready'] else 'no'}**",
        "",
        "## Production recommendation graph counts",
        "",
        "| Metric | Current | Final target |",
        "|---|---:|---:|",
    ]
    for key, target in EXPECTED_TARGET.items():
        lines.append(f"| {key} | {counts[key]:,} | {target:,} |")

    lines.extend(["", "## Operation state", "", "| Operation | State | Estimated rows |", "|---|---|---:|"])
    for op in OPERATION_ORDER:
        lines.append(f"| {op} | {snapshot['operation_states'][op]['state']} | {snapshot['operation_costs'][op]:,} |")

    if snapshot["health_violations"]:
        lines.extend(["", "## Health violations", ""])
        for key, value in sorted(snapshot["health_violations"].items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.extend(["", "Health probes: **zero orphan/provenance violations detected**."])

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--operation-dir", required=True)
    parser.add_argument("--counts-json", required=True)
    parser.add_argument("--guard-json", required=True)
    parser.add_argument("--source-movies", required=True)
    parser.add_argument("--source-catalogue", required=True)
    parser.add_argument("--source-series", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    snapshot = build_snapshot(args)
    Path(args.out_json).write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.out_md).write_text(render_markdown(snapshot), encoding="utf-8")
    print("P1_PRODUCTION_STATUS=" + json.dumps({
        "source_cleanup_state": snapshot["source_cleanup_state"],
        "overall_operation_state": snapshot["overall_operation_state"],
        "completed_operation_count": snapshot["completed_operation_count"],
        "next_operation": snapshot["next_operation"],
        "next_operation_estimated_rows_written": snapshot["next_operation_estimated_rows_written"],
        "p1_exit_ready": snapshot["p1_exit_ready"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
