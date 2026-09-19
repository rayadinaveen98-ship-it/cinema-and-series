#!/usr/bin/env python3
"""Build a deterministic attestation manifest for the reviewed P1 V3 artifact.

The V3 title projection fingerprint protects catalogue identity and the V3 graph
fingerprint protects normalized recommendation content. This manifest adds the
last layer needed by a production writer: hashes for every reviewed shard JSON,
reviewed SQL, D1-compatible executable SQL, cost manifest, and the preserved
shard-0 delta-only top-up.

The manifest is generated only after the 16-way repartition and write-cost plan
have passed. Its own file SHA-256 can then be locked by the production writer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def require_hex64(value: object, label: str) -> str:
    text = str(value or "")
    if not HEX64.fullmatch(text):
        raise ValueError(f"{label} must be a lowercase SHA-256 hex digest")
    return text


def build_manifest(
    root: Path,
    *,
    expected_projection_sha256: str,
    expected_candidates: int,
    shard_count: int = 16,
) -> dict[str, Any]:
    expected_projection_sha256 = require_hex64(expected_projection_sha256, "projection sha256")
    summary_path = root / "recommendation-metadata-materialization-v3-summary.json"
    projection_path = root / "recommendation-projection-manifest.json"
    cost_plan_path = root / "write-cost-plan-v3.json"
    summary = load_json(summary_path)
    projection = load_json(projection_path)
    cost_plan = load_json(cost_plan_path)

    if summary.get("state") != "complete" or summary.get("production_mutation") is not False:
        raise ValueError("V3 summary is not complete/read-only")
    projection_summary = summary.get("projection_manifest") or {}
    if projection_summary.get("sha256") != expected_projection_sha256:
        raise ValueError("V3 summary projection fingerprint mismatch")
    if projection.get("sha256") != expected_projection_sha256:
        raise ValueError("V3 projection artifact fingerprint mismatch")
    if int(projection.get("candidate_count") or 0) != expected_candidates:
        raise ValueError("V3 projection candidate count mismatch")
    if int((summary.get("totals") or {}).get("candidate_titles") or 0) != expected_candidates:
        raise ValueError("V3 materialization candidate count mismatch")
    if int(summary.get("physical_shard_count") or 0) != shard_count:
        raise ValueError("V3 physical shard count mismatch")
    if cost_plan.get("projection_sha256") != expected_projection_sha256:
        raise ValueError("V3 write-cost plan projection fingerprint mismatch")

    global_materialization_sha256 = require_hex64(
        summary.get("materialization_sha256"), "global materialization sha256"
    )
    summary_shards = {
        int(row["shard"]): row for row in (summary.get("shards") or [])
        if isinstance(row, dict) and "shard" in row
    }
    if set(summary_shards) != set(range(shard_count)):
        raise ValueError("V3 summary does not describe every physical shard exactly once")

    planned_costs = cost_plan.get("physical_shard_rows_written") or {}
    shard_entries: list[dict[str, Any]] = []
    for shard in range(shard_count):
        report_path = root / f"recommendation-materialization-physical-shard-{shard}.json"
        sql_path = root / f"recommendation-materialization-physical-shard-{shard}.sql"
        executable_path = root / "executable" / f"physical-shard-{shard}.sql"
        cost_path = root / "executable" / f"physical-shard-{shard}-cost.json"
        for path in (report_path, sql_path, executable_path, cost_path):
            if not path.exists():
                raise ValueError(f"missing V3 shard artifact: {path}")

        report = load_json(report_path)
        cost = load_json(cost_path)
        shard_materialization_sha256 = require_hex64(
            report.get("materialization_sha256"), f"physical shard {shard} materialization sha256"
        )
        if report.get("global_materialization_sha256") != global_materialization_sha256:
            raise ValueError(f"physical shard {shard} global graph fingerprint mismatch")
        if int(report.get("shard_index", -1)) != shard or int(report.get("shard_count") or 0) != shard_count:
            raise ValueError(f"physical shard {shard} identity mismatch")
        if (report.get("projection_manifest") or {}).get("sha256") != expected_projection_sha256:
            raise ValueError(f"physical shard {shard} projection mismatch")
        if summary_shards[shard].get("materialization_sha256") != shard_materialization_sha256:
            raise ValueError(f"physical shard {shard} summary graph fingerprint mismatch")

        sql = sql_path.read_text(encoding="utf-8")
        if f"-- Projection manifest SHA-256: {expected_projection_sha256}" not in sql:
            raise ValueError(f"physical shard {shard} reviewed SQL lacks projection binding")
        if f"-- Global materialization SHA-256: {global_materialization_sha256}" not in sql:
            raise ValueError(f"physical shard {shard} reviewed SQL lacks global graph binding")
        if f"-- Shard materialization SHA-256: {shard_materialization_sha256}" not in sql:
            raise ValueError(f"physical shard {shard} reviewed SQL lacks shard graph binding")

        estimated = int(cost.get("estimated_rows_written") or 0)
        if estimated <= 0:
            raise ValueError(f"physical shard {shard} has invalid write-cost estimate")
        if int(planned_costs.get(str(shard), 0)) != estimated:
            raise ValueError(f"physical shard {shard} cost plan mismatch")

        shard_entries.append({
            "shard": shard,
            "materialization_sha256": shard_materialization_sha256,
            "candidate_titles": int((report.get("stats") or {}).get("candidate_titles") or 0),
            "genre_relations": int((report.get("stats") or {}).get("emitted_genre_relations") or 0),
            "credit_relations": int((report.get("stats") or {}).get("emitted_credit_relations") or 0),
            "estimated_rows_written": estimated,
            "report_sha256": file_sha256(report_path),
            "reviewed_sql_sha256": file_sha256(sql_path),
            "executable_sql_sha256": file_sha256(executable_path),
            "cost_manifest_sha256": file_sha256(cost_path),
        })

    topup_sql = root / "executable" / "existing-shard-0-topup.sql"
    topup_cost_path = root / "executable" / "existing-shard-0-topup-cost.json"
    if not topup_sql.exists() or not topup_cost_path.exists():
        raise ValueError("missing existing shard-0 top-up artifact")
    topup_cost = load_json(topup_cost_path)
    topup_estimated = int(topup_cost.get("estimated_rows_written") or 0)
    if topup_estimated != int(cost_plan.get("existing_shard_0_topup_rows_written") or 0):
        raise ValueError("existing shard-0 top-up cost plan mismatch")

    total_titles = sum(row["candidate_titles"] for row in shard_entries)
    total_genres = sum(row["genre_relations"] for row in shard_entries)
    total_credits = sum(row["credit_relations"] for row in shard_entries)
    totals = summary.get("totals") or {}
    if total_titles != int(totals.get("candidate_titles") or 0):
        raise ValueError("physical shard title totals do not match V3 summary")
    if total_genres != int(totals.get("emitted_genre_relations") or 0):
        raise ValueError("physical shard genre totals do not match V3 summary")
    if total_credits != int(totals.get("emitted_credit_relations") or 0):
        raise ValueError("physical shard credit totals do not match V3 summary")

    return {
        "schema_version": "recommendation-metadata-v3-artifact-attestation",
        "projection_sha256": expected_projection_sha256,
        "candidate_count": expected_candidates,
        "global_materialization_sha256": global_materialization_sha256,
        "summary_sha256": file_sha256(summary_path),
        "projection_manifest_file_sha256": file_sha256(projection_path),
        "write_cost_plan_sha256": file_sha256(cost_plan_path),
        "lineage": summary.get("lineage") or {},
        "totals": totals,
        "physical_shards": shard_entries,
        "existing_shard_0_topup": {
            "estimated_rows_written": topup_estimated,
            "executable_sql_sha256": file_sha256(topup_sql),
            "cost_manifest_sha256": file_sha256(topup_cost_path),
        },
        "already_present_parent_partitions": cost_plan.get("already_present_parent_partitions") or [],
        "remaining_full_physical_shards": cost_plan.get("remaining_full_physical_shards") or [],
        "hard_ceiling": int(cost_plan.get("hard_ceiling") or 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--expected-projection-sha256", required=True)
    parser.add_argument("--expected-candidates", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=16)
    parser.add_argument("--out", required=True)
    parser.add_argument("--sha-out")
    args = parser.parse_args()

    root = Path(args.root)
    manifest = build_manifest(
        root,
        expected_projection_sha256=args.expected_projection_sha256,
        expected_candidates=args.expected_candidates,
        shard_count=args.shard_count,
    )
    out = Path(args.out)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = file_sha256(out)
    if args.sha_out:
        Path(args.sha_out).write_text(digest + "\n", encoding="utf-8")
    print("P1_V3_ARTIFACT_ATTESTATION_SHA256=" + digest)
    print("P1_V3_GRAPH_SHA256=" + manifest["global_materialization_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
