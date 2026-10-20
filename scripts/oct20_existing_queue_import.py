#!/usr/bin/env python3
"""One-time new Indian film import from the durable Wikipedia category queue.

Follows the app's existing category-eligible rules. Source membership is not
official film-country or release-day verification: inserted records remain
unconfirmed and year-precision. Full exact/year/series D1 identity snapshots
and indexed SQL guards prevent silent title/QID collisions. Stops on D1 quota.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_indian_movie_growth import audit
from india_daily_autopilot import (
    D1Error, D1QuotaReached, d1_execute, eligible_queue_items,
    qids_present_in_year_table,
)
from prepare_india_category_import import eligible, select_batch
from production_catalogue_quality import load_d1_rows, norm
from verify_indian_movie_candidates import QID, sql_for_movie

SQL_BATCH = 75
RUN_MAX = 5000
READ_BUDGET = 1_200_000


def choose(state: dict, exact: list[dict], year: list[dict],
           series: list[dict], maximum: int) -> tuple[list[dict], dict]:
    if not 1 <= maximum <= RUN_MAX:
        raise ValueError("Invalid new-title batch limit")
    if state.get("schema_version") != 1 or not isinstance(state.get("queue"), dict):
        raise ValueError("Missing audited India movie category source queue")
    source = eligible_queue_items(state["queue"])
    report = audit(source, exact, year)
    known_series = {str(row.get("wikidata_qid") or "").upper() for row in series}
    known_movie_qids = {str(row.get("wikidata_qid") or "").upper() for row in exact+year}
    known_movie_title_year = set()
    for row in exact+year:
        date = row.get("release_date")
        y = int(date[:4]) if isinstance(date, str) and date[:4].isdigit() else row.get("release_year")
        if isinstance(y, int):
            known_movie_title_year.add((norm(row.get("title")), y))
    series_title_year = {
        (norm(row.get("title")), row.get("first_air_year"))
        for row in series if isinstance(row.get("first_air_year"), int)
    }
    selected, seen_qids, seen_title_year = [], set(), set()
    offset = 0
    while len(selected) < maximum:
        page, _ = select_batch(report, min(250, maximum-len(selected)), offset=offset)
        if not page:
            break
        offset += len(page)
        for item in page:
            qid = str(item["wikidata_qid"]).upper()
            key = (norm(item["title"]), item["year"])
            if (qid in known_series or qid in known_movie_qids
                    or key in known_movie_title_year or key in series_title_year
                    or qid in seen_qids or key in seen_title_year
                    or eligible(item) != "eligible"):
                continue
            selected.append(item)
            seen_qids.add(qid)
            seen_title_year.add(key)
        if len(page) < min(250, maximum-len(selected)):
            # A short last page means no more audited candidates.
            break
    return selected[:maximum], {
        "source_queue_qids": len(state["queue"]),
        "category_qualified": len(source),
        "eligible_not_in_production": report["summary"]["new_indian_category_candidates"],
        "selected_count": len(selected[:maximum]),
        "source_basis": "Wikipedia Category:YYYY Indian films with exact QID and page ID",
        "official_film_release_claim": False,
    }


def apply(selected: list[dict], dest: Path, known_year: list[dict],
          *, execute=d1_execute, present=qids_present_in_year_table,
          row_read_budget: int = READ_BUDGET) -> dict:
    if not 10_000 <= row_read_budget <= 1_500_000:
        raise ValueError("Unsafe daily D1 read budget")
    dest.mkdir(parents=True, exist_ok=True)
    prior = {str(row.get("wikidata_qid") or "").upper() for row in known_year}
    added = set()
    attempted = 0
    reads = 0
    files = 0
    status = "completed"
    for offset in range(0, len(selected), SQL_BATCH):
        if reads >= row_read_budget:
            status = "read_budget_paused"
            break
        batch = selected[offset:offset+SQL_BATCH]
        qids = [str(x["wikidata_qid"]).upper() for x in batch]
        if len(set(qids)) != len(qids) or any(not QID.fullmatch(qid) for qid in qids):
            raise ValueError("Untrusted QID batch")
        sql = "\n".join(sql_for_movie(x) for x in batch) + "\n"
        if sql.count("INSERT OR IGNORE INTO catalogue_titles") != len(batch):
            raise ValueError("Wrong category SQL statement count")
        sql_path = dest/f"india-new-{offset//SQL_BATCH:03d}.sql"
        sql_path.write_text("-- Guarded insert-only, year-precision, unconfirmed films.\n"+sql)
        try:
            _, cost = execute(sql_file=sql_path)
            reads += cost
            files += 1
            attempted += len(batch)
            now = set(present(qids))
            added.update(now-prior)
            prior |= now
        except D1QuotaReached:
            status = "cloudflare_quota_paused"
            break
        except D1Error:
            raise
    return {
        "status": status, "selected": len(selected),
        "submitted_to_d1": attempted, "verified_net_new_qids": len(added),
        "rows_read_reported_by_sql_batches": reads,
        "executed_sql_batches": files, "max_allowed_row_reads": row_read_budget,
        "new_qids_sample": sorted(added)[:20],
        "source_only_counted": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True, type=Path)
    p.add_argument("--exact", required=True, type=Path)
    p.add_argument("--year", required=True, type=Path)
    p.add_argument("--series", required=True, type=Path)
    p.add_argument("--dir", required=True, type=Path)
    p.add_argument("--max-new", type=int, default=RUN_MAX)
    p.add_argument("--max-reads", type=int, default=READ_BUDGET)
    args = p.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8"))
    exact, year, series = (load_d1_rows(x) for x in (args.exact,args.year,args.series))
    selected, preview = choose(state, exact, year, series, args.max_new)
    args.dir.mkdir(parents=True, exist_ok=True)
    (args.dir/"selection.json").write_text(json.dumps(selected,ensure_ascii=False,indent=2)+"\n")
    (args.dir/"preview.json").write_text(json.dumps(preview,indent=2)+"\n")
    print("INDIA_NEW_CATEGORY_PREVIEW="+json.dumps(preview,sort_keys=True),flush=True)
    result = apply(selected, args.dir/"sql", year, row_read_budget=args.max_reads) if selected else {
        "status":"no_eligible_new_candidates","selected":0,"submitted_to_d1":0,
        "verified_net_new_qids":0, "rows_read_reported_by_sql_batches":0,
        "executed_sql_batches":0,"max_allowed_row_reads":args.max_reads,
        "new_qids_sample":[],"source_only_counted":False
    }
    (args.dir/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("INDIA_NEW_CATEGORY_IMPORT="+json.dumps(result,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
