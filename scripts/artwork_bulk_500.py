#!/usr/bin/env python3
"""Bulk exact-title artwork discovery. 500 EXISTING production identities maximum.

This step discovers poster candidates, not permission to use copyrighted images.
No new title records, D1 writes, auto approvals, app modifications or TMDB.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artwork_fast_70 import attach_candidates, shape
from existing_title_artwork_pilot import read_wrangle_rows, p18_by_qid, commons_by_filename
from wikipedia_film_posters_pilot import article_sitelinks, film_page_images

MAX_TITLES = 500
QUOTAS = {"movies": 275, "catalogue_titles": 150, "series_titles": 75}
LANGUAGES = ("Telugu", "Tamil", "Malayalam", "Kannada", "Hindi", "Bengali", "Marathi")
QID = re.compile(r"Q[1-9]\d*\Z")
HEADERS = ("source_table", "source_id", "wikidata_qid", "title", "year",
           "language", "media_type", "status", "poster_url", "source_page",
           "image_source", "rights_status", "approved_for_publication")


def rank(row: dict) -> tuple:
    language = str(row.get("language_name") or "")
    year = row.get("year")
    return (LANGUAGES.index(language) if language in LANGUAGES else len(LANGUAGES),
            -(year if isinstance(year, int) else 0),
            str(row.get("title") or "").casefold(),
            str(row.get("id") or ""))


def select_500(rows_by_table: dict[str, list[dict]], limit: int = MAX_TITLES) -> list[dict]:
    if not 1 <= limit <= MAX_TITLES:
        raise ValueError("Batch limit must be between 1 and 500")
    ranked = {}
    for table in QUOTAS:
        eligible = []
        for row in rows_by_table.get(table, []):
            qid = str(row.get("wikidata_qid") or "")
            title = str(row.get("title") or "").strip()
            row_id = str(row.get("id") or "").strip()
            year = row.get("year")
            if (not QID.fullmatch(qid) or not row_id or not title or title == qid
                    or not isinstance(year, int) or not 1888 <= year <= 2035
                    or str(row.get("language_name") or "") not in LANGUAGES
                    or row.get("has_poster") in (1, True)):
                continue
            eligible.append(row)
        ranked[table] = sorted(eligible, key=rank)
    chosen, seen_qids = [], set()

    def add(table: str, maximum: int) -> None:
        taken = 0
        for row in ranked[table]:
            if taken >= maximum or len(chosen) >= limit:
                return
            qid = row["wikidata_qid"]
            if qid in seen_qids:
                continue
            seen_qids.add(qid)
            chosen.append({
                "source_table": table, "source_id": str(row["id"]),
                "wikidata_qid": qid, "title": row["title"].strip(),
                "year": row["year"], "language": row["language_name"],
                "country": str(row.get("country_code") or "XX"),
                "media_type": "series" if table == "series_titles" else "movie",
                "image": None, "poster_candidate": None, "backdrop_candidate": None,
                "approved_for_publication": False, "production_written": False,
            })
            taken += 1

    for table, quota in QUOTAS.items():
        add(table, min(quota, limit))
    # Fill unused slots when one table has fewer eligible titles.
    for table in QUOTAS:
        add(table, limit - len(chosen))
    return chosen


def discover(samples: dict[str, list[dict]], *, limit: int = MAX_TITLES,
             get_links=article_sitelinks, get_images=film_page_images,
             get_p18=p18_by_qid, get_commons=commons_by_filename) -> dict:
    chosen = select_500(samples, limit=limit)
    qids = [x["wikidata_qid"] for x in chosen]
    if not qids:
        raise ValueError("No eligible existing title identities in D1 snapshot")
    links, sitelink_errors = get_links(qids)
    images, article_errors = get_images(links)
    # Commons fallback only for titles lacking an article poster; avoids
    # unnecessary Wikimedia requests for the most useful source.
    fallback_ids = [qid for qid in qids if shape(images.get(qid)) != "poster"]
    commons, commons_errors = {}, 0
    try:
        filenames = get_p18(fallback_ids) if fallback_ids else {}
        by_name = get_commons(list(filenames.values())) if filenames else {}
        for qid, filename in filenames.items():
            source = by_name.get(filename.replace("_", " ").casefold())
            if source and source.get("image_url"):
                commons[qid] = {
                    **source, "source": "wikidata_p18_commons",
                    "match_basis": "EXACT_WIKIDATA_QID_P18",
                    "rights_status": "REVIEW_REQUIRED",
                }
    except (ValueError, OSError, TimeoutError, KeyError):
        commons_errors += 1
    result = attach_candidates(chosen, images, commons, {
        "wikidata_sitelink_batches": sitelink_errors,
        "wikipedia_pageimage_batches": article_errors,
        "commons_batches": commons_errors,
    })
    result["schema"] = "artwork-bulk-500-v1"
    result["target_limit"] = limit
    result["d1_reads_during_discovery"] = 0
    result["new_catalogue_records"] = 0
    result["publishable_posters"] = 0
    result["displayed_in_app"] = 0
    result["rights_automatically_approved"] = 0
    result["warning"] = (
        "Candidate image URLs are not licensed for use automatically. "
        "Exact article identity, poster artwork, and usage permission "
        "must be verified before publishing."
    )
    return result


def as_csv(report: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        for row in report["candidates"]:
            image = row.get("poster_candidate") or {}
            writer.writerow({
                "source_table": row["source_table"],
                "source_id": row["source_id"],
                "wikidata_qid": row["wikidata_qid"],
                "title": row["title"],
                "year": row["year"],
                "language": row["language"],
                "media_type": row["media_type"],
                "status": row["status"],
                "poster_url": image.get("image_url", ""),
                "source_page": image.get("file_page_url", ""),
                "image_source": image.get("source", ""),
                "rights_status": "UNVERIFIED_NOT_FOR_PUBLICATION",
                "approved_for_publication": False,
            })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for table in QUOTAS:
        parser.add_argument("--" + table.replace("_", "-"), required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=MAX_TITLES)
    args = parser.parse_args()
    samples = {table: read_wrangle_rows(getattr(args, table)) for table in QUOTAS}
    report = discover(samples, limit=args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    as_csv(report, args.csv)
    print("ARTWORK_BULK_500=" + json.dumps({
        "selected": report["selected_count"],
        "posters_found": report["poster_candidates"],
        "backdrops_found": report["backdrop_candidates"],
        "identity_flags": (report["media_type_mismatch_holds"]
                           + report["year_mismatch_holds"]
                           + report["poster_filename_review_count"]),
        "source_errors": report["source_errors"],
        "published": report["displayed_in_app"],
        "d1_writes": report["d1_writes"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
