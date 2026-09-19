#!/usr/bin/env python3
"""Determine whether one reviewed P1 recommendation shard is complete in D1.

The status probe is intentionally title-scoped. P1 materialization shards are
partitioned by recommendation title, so recommendation_titles/title_genres/
title_credits are sufficient to distinguish an untouched shard from a fully
materialized shard. Any mixed/partial state is treated as unsafe and must not
be auto-advanced.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TITLE_PREFIX = "INSERT INTO recommendation_titles "
TITLE_GENRE_PREFIX = "INSERT OR IGNORE INTO title_genres "
TITLE_CREDIT_PREFIX = "INSERT OR IGNORE INTO title_credits "
TITLE_ID_RE = re.compile(
    r"^INSERT INTO recommendation_titles .*? VALUES \('(?P<title_id>wikidata:Q[0-9]+)'"
)
MAX_D1_SQL_BYTES = 100_000


def build_status_query(sql: str, expected_fingerprint: str) -> tuple[str, dict[str, Any]]:
    lines = sql.splitlines()
    marker = f"-- Projection manifest SHA-256: {expected_fingerprint}"
    if marker not in lines:
        raise ValueError("reviewed shard is not bound to the expected projection fingerprint")

    title_ids: list[str] = []
    title_genres = 0
    title_credits = 0
    for raw in lines:
        line = raw.strip()
        if line.startswith(TITLE_PREFIX):
            match = TITLE_ID_RE.match(line)
            if not match:
                raise ValueError(f"unable to parse recommendation title id: {line[:160]}")
            title_ids.append(match.group("title_id"))
        elif line.startswith(TITLE_GENRE_PREFIX):
            title_genres += 1
        elif line.startswith(TITLE_CREDIT_PREFIX):
            title_credits += 1

    if not title_ids:
        raise ValueError("reviewed shard contains no recommendation titles")
    if len(title_ids) != len(set(title_ids)):
        raise ValueError("reviewed shard contains duplicate recommendation title ids")

    # Keep the title literals in one reusable CTE instead of repeating the
    # entire IN-list three times. Production shards contain ~1.7k titles; the
    # repeated form can cross D1's SQL statement-size limit even though the
    # underlying status probe is small and read-only.
    values = ",".join(f"('{title_id}')" for title_id in title_ids)
    query = (
        f"WITH shard_ids(id) AS (VALUES {values}) "
        "SELECT "
        "(SELECT COUNT(*) FROM recommendation_titles r JOIN shard_ids s ON s.id=r.id) AS titles, "
        "(SELECT COUNT(*) FROM title_genres g JOIN shard_ids s ON s.id=g.title_id) AS title_genres, "
        "(SELECT COUNT(*) FROM title_credits c JOIN shard_ids s ON s.id=c.title_id) AS title_credits;"
    )
    query_bytes = len(query.encode("utf-8"))
    if query_bytes > MAX_D1_SQL_BYTES:
        raise ValueError("generated shard status query exceeds D1 SQL statement limit")

    meta: dict[str, Any] = {
        "schema_version": "p1-shard-status-v2",
        "projection_sha256": expected_fingerprint,
        "expected": {
            "titles": len(title_ids),
            "title_genres": title_genres,
            "title_credits": title_credits,
        },
        "title_id_count": len(title_ids),
        "query_bytes": query_bytes,
    }
    return query, meta


def d1_single_row(payload: Any) -> dict[str, Any]:
    batches = payload if isinstance(payload, list) else [payload]
    rows: list[dict[str, Any]] = []
    for batch in batches:
        if isinstance(batch, dict):
            rows.extend(row for row in (batch.get("results") or []) if isinstance(row, dict))
    if len(rows) != 1:
        raise ValueError(f"expected one D1 result row, received {len(rows)}")
    return rows[0]


def evaluate_status(meta: dict[str, Any], payload: Any) -> dict[str, Any]:
    expected = {key: int(value) for key, value in (meta.get("expected") or {}).items()}
    required = ("titles", "title_genres", "title_credits")
    if set(expected) != set(required):
        raise ValueError("shard status metadata has an unexpected expected-count shape")

    row = d1_single_row(payload)
    current = {key: int(row.get(key) or 0) for key in required}

    if all(current[key] == expected[key] for key in required):
        state = "complete"
    elif all(current[key] == 0 for key in required):
        state = "not_started"
    else:
        overfilled = {
            key: {"expected": expected[key], "current": current[key]}
            for key in required
            if current[key] > expected[key]
        }
        state = "unsafe_partial"
        if overfilled:
            state = "unsafe_overfilled"

    return {
        "schema_version": "p1-shard-status-evaluation-v1",
        "state": state,
        "expected": expected,
        "current": current,
        "projection_sha256": meta.get("projection_sha256"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan")
    plan.add_argument("--input", required=True)
    plan.add_argument("--expected-fingerprint", required=True)
    plan.add_argument("--query-out", required=True)
    plan.add_argument("--meta-out", required=True)

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--meta", required=True)
    evaluate.add_argument("--d1-json", required=True)
    evaluate.add_argument("--state-out", required=True)
    evaluate.add_argument("--result-out")

    args = parser.parse_args()

    if args.command == "plan":
        sql = Path(args.input).read_text(encoding="utf-8")
        query, meta = build_status_query(sql, args.expected_fingerprint)
        query_path = Path(args.query_out)
        meta_path = Path(args.meta_out)
        query_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        query_path.write_text(query + "\n", encoding="utf-8")
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("P1_SHARD_STATUS_PLAN=" + json.dumps(meta, sort_keys=True))
        return 0

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    payload = json.loads(Path(args.d1_json).read_text(encoding="utf-8"))
    result = evaluate_status(meta, payload)
    Path(args.state_out).write_text(str(result["state"]) + "\n", encoding="utf-8")
    if args.result_out:
        Path(args.result_out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P1_SHARD_STATUS=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
