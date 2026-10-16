#!/usr/bin/env python3
"""Shared 10K Indian-film growth target between daily and Wikidata importers.

Only QIDs proven PRESENT in a freshly retrieved production year-precision
snapshot count toward growth. Keep cohorts disjoint and avoid double-counting.
This is an operational addition tally, not official film-content verification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from production_catalogue_quality import load_d1_rows
from verify_indian_movie_candidates import QID

GOAL = 10_000
PREVIOUSLY_CONFIRMED = 1552
BULK_SOURCE_PREFIX = "wikidata:P31=film;P495=India;P577=release_year"


def growth_progress(year_rows: list[dict], state: dict) -> dict:
    existing = {
        str(row.get("wikidata_qid") or "").strip().upper()
        for row in year_rows
        if QID.fullmatch(str(row.get("wikidata_qid") or "").strip().upper())
    }
    cohort_2000 = set(state.get("2000s_seed_qids") or []) & existing
    cohort_auto = (set(state.get("attempted_by_autopilot") or []) & existing) - cohort_2000
    cohort_bulk = {
        str(row.get("wikidata_qid") or "").strip().upper()
        for row in year_rows
        if str(row.get("source_category") or "") == BULK_SOURCE_PREFIX
    } & existing
    cohort_bulk -= cohort_2000 | cohort_auto
    return {
        "goal": GOAL,
        "confirmed_pre_autopilot": PREVIOUSLY_CONFIRMED,
        "confirmed_2000s_cohort": len(cohort_2000),
        "confirmed_daily_autopilot": len(cohort_auto),
        "confirmed_wikidata_bulk_imports": len(cohort_bulk),
        "confirmed_total": PREVIOUSLY_CONFIRMED
            + len(cohort_2000) + len(cohort_auto) + len(cohort_bulk),
        "remaining": max(0, GOAL - PREVIOUSLY_CONFIRMED
            - len(cohort_2000) - len(cohort_auto) - len(cohort_bulk)),
    }


def max_additional_bulk_rows(year_rows: list[dict], state: dict, max_requested: int) -> dict:
    if not 1 <= max_requested <= 10_000:
        raise ValueError("Requested import count outside accepted bounds")
    progress = growth_progress(year_rows, state)
    progress["bulk_allowed_now"] = min(max_requested, progress["remaining"])
    return progress


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year-movies", type=Path, required=True)
    p.add_argument("--autopilot-state", type=Path, required=True)
    p.add_argument("--max-requested", type=int, required=True)
    p.add_argument("--out-env", type=Path, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    args = p.parse_args()
    year = load_d1_rows(args.year_movies)
    state = json.loads(args.autopilot_state.read_text(encoding="utf-8"))
    if state.get("schema_version") != 1:
        raise ValueError("Invalid or missing daily autopilot state; refuse uncapped import")
    result = max_additional_bulk_rows(year, state, args.max_requested)
    args.out_env.parent.mkdir(parents=True, exist_ok=True)
    with args.out_env.open("a", encoding="utf-8") as fh:
        fh.write(f"BULK_ALLOWED_NOW={result['bulk_allowed_now']}\n")
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("INDIA_SHARED_IMPORT_TARGET=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
