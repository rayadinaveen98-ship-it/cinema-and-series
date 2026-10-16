#!/usr/bin/env python3
"""Daily India movie catalogue autopilot.

Conservative zero-upgrade workflow: resume Wikipedia discovery, reconcile a
fresh D1 snapshot, import source-backed year-only movies with indexed duplicate
guards and verify QIDs after each write. State is persisted on a dedicated
GitHub branch by the workflow. An interrupted run is safe to retry because the
database is the canonical checkpoint and every SQL statement is idempotent.

The QID + "YYYY Indian films" membership is *discovery* evidence, not official
film/country certification. All imports remain explicitly unconfirmed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_indian_movie_growth import audit, discover
from prepare_india_category_import import select_batch
from production_catalogue_quality import load_d1_rows
from verify_indian_movie_candidates import sql_for_movie, QID

# Prioritize high-quality year-level Indian-film categories (one seed/year).
# Existing broader language-category audits remain available for backfill.
# Resume offsets are in INDIA-ONLY year-category units, not old 13-per-year units.
# Previously archived scans already captured the newest one/two years in
# later decades; still re-check conservatively when a rate-limit interrupted.
# Historical decades first; then resume partially scanned decades.
DECADES = [
    (1960, 1969, 0),
    (1950, 1959, 0),
    (1940, 1949, 0),
    (1930, 1939, 0),
    (1913, 1929, 0),
    (1970, 1979, 1),
    (1980, 1989, 2),
    (1990, 1999, 1),
    (2000, 2009, 2),
    (2010, 2019, 2),
    (2020, 2026, 2),
]
MAX_DISCOVERY_CATEGORIES = 16
MAX_NEW_PER_DAY = 1500
SQL_BATCH_SIZE = 75
MAX_IMPORT_ROWS_READ = 1_200_000  # Reserve at least 3.8M of D1's 5M free reads for app activity.
TARGET_ADDITIONAL_MOVIES = 10_000
CONFIRMED_PRE_AUTOPILOT = 1552  # Previously audited +734 and +818.


class D1QuotaReached(Exception):
    pass


class D1Error(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initial_state() -> dict:
    return {
        "schema_version": 1,
        "goal_additional_indian_films": TARGET_ADDITIONAL_MOVIES,
        "previously_confirmed": CONFIRMED_PRE_AUTOPILOT,
        "2000s_import_present": 0,
        "2000s_seed_qids": [],
        "autopilot_added_confirmed": 0,
        "attempted_by_autopilot": [],
        "queue": {},
        "scan": {"decade_index": 0, "offset": 0, "finished": False, "mode": "india_only"},
        "last_run": {},
        "history": [],
    }


def merge_source(queue: dict, row: dict) -> None:
    qid = str(row.get("wikidata_qid") or "").strip().upper()
    if not QID.fullmatch(qid):
        return
    page = int(row.get("page_id") or 0)
    title = str(row.get("title") or "").strip()
    if page <= 0 or not title or title.upper() == qid:
        return
    years = row.get("observed_years") or ([row["year"]] if isinstance(row.get("year"), int) else [])
    years = {int(year) for year in years if isinstance(year, int) and 1913 <= year <= 2026}
    categories = {str(x) for x in row.get("source_categories") or []}
    languages = {str(x) for x in row.get("observed_languages") or []}
    if not years:
        return
    if qid not in queue:
        queue[qid] = {
            "wikidata_qid": qid, "page_id": page, "title": title,
            "observed_years": [], "source_categories": [], "observed_languages": [],
            "india_category": False,
        }
    saved = queue[qid]
    saved["observed_years"] = sorted(set(saved["observed_years"]) | years)
    saved["source_categories"] = sorted(set(saved["source_categories"]) | categories)
    saved["observed_languages"] = sorted(set(saved["observed_languages"]) | languages)
    saved["india_category"] = bool(saved["india_category"] or row.get("india_category"))


def eligible_queue_items(queue: dict) -> list[dict]:
    result = []
    for row in queue.values():
        years = row.get("observed_years") or []
        if len(years) != 1:
            continue
        year = years[0]
        if f"Category:{year} Indian films" not in row.get("source_categories", []):
            continue
        result.append({
            **row, "year": year,
            "source_categories": [
                f"Category:{year} Indian films",
                *[x for x in row["source_categories"] if x != f"Category:{year} Indian films"],
            ],
            "language": (row.get("observed_languages") or ["Unknown"])[0],
        })
    return result


def bootstrap(state: dict, archive_year: Path | None, archive_history: Path | None) -> None:
    if state.get("queue"):
        return
    if not archive_year or not archive_history or not archive_year.is_file() or not archive_history.is_file():
        raise ValueError("First run requires both archived 2000s and 1970s–1990s source reports")
    for archive in (archive_year, archive_history):
        report = json.loads(archive.read_text(encoding="utf-8"))
        if report.get("schema_version") not in {
            "india-movie-discovery-audit-v1", "indian-historical-source-merge-v1"
        }:
            raise ValueError("Unsupported source archive; refusing to bootstrap")
        for row in report.get("candidates", []):
            merge_source(state["queue"], row)
            if archive == archive_year:
                qid = str(row.get("wikidata_qid") or "").upper()
                year = row.get("year")
                if (row.get("classification") == "new_indian_category_candidates"
                        and QID.fullmatch(qid) and isinstance(year, int)
                        and 2000 <= year <= 2009
                        and f"Category:{year} Indian films" in row.get("source_categories", [])):
                    state["2000s_seed_qids"].append(qid)
    state["2000s_seed_qids"] = sorted(set(state["2000s_seed_qids"]))


def source_step(state: dict) -> dict:
    progress = state["scan"]
    if progress.get("mode") != "india_only":
        # Migrate safely from the previous 13-category/year cursor. Rounding
        # down deliberately revisits the partially scanned year's India
        # category, rather than ever skipping an unvisited historical year.
        progress["offset"] = max(0, int(progress.get("offset", 0)) // 13)
        progress["mode"] = "india_only"
    if progress.get("finished"):
        return {"status": "completed", "added_source_qids": 0}
    index = int(progress["decade_index"])
    if index >= len(DECADES):
        progress["finished"] = True
        return {"status": "completed", "added_source_qids": 0}
    start, end, first_offset = DECADES[index]
    offset = max(int(progress["offset"]), first_offset)
    prior = len(state["queue"])
    records, source = discover(start, end, max_candidates=8000,
                               max_categories=MAX_DISCOVERY_CATEGORIES,
                               category_offset=offset, india_only=True)
    for row in records:
        merge_source(state["queue"], row)
    next_offset = int(source.get("next_category_offset", offset))
    total_seeds = end - start + 1
    if next_offset >= total_seeds and source.get("halt_reason") != "wikipedia_rate_limit":
        progress["decade_index"] = index + 1
        progress["offset"] = 0
    else:
        progress["offset"] = next_offset
    if progress["decade_index"] >= len(DECADES):
        progress["finished"] = True
    return {
        "status": source.get("halt_reason") or "category_batch_complete",
        "decade": f"{start}-{end}",
        "next_offset": next_offset,
        "new_source_qids": len(state["queue"]) - prior,
        "failed_categories": source.get("categories_failed", 0),
        "wikipedia_rate_limited": source.get("halt_reason") == "wikipedia_rate_limit",
    }


def d1_execute(*, sql: str | None = None, sql_file: Path | None = None) -> tuple[str, int]:
    args = ["npx", "wrangler", "d1", "execute", "cinema-and-series", "--remote"]
    if sql is not None:
        args.extend(["--json", "--command", sql])
    elif sql_file is not None:
        args.append(f"--file={sql_file}")
    else:
        raise ValueError("missing D1 command")
    result = subprocess.run(args, text=True, capture_output=True, timeout=110)
    output = result.stdout + "\n" + result.stderr
    if result.returncode:
        if "7500" in output and ("row read" in output.lower() or "free tier" in output.lower()):
            raise D1QuotaReached("D1 free-tier daily row-read limit reached")
        raise D1Error("D1 query failed: " + output[-850:])
    match = re.search(r"Rows read[^0-9]{0,30}([0-9]+)", output)
    return result.stdout, int(match.group(1)) if match else 0


def query_rows(sql: str) -> list[dict]:
    raw, _ = d1_execute(sql=sql)
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list) or not parsed or not parsed[0].get("success", True):
            raise ValueError("D1 query returned no successful results")
        return parsed[0]["results"]
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        raise D1Error(f"Unable to parse D1 query response: {str(exc)}") from exc


def qids_present_in_year_table(qids: list[str]) -> set[str]:
    found = set()
    for first in range(0, len(qids), 75):
        members = qids[first:first+75]
        if not members:
            continue
        terms = ",".join(f"'{qid}'" for qid in members if QID.fullmatch(qid))
        for row in query_rows(f"SELECT wikidata_qid FROM catalogue_titles WHERE wikidata_qid IN ({terms});"):
            qid = str(row.get("wikidata_qid") or "").upper()
            if QID.fullmatch(qid):
                found.add(qid)
    return found


def safe_queue_selection(state: dict, exact: list[dict], year: list[dict],
                         series: list[dict], max_rows: int) -> list[dict]:
    report = audit(eligible_queue_items(state["queue"]), exact, year)
    selected, _ = select_batch(report, max_rows)
    known_series = {str(row.get("wikidata_qid") or "").upper() for row in series}
    selected = [row for row in selected if row["wikidata_qid"] not in known_series]
    # Refuse conflicting identities and repeated normalized title/year among this batch.
    seen = set()
    safe = []
    for item in selected:
        key = (str(item["title"]).strip().casefold(), item["year"])
        if key not in seen:
            seen.add(key)
            safe.append(item)
    return safe


def process_d1(state: dict, output_dir: Path, max_daily: int, max_reads: int) -> dict:
    exact = query_rows("SELECT id,wikidata_qid,title,release_date FROM movies;")
    year = query_rows(
        "SELECT id,wikidata_qid,wikipedia_page_id,title,release_year FROM catalogue_titles;"
    )
    series = query_rows("SELECT wikidata_qid FROM series_titles WHERE wikidata_qid IS NOT NULL;")
    year_qids = {str(row.get("wikidata_qid") or "").upper() for row in year}
    # Explicitly verify the 689-title 2000s import from the prior incomplete run.
    year_2000 = set(state.get("2000s_seed_qids") or [])
    state["2000s_import_present"] = len(year_2000 & year_qids)
    # Crash recovery: submitted rows not verified in a previous run count only
    # when the database actually contains their QIDs.
    attempted = set(state["attempted_by_autopilot"])
    state["autopilot_added_confirmed"] = len(attempted & year_qids)
    confirmed = (state["previously_confirmed"] + state["2000s_import_present"]
                 + state["autopilot_added_confirmed"])
    if confirmed >= state["goal_additional_indian_films"]:
        return {"status": "goal_reached", "goal": state["goal_additional_indian_films"],
                "confirmed_count": confirmed, "added_today": 0}
    max_daily = min(max_daily, state["goal_additional_indian_films"] - confirmed)
    selected = safe_queue_selection(state, exact, year, series, max_daily)
    added = 0
    read_usage = 0
    attempted_today = 0
    for index in range(0, len(selected), SQL_BATCH_SIZE):
        if read_usage >= max_reads:
            break
        batch = selected[index:index+SQL_BATCH_SIZE]
        filename = output_dir / f"import-{index//SQL_BATCH_SIZE:02d}.sql"
        filename.write_text("-- Idempotent insert-only India film year catalogue batch.\n"
                            + "\n".join(sql_for_movie(row) for row in batch) + "\n",
                            encoding="utf-8")
        _, read_cost = d1_execute(sql_file=filename)
        read_usage += read_cost
        attempted_today += len(batch)
        for row in batch:
            qid = row["wikidata_qid"]
            if qid not in state["attempted_by_autopilot"]:
                state["attempted_by_autopilot"].append(qid)
        # Verify each submitted QID immediately; never rely on SQL "success" alone.
        now_present = qids_present_in_year_table([row["wikidata_qid"] for row in batch])
        added += len(now_present - year_qids)
        year_qids |= now_present
        state["autopilot_added_confirmed"] = len(set(state["attempted_by_autopilot"]) & year_qids)
    return {
        "status": "batch_complete" if attempted_today else "no_eligible_new_candidates",
        "known_exact_movies": len(exact),
        "known_year_movies": len(year),
        "2000s_import_present": state["2000s_import_present"],
        "new_movies_added_today": added,
        "rows_submitted_today": attempted_today,
        "db_rows_read_reported_by_import": read_usage,
        "target": state["goal_additional_indian_films"],
        "confirmed_target_progress": state["previously_confirmed"]
            + state["2000s_import_present"] + state["autopilot_added_confirmed"],
    }


def run(state: dict, output_dir: Path, max_daily: int, max_reads: int,
        no_db: bool = False, discover_enabled: bool = True) -> dict:
    result = {"timestamp_utc": utc_now(), "source_queue_qids": len(state["queue"])}
    if discover_enabled and state.get("scan", {}).get("finished") is not True:
        try:
            result["source_discovery"] = source_step(state)
        except Exception as exc:
            result["source_discovery"] = {"status": "deferred_source_failure",
                                          "error": str(exc)[:250]}
    result["source_queue_qids"] = len(state["queue"])
    result["category_qualified_queue"] = len(eligible_queue_items(state["queue"]))
    if no_db:
        result["production"] = {"status": "source_only"}
        return result
    try:
        result["production"] = process_d1(state, output_dir, max_daily, max_reads)
    except D1QuotaReached:
        result["production"] = {"status": "quota_paused_until_next_utc_day"}
    except (D1Error, subprocess.TimeoutExpired) as exc:
        result["production"] = {"status": "error_requires_attention",
                                "message": str(exc)[:450]}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive-2000", type=Path)
    parser.add_argument("--archive-history", type=Path)
    parser.add_argument("--max-new", type=int, default=MAX_NEW_PER_DAY)
    parser.add_argument("--max-reads", type=int, default=MAX_IMPORT_ROWS_READ)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    if not (1 <= args.max_new <= 2000 and 10000 <= args.max_reads <= 1_500_000):
        parser.error("max-new must be 1..2000 and import read budget 10k..1.5M")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    saved = json.loads(args.state.read_text(encoding="utf-8")) if args.state.is_file() else {}
    state = saved if saved.get("schema_version") == 1 else initial_state()
    bootstrap(state, args.archive_2000, args.archive_history)
    result = run(state, args.output_dir, args.max_new, args.max_reads, no_db=args.source_only)
    state["last_run"] = result
    state["history"] = (state.get("history", []) + [{
        "timestamp": result["timestamp_utc"],
        "production_status": result["production"]["status"],
        "discovery_status": result.get("source_discovery", {}).get("status"),
        "new_movies_added_today": result["production"].get("new_movies_added_today", 0),
    }])[-60:]
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    args.out_report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print("INDIA_DAILY_AUTOPILOT=" + json.dumps(result, sort_keys=True))
    return 1 if result["production"]["status"] == "error_requires_attention" else 0


if __name__ == "__main__":
    raise SystemExit(main())
