#!/usr/bin/env python3
"""Stage Wikidata-supported Indian film identities locally in SQLite, without D1.

Source: Wikidata Query Service, CC0 structured P31=film (Q11424),
P495=India (Q668), P577=release date. Collect small quarter shards with
bounded requests and checkpoints. A Wikidata statement is not equivalent
to official release verification. No SQL writes to Cloudflare are performed.

Example:
 python scripts/wikidata_bulk_stage.py --start-year 2000 --end-year 2009 \
   --max-quarters 8 --db data/generated/wikidata-stage.sqlite \
   --out-json data/generated/wikidata-stage-report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WDQS = "https://query.wikidata.org/sparql"
USER_AGENT = "CinemaAndSeriesFilmCatalogue/0.2 (https://github.com/rayadinaveen98-ship-it/cinema-and-series; respectful CC0 source extraction)"
QID = re.compile(r"^Q[1-9][0-9]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T")
LIMIT = 3000
COOLDOWN_SECONDS = 2.0


def quarter_dates(year: int, quarter: int) -> tuple[str, str]:
    if not 1913 <= year <= 2026 or quarter not in (1, 2, 3, 4):
        raise ValueError("Invalid year or quarter")
    month = 1 + 3 * (quarter - 1)
    after_year = year + (1 if quarter == 4 else 0)
    after_month = 1 if quarter == 4 else month + 3
    return (f"{year:04d}-{month:02d}-01T00:00:00Z",
            f"{after_year:04d}-{after_month:02d}-01T00:00:00Z")


def sparql_for_quarter(year: int, quarter: int, limit: int = LIMIT) -> str:
    first, end = quarter_dates(year, quarter)
    if limit < 1 or limit > LIMIT:
        raise ValueError("Unsafe result limit")
    return f"""PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>
SELECT DISTINCT ?film ?filmLabel ?release WHERE {{
  ?film wdt:P31 wd:Q11424 .
  ?film wdt:P495 wd:Q668 .
  ?film wdt:P577 ?release .
  FILTER(?release >= "{first}"^^xsd:dateTime &&
         ?release < "{end}"^^xsd:dateTime)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,hi,te,ta,ml,kn,bn,mr,pa,gu,or,as". }}
}} LIMIT {limit}
"""


def fetch_wdqs(query: str, timeout: int = 58) -> dict:
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    request = urllib.request.Request(
        WDQS + "?" + params,
        headers={"Accept": "application/sparql-results+json",
                 "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read(8_000_000).decode("utf-8"))


def parse_rows(payload: dict, year: int, quarter: int) -> tuple[list[dict], int]:
    first, end = quarter_dates(year, quarter)
    bindings = payload.get("results", {}).get("bindings")
    if not isinstance(bindings, list):
        raise ValueError("Unexpected Wikidata SPARQL result shape")
    accepted, discarded = [], 0
    for row in bindings:
        film = str(row.get("film", {}).get("value") or "")
        qid = film.rsplit("/", 1)[-1].upper()
        title = str(row.get("filmLabel", {}).get("value") or "").strip()
        released = str(row.get("release", {}).get("value") or "")
        # Refuse unresolved labels and dates outside the exact source shard.
        if (not film.startswith("http://www.wikidata.org/entity/Q")
                and not film.startswith("https://www.wikidata.org/entity/Q")):
            discarded += 1
            continue
        if (not QID.fullmatch(qid) or not title or title.upper() == qid
                or not DATE.match(released) or not first[:10] <= released[:10] < end[:10]):
            discarded += 1
            continue
        accepted.append({"qid": qid, "title": title, "release_year": year,
                         "release_day_observed": released[:10],
                         "origin": "Wikidata P31=Q11424 P495=Q668 P577"})
    return accepted, discarded


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path))
    db.executescript("""
      PRAGMA journal_mode=WAL;
      CREATE TABLE IF NOT EXISTS films (
        qid TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        year INTEGER NOT NULL,
        source_release_day TEXT NOT NULL,
        year_conflict INTEGER NOT NULL DEFAULT 0,
        title_conflict INTEGER NOT NULL DEFAULT 0,
        source TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_staged_films_year ON films(year);
      CREATE TABLE IF NOT EXISTS shards (
        year INTEGER NOT NULL,
        quarter INTEGER NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN ('complete','incomplete')),
        fetched_rows INTEGER NOT NULL,
        accepted_rows INTEGER NOT NULL,
        completed_at TEXT NOT NULL,
        PRIMARY KEY (year, quarter)
      );
    """)
    return db


def stage_quarter(db: sqlite3.Connection, payload: dict, year: int, quarter: int,
                  result_limit: int = LIMIT) -> dict:
    bindings = payload.get("results", {}).get("bindings", [])
    records, discarded = parse_rows(payload, year, quarter)
    incomplete = len(bindings) >= result_limit
    # A truncated result set MUST NOT be counted as completed.
    with db:
        for item in records:
            db.execute(
                """INSERT INTO films (qid,title,year,source_release_day,source)
                   VALUES (?,?,?,?,?) ON CONFLICT(qid) DO UPDATE SET
                     year_conflict = MAX(films.year_conflict, films.year <> excluded.year),
                     title_conflict = MAX(films.title_conflict,
                        films.title <> excluded.title COLLATE NOCASE)""",
                (item["qid"], item["title"], item["release_year"],
                 item["release_day_observed"], item["origin"]),
            )
        db.execute(
            """INSERT INTO shards(year,quarter,outcome,fetched_rows,accepted_rows,completed_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(year,quarter) DO UPDATE SET
                 outcome=excluded.outcome, fetched_rows=excluded.fetched_rows,
                 accepted_rows=excluded.accepted_rows, completed_at=excluded.completed_at""",
            (year, quarter, "incomplete" if incomplete else "complete",
             len(bindings), len(records), datetime.now(timezone.utc).isoformat()),
        )
    return {"year": year, "quarter": quarter, "returned": len(bindings),
            "accepted": len(records), "rejected": discarded, "truncated": incomplete}


def report_for(db: sqlite3.Connection, start_year: int, end_year: int,
               new_shards: list[dict], stopped_reason: str | None) -> dict:
    def count(sql: str) -> int:
        return int(db.execute(sql).fetchone()[0])
    shards_total = 4 * (end_year - start_year + 1)
    incomplete = db.execute(
        "SELECT year,quarter FROM shards WHERE outcome!='complete' ORDER BY year,quarter"
    ).fetchall()
    sampled = db.execute(
        "SELECT qid,title,year FROM films WHERE year_conflict=0 AND title_conflict=0 ORDER BY year DESC,title LIMIT 12"
    ).fetchall()
    return {
        "schema_version": "wikidata-indian-films-staging-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Wikidata Query Service (CC0 structured statements)",
        "evidence": ["P31=Q11424", "P495=Q668", "P577 release year"],
        "years": [start_year, end_year],
        "intended_shards": shards_total,
        "completed_shards": count("SELECT COUNT(*) FROM shards WHERE outcome='complete'"),
        "incomplete_shards": [list(x) for x in incomplete],
        "new_shard_results": new_shards,
        "distinct_source_qids": count("SELECT COUNT(*) FROM films"),
        "source_qualified_unconflicted": count(
            "SELECT COUNT(*) FROM films WHERE year_conflict=0 AND title_conflict=0"),
        "conflicting_source_ids": count(
            "SELECT COUNT(*) FROM films WHERE year_conflict=1 OR title_conflict=1"),
        "stopped_reason": stopped_reason,
        "all_shards_completed": count("SELECT COUNT(*) FROM shards WHERE outcome='complete'") == shards_total,
        "production_snapshot_checked": False,
        "net_new_against_production": None,
        "production_rows_imported": 0,
        "sample": [{"qid": q, "title": t, "year": y} for q, t, y in sampled],
    }


def run_stage(db: sqlite3.Connection, start_year: int, end_year: int, max_quarters: int,
              fetcher=fetch_wdqs, cooldown: float = COOLDOWN_SECONDS) -> dict:
    if not 1913 <= start_year <= end_year <= 2026:
        raise ValueError("Invalid year range")
    if not 1 <= max_quarters <= 160:
        raise ValueError("max quarters must be 1..160")
    new_shards, stopped_reason = [], None
    for year in range(start_year, end_year + 1):
        for quarter in (1, 2, 3, 4):
            status = db.execute(
                "SELECT outcome FROM shards WHERE year=? AND quarter=?",
                (year, quarter),
            ).fetchone()
            if status and status[0] == "complete":
                continue
            if len(new_shards) >= max_quarters:
                stopped_reason = "bounded_run_limit"
                break
            try:
                payload = fetcher(sparql_for_quarter(year, quarter))
                outcome = stage_quarter(db, payload, year, quarter)
                new_shards.append(outcome)
                if outcome["truncated"]:
                    stopped_reason = "shard_truncated_needs_smaller_slice"
                    break
                if cooldown:
                    time.sleep(cooldown)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
                stopped_reason = (
                    f"wikidata_rate_limited_{exc.code}" if isinstance(exc, urllib.error.HTTPError)
                    and exc.code in (429, 503) else f"wikidata_source_error_{type(exc).__name__}"
                )
                break
        if stopped_reason:
            break
    return report_for(db, start_year, end_year, new_shards, stopped_reason)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=2009)
    parser.add_argument("--max-quarters", type=int, default=8)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    with connect(args.db) as db:
        report = run_stage(db, args.start_year, args.end_year, args.max_quarters)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print("WIKIDATA_BULK_STAGE=" + json.dumps(
        {k: report[k] for k in (
            "years", "completed_shards", "distinct_source_qids",
            "source_qualified_unconflicted", "stopped_reason",
            "all_shards_completed", "production_rows_imported"
        )}, sort_keys=True))
    # Rate-limit or 60sec query timeout yields partial artifacts, not lost work.
    return 0 if report["new_shard_results"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
