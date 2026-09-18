#!/usr/bin/env python3
"""Prepare immutable reviewed P1 SQL for Cloudflare D1 file execution.

The reviewed materializer intentionally emits a SQLite transaction wrapper as
analysis evidence. Cloudflare D1's remote SQL-file importer already provides
atomic import handling and rejects explicit BEGIN/COMMIT statements. This
helper validates the reviewed SQL, removes only the redundant execution-control
lines, and writes a D1-compatible derivative without changing any data
statement.

It also computes a deterministic D1 rows-written estimate from the normalized
P1 schema/index layout. The estimate is used as a safety gate for the Workers
Free daily rows-written limit; it is not a billing forecast for unrelated app
traffic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CONTROL_LINES = {
    "PRAGMA foreign_keys = ON;",
    "BEGIN;",
    "COMMIT;",
}
DATA_PREFIXES = (
    "INSERT INTO recommendation_titles ",
    "INSERT INTO genres ",
    "INSERT INTO people ",
    "INSERT OR IGNORE INTO title_genres ",
    "INSERT OR IGNORE INTO title_credits ",
)

# D1 counts the table row plus affected SQLite index rows. These multipliers
# are derived from migration 0021's normalized schema/index layout and matched
# the observed shard-0 import exactly (65,299 rows written).
D1_WRITE_MULTIPLIERS = {
    "INSERT INTO recommendation_titles": 4,
    "INSERT INTO genres": 4,
    "INSERT INTO people": 4,
    "INSERT OR IGNORE INTO title_genres": 3,
    "INSERT OR IGNORE INTO title_credits": 4,
}
FREE_DAILY_ROWS_WRITTEN = 100_000


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def estimate_rows_written(statement_counts: dict[str, int]) -> int:
    unknown = sorted(set(statement_counts) - set(D1_WRITE_MULTIPLIERS))
    if unknown:
        raise ValueError(f"unknown P1 statement types for D1 cost model: {unknown}")
    return sum(
        int(statement_counts.get(statement, 0)) * multiplier
        for statement, multiplier in D1_WRITE_MULTIPLIERS.items()
    )


def prepare_sql(sql: str, expected_fingerprint: str) -> tuple[str, dict[str, object]]:
    lines = sql.splitlines()
    noncomment = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("--")]

    fingerprint_marker = f"-- Projection manifest SHA-256: {expected_fingerprint}"
    if fingerprint_marker not in lines:
        raise ValueError("reviewed SQL is not bound to the expected projection fingerprint")

    for control in CONTROL_LINES:
        if noncomment.count(control) != 1:
            raise ValueError(f"reviewed SQL must contain exactly one {control!r}")

    if not noncomment or noncomment[0] != "PRAGMA foreign_keys = ON;":
        raise ValueError("reviewed SQL must begin with the expected foreign-key control")
    if len(noncomment) < 2 or noncomment[1] != "BEGIN;":
        raise ValueError("reviewed SQL must contain BEGIN immediately after the foreign-key control")
    if noncomment[-1] != "COMMIT;":
        raise ValueError("reviewed SQL must end with COMMIT")

    data_lines: list[str] = []
    counts = {prefix.strip(): 0 for prefix in DATA_PREFIXES}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        if stripped in CONTROL_LINES:
            continue
        matched = False
        for prefix in DATA_PREFIXES:
            if stripped.startswith(prefix):
                counts[prefix.strip()] += 1
                matched = True
                break
        if not matched:
            raise ValueError(f"unsafe or unexpected SQL statement: {stripped[:160]}")
        data_lines.append(line)

    if not data_lines:
        raise ValueError("reviewed SQL contains no data statements")

    # Preserve comments and every data statement byte-for-byte; remove only the
    # three execution-control lines that D1 either enforces automatically or
    # rejects in remote SQL-file imports.
    executable_lines = [line for line in lines if line.strip() not in CONTROL_LINES]
    executable = "\n".join(executable_lines).rstrip() + "\n"

    upper = executable.upper()
    if "\nBEGIN;" in "\n" + upper or "\nCOMMIT;" in "\n" + upper or "SAVEPOINT" in upper:
        raise ValueError("transaction control leaked into D1 executable SQL")

    expected_executable_noncomment = [
        line.strip() for line in executable.splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ]
    original_data_noncomment = [line.strip() for line in data_lines]
    if expected_executable_noncomment != original_data_noncomment:
        raise ValueError("D1 transformation changed reviewed data statements")

    estimated_rows = estimate_rows_written(counts)
    manifest: dict[str, object] = {
        "schema_version": "p1-d1-reviewed-import-v2",
        "expected_projection_sha256": expected_fingerprint,
        "original_sha256": sha256_text(sql),
        "executable_sha256": sha256_text(executable),
        "original_line_count": len(lines),
        "executable_line_count": len(executable.splitlines()),
        "data_statement_count": len(data_lines),
        "removed_controls": ["PRAGMA foreign_keys = ON;", "BEGIN;", "COMMIT;"],
        "statement_counts": counts,
        "write_cost_model": D1_WRITE_MULTIPLIERS,
        "estimated_rows_written": estimated_rows,
        "free_daily_rows_written_limit": FREE_DAILY_ROWS_WRITTEN,
        "free_daily_rows_written_headroom": FREE_DAILY_ROWS_WRITTEN - estimated_rows,
    }
    return executable, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-fingerprint", required=True)
    args = parser.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    manifest_path = Path(args.manifest)
    sql = source.read_text(encoding="utf-8")
    executable, manifest = prepare_sql(sql, args.expected_fingerprint)

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(executable, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P1_D1_EXECUTABLE=" + json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
