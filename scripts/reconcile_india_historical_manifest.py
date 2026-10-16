#!/usr/bin/env python3
"""Reconcile the historical offline discovery manifest against a fresh D1 snapshot.

READ ONLY. Converts a deduplicated source queue to net-new candidate and SQL
preview reports; does not execute any SQL or publish unconfirmed movie records.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_indian_movie_growth import audit, markdown_report
from prepare_india_category_import import select_batch
from production_catalogue_quality import load_d1_rows
from verify_indian_movie_candidates import sql_for_movie


def reconcile(manifest: dict, exact_movies: list[dict], year_movies: list[dict],
              max_preview: int = 100) -> tuple[dict, dict, list[str]]:
    if manifest.get("schema_version") != "indian-historical-source-merge-v1":
        raise ValueError("Expected a deduplicated historical source-only manifest")
    if manifest.get("production_snapshot_available") or manifest.get("production_import_authorized"):
        raise ValueError("Unexpected production-authorized source manifest")
    source = {"source_incomplete": True, "mode": "live_d1_reconciliation",
              "notes": "Offline 1970s/1980s/1990s Wikipedia sources; partial sampled cohorts"}
    report = audit(manifest["candidates"], exact_movies, year_movies, source)
    selected, selection = select_batch(report, max_preview)
    return report, {"summary": selection, "selected": selected}, [
        sql_for_movie(item) for item in selected
    ]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest-json", type=Path, required=True)
    p.add_argument("--exact-movies", type=Path, required=True)
    p.add_argument("--year-movies", type=Path, required=True)
    p.add_argument("--max-preview", type=int, default=100)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-md", type=Path, required=True)
    p.add_argument("--out-plan", type=Path, required=True)
    p.add_argument("--out-sql", type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads(args.manifest_json.read_text(encoding="utf-8"))
    report, plan, statements = reconcile(manifest, load_d1_rows(args.exact_movies),
                                         load_d1_rows(args.year_movies), args.max_preview)
    outputs = [
        (args.out_json, json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
        (args.out_md, markdown_report(report)),
        (args.out_plan, json.dumps(plan, indent=2, ensure_ascii=False) + "\n"),
        (args.out_sql, "-- SQL PREVIEW ONLY. NOT APPLIED.\n" + "\n".join(statements) + "\n"),
    ]
    for path, body in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print("INDIA_HISTORICAL_PRODUCTION_RECONCILIATION=" + json.dumps({
        "discovered_unique_pages": report["summary"]["discovered_unique_pages"],
        "net_new_source_leads": report["summary"]["total_net_new_discovery_candidates"],
        "likely_existing": report["summary"]["already_in_production"],
        "uncertain_year_identity": report["summary"]["needs_identity_or_year_review"],
        "category_qualified_preview_rows": len(plan["selected"]),
        "production_rows_imported": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
