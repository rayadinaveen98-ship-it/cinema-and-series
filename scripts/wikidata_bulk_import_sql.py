#!/usr/bin/env python3
"""Create audited, idempotent D1 SQL previews from an offline Wikidata stage.

Requires fresh Cloudflare production SELECT snapshots; never connects to D1
or executes SQL. Direct Wikidata P31/P495/P577 claims establish sourced
identity/year, but *not* an official release confirmation. Imported rows must
remain 'unconfirmed' and release day deliberately absent.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from production_catalogue_quality import load_d1_rows, norm, year_from_date
from verify_indian_movie_candidates import sql_quote, QID


def sql_for_staged_movie(item: dict) -> str:
    qid = str(item["qid"]).upper()
    title = str(item["title"]).strip()
    year = int(item["year"])
    if not QID.fullmatch(qid) or not title or title.upper() == qid or not 1913 <= year <= 2026:
        raise ValueError("Unsafe staged film identity")
    quoted_title = sql_quote(title)
    quoted_qid = sql_quote(qid)
    return (
        "INSERT OR IGNORE INTO catalogue_titles "
        "(id,wikidata_qid,wikipedia_page_id,title,release_year,date_precision,"
        "language_name,country_code,source_category,source_url,verification_status,updated_at) "
        "SELECT "
        f"{sql_quote('wd-' + qid)},{quoted_qid},NULL,{quoted_title},{year},"
        "'year','Unknown','IN','wikidata:P31=film;P495=India;P577=release_year',"
        f"{sql_quote('https://www.wikidata.org/wiki/' + qid)},'unconfirmed',CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS (SELECT 1 FROM movies m "
        f"WHERE m.wikidata_qid={quoted_qid}) "
        "AND NOT EXISTS (SELECT 1 FROM movies m "
        f"WHERE m.title={quoted_title} COLLATE NOCASE "
        f"AND m.release_date BETWEEN '{year}-01-01' AND '{year}-12-31') "
        "AND NOT EXISTS (SELECT 1 FROM series_titles s "
        f"WHERE s.wikidata_qid={quoted_qid}) "
        "AND NOT EXISTS (SELECT 1 FROM catalogue_titles c "
        f"WHERE c.wikidata_qid={quoted_qid}) "
        "AND NOT EXISTS (SELECT 1 FROM catalogue_titles c "
        f"WHERE c.release_year={year} AND c.title={quoted_title} COLLATE NOCASE);"
    )


def load_stage(db_path: Path) -> list[dict]:
    with sqlite3.connect(str(db_path)) as db:
        return [
            {"qid": qid, "title": title, "year": year, "day": release_day}
            for qid, title, year, release_day in db.execute(
                "SELECT qid,title,year,source_release_day FROM films "
                "WHERE year_conflict=0 AND title_conflict=0 "
                "ORDER BY year DESC,title COLLATE NOCASE,qid")
        ]


def reconcile(stage_rows: list[dict], exact_movies: list[dict],
              year_movies: list[dict], series_rows: list[dict],
              max_preview: int = 1000) -> tuple[list[dict], dict]:
    if not 1 <= max_preview <= 10000:
        raise ValueError("Preview limit out of bounds")
    known_qids = set()
    known_title_year = set()
    known_page_ids = set()
    for row in exact_movies + year_movies + series_rows:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if QID.fullmatch(qid):
            known_qids.add(qid)
        pid = row.get("wikipedia_page_id")
        if pid:
            known_page_ids.add(str(pid))
        title = norm(row.get("title"))
        year = year_from_date(row.get("release_date"))
        if year is None:
            year = row.get("release_year")
        if year is None:
            year = row.get("first_air_year")
        if title and isinstance(year, int):
            known_title_year.add((title, year))

    source_counts = Counter()
    seen_qids, seen_titles = set(), set()
    candidates = []
    for item in stage_rows:
        qid = str(item.get("qid") or "").upper()
        title = str(item.get("title") or "").strip()
        year = item.get("year")
        if not QID.fullmatch(qid) or not isinstance(year, int) or not 1913 <= year <= 2026 or not title or title.upper() == qid:
            source_counts["invalid_source_identity"] += 1
            continue
        key = (norm(title), year)
        if qid in seen_qids or key in seen_titles:
            source_counts["staging_identity_collision"] += 1
            continue
        seen_qids.add(qid)
        seen_titles.add(key)
        if qid in known_qids:
            source_counts["already_exists_qid"] += 1
        elif key in known_title_year:
            source_counts["possible_title_year_match"] += 1
        else:
            source_counts["eligible_with_production_snapshot"] += 1
            candidates.append(item)
    selected = candidates[:max_preview]
    summary = {
        "staged_unconflicted": len(stage_rows),
        "existing_qid": source_counts["already_exists_qid"],
        "held_title_year_collision": source_counts["possible_title_year_match"],
        "held_staging_collision": source_counts["staging_identity_collision"],
        "held_invalid_identity": source_counts["invalid_source_identity"],
        "reconciled_net_new_candidates": len(candidates),
        "sql_preview_rows": len(selected),
        "not_imported": True,
        "officially_verified": False,
    }
    return selected, summary


def write_preview(sql_dir: Path, selected: list[dict], chunk_size: int = 200) -> list[str]:
    if not 1 <= chunk_size <= 500:
        raise ValueError("Unsafe chunk size")
    sql_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for offset in range(0, len(selected), chunk_size):
        path = sql_dir / f"wikidata-{offset:05d}.sql"
        payload = selected[offset:offset+chunk_size]
        path.write_text(
            "-- PREVIEW ONLY. Requires explicit review and D1 write authorization.\n"
            "-- All movie records are year-precision and unconfirmed.\n"
            + "\n".join(sql_for_staged_movie(item) for item in payload) + "\n",
            encoding="utf-8",
        )
        generated.append(path.name)
    return generated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--exact-movies", type=Path, required=True)
    parser.add_argument("--year-movies", type=Path, required=True)
    parser.add_argument("--series", type=Path, required=True)
    parser.add_argument("--max-preview", type=int, default=1000)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    stage = load_stage(args.stage)
    selected, summary = reconcile(stage, load_d1_rows(args.exact_movies),
                                   load_d1_rows(args.year_movies),
                                   load_d1_rows(args.series), args.max_preview)
    generated = write_preview(args.out_dir, selected)
    report = {**summary, "sql_files": generated,
              "note": "No SQL has been applied. Live D1 identity checks must be fresh."}
    (args.out_dir/"reconciliation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.out_dir/"selected.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WIKIDATA_SQL_PREVIEW=" + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
