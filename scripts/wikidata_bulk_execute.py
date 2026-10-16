#!/usr/bin/env python3
"""Apply previously reconciled, index-guarded Wikidata Indian-film SQL batches.

Designed for GitHub Actions on the existing Cloudflare D1 database. In dry-run
mode it performs ZERO D1 operations. In apply mode the run explicitly opts into
remote production writes, verifies submitted QIDs, and stops on quota 7500.
Replaying this step is safe because every preview SQL is insert-only and the
next preview is rebuilt from fresh D1 snapshots.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from india_daily_autopilot import D1QuotaReached, D1Error, d1_execute, qids_present_in_year_table
from verify_indian_movie_candidates import QID


def apply_batch_files(selected: list[dict], sql_dir: Path,
                      max_row_reads: int = 1_200_000, apply: bool = False) -> dict:
    qids = [str(row["qid"]).upper() for row in selected]
    if any(not QID.fullmatch(qid) for qid in qids) or len(qids) != len(set(qids)):
        raise ValueError("Unsafe Wikidata import QIDs")
    if not 0 <= len(qids) <= 10_000:
        raise ValueError("Source batch exceeds 10,000 records")
    if not 10_000 <= max_row_reads <= 2_000_000:
        raise ValueError("Invalid daily bulk import row-read budget")
    files = sorted(sql_dir.glob("wikidata-*.sql"))
    if not files and qids:
        raise ValueError("SQL preview was not generated")
    if not apply:
        return {"status": "dry_run_no_d1", "preview_qids": len(qids),
                "verified_added_qids": 0, "rows_read_reported": 0, "executed_sql_files": 0}
    attempted, present, usage = 0, set(), 0
    status = "completed"
    for filename in files:
        if usage >= max_row_reads:
            status = "read_budget_paused"
            break
        offset = int(filename.stem.split("-")[-1])
        chunk = qids[offset:offset + 200]
        if not chunk:
            raise ValueError(f"Unexpected SQL preview with no QIDs: {filename.name}")
        contents = filename.read_text(encoding="utf-8")
        if contents.count("INSERT OR IGNORE INTO catalogue_titles") != len(chunk):
            raise ValueError(f"SQL file mismatched submitted identities: {filename.name}")
        if "DELETE FROM" in contents.upper() or "UPDATE CATALOGUE_TITLES" in contents.upper():
            raise ValueError("Bulk production SQL must be insert-only")
        try:
            _, batch_reads = d1_execute(sql_file=filename)
            usage += batch_reads
            attempted += len(chunk)
            now = qids_present_in_year_table(chunk)
            present.update(now)
        except D1QuotaReached:
            status = "cloudflare_quota_paused"
            break
        except D1Error:
            raise
    return {
        "status": status, "preview_qids": len(qids),
        "submitted_to_d1": attempted,
        "verified_present_qids": len(present),
        "rows_read_reported": usage,
        "executed_sql_files": min(len(files), (attempted + 199) // 200),
        "note": "Presence is checked after every batch. Prior existing IDs remain idempotent.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected", type=Path, required=True)
    p.add_argument("--sql-dir", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--max-row-reads", type=int, default=1_200_000)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    candidates = json.loads(args.selected.read_text(encoding="utf-8"))
    result = apply_batch_files(candidates, args.sql_dir, args.max_row_reads, apply=args.apply)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("WIKIDATA_BULK_IMPORT_RESULT=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
