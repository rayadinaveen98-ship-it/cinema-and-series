#!/usr/bin/env python3
"""Run immediate 500-title artwork SOURCE discovery without Cloudflare D1.

Uses 70 real previously exported D1 identities plus up to 430 separate,
explicitly unconfirmed Wikipedia category source records. The external QIDs
must not be treated as records in the app until independently joined to D1.
This script never publishes copyrighted artwork or mutates production.
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
from india_daily_autopilot import eligible_queue_items
from existing_title_artwork_pilot import p18_by_qid, commons_by_filename
from wikipedia_film_posters_pilot import article_sitelinks, film_page_images

MAX_TOTAL = 500
EXACT_ARCHIVE_COUNT = 70
LANGUAGES = ("Telugu", "Tamil", "Malayalam", "Kannada", "Hindi", "Bengali", "Marathi")
QID = re.compile(r"Q[1-9]\d*\Z")
CSV_FIELDS = (
    "wikidata_qid", "title", "year", "language", "media_type",
    "database_identity_confirmed", "source_table", "source_id",
    "status", "poster_candidate_url", "source_article",
    "rights_status", "published_in_app",
)


def infer_language(item: dict) -> str:
    hints = " ".join(str(x) for x in (
        item.get("observed_languages") or []
    ) + (item.get("source_categories") or [])).casefold()
    for language in LANGUAGES:
        if language.casefold() in hints:
            return language
    return "Unknown"


def select_external(state: dict, archived_qids: set[str], max_new: int) -> list[dict]:
    if state.get("schema_version") != 1 or not isinstance(state.get("queue"), dict):
        raise ValueError("Unexpected durable India film source checkpoint")
    if not 0 <= max_new <= MAX_TOTAL - EXACT_ARCHIVE_COUNT:
        raise ValueError("Unsafe new candidate limit")
    choices = eligible_queue_items(state["queue"])
    choices.sort(key=lambda x: (
        LANGUAGES.index(infer_language(x)) if infer_language(x) in LANGUAGES else 99,
        -int(x["year"]), str(x["title"]).casefold(), x["wikidata_qid"],
    ))
    new = []
    seen = set(archived_qids)
    for raw in choices:
        qid = str(raw.get("wikidata_qid") or "")
        title = str(raw.get("title") or "").strip()
        year = raw.get("year")
        page = raw.get("page_id")
        if (not QID.fullmatch(qid) or qid in seen or not title or title.upper() == qid
                or not isinstance(year, int) or not 1888 <= year <= 2026
                or not isinstance(page, int) or page <= 0):
            continue
        new.append({
            "source_table": "external_source_only",
            "source_id": None,
            "wikidata_qid": qid, "title": title, "year": year,
            "language": infer_language(raw), "country": "IN",
            "media_type": "movie", "image": None,
            "poster_candidate": None, "backdrop_candidate": None,
            "approved_for_publication": False, "production_written": False,
            "database_identity_confirmed": False,
            "source_wikipedia_page_id": page,
        })
        seen.add(qid)
        if len(new) >= max_new:
            break
    return new


def run(archive: dict, state: dict, *, total: int = MAX_TOTAL,
        get_links=article_sitelinks, get_images=film_page_images,
        get_p18=p18_by_qid, get_commons=commons_by_filename) -> dict:
    rows = archive.get("candidates")
    if (archive.get("schema") != "existing-title-artwork-pilot-v1" or
            archive.get("d1_writes") != 0 or archive.get("publication_performed") is not False
            or not isinstance(rows, list) or len(rows) != EXACT_ARCHIVE_COUNT
            or archive.get("selected_count") != EXACT_ARCHIVE_COUNT
            or not EXACT_ARCHIVE_COUNT <= total <= MAX_TOTAL):
        raise ValueError("Invalid completed read-only 70-title production archive")
    existing = []
    known_qids = set()
    for item in rows:
        qid = item.get("wikidata_qid")
        if (not isinstance(qid, str) or not QID.fullmatch(qid) or qid in known_qids
                or not item.get("source_id") or
                item.get("source_table") not in ("movies", "catalogue_titles", "series_titles")
                or item.get("approved_for_publication") is not False or
                item.get("production_written") is not False):
            raise ValueError("Archive contains invalid or previously published identities")
        known_qids.add(qid)
        existing.append({
            **item,
            "database_identity_confirmed": True,
            "rights_status": "UNVERIFIED_NOT_FOR_PUBLICATION",
            "approved_for_publication": False,
            "production_written": False,
        })

    selected = select_external(state, known_qids, total - len(existing))
    qids = [item["wikidata_qid"] for item in selected]
    article_images, commons, errors = {}, {}, {
        "wikidata_sitelinks": 0, "wikipedia_images": 0, "commons": 0,
    }
    if qids:
        links, errors["wikidata_sitelinks"] = get_links(qids)
        article_images, errors["wikipedia_images"] = get_images(links)
        missing = [qid for qid in qids if shape(article_images.get(qid)) != "poster"]
        try:
            p18 = get_p18(missing) if missing else {}
            images = get_commons(list(p18.values())) if p18 else {}
            for qid, name in p18.items():
                saved = images.get(name.replace("_", " ").casefold())
                if saved and saved.get("image_url"):
                    commons[qid] = {
                        **saved, "source": "wikidata_p18_commons",
                        "match_basis": "EXACT_WIKIDATA_QID_P18",
                        "rights_status": "REVIEW_REQUIRED",
                    }
        except (OSError, TimeoutError, ValueError, KeyError):
            errors["commons"] = 1
    result = attach_candidates(selected, article_images, commons, errors)
    # External records are source discovery only. The 70 archived records are
    # the only ones previously joined to a real app D1 ID.
    combined = existing + result["candidates"]
    status = Counter(x.get("status") or "UNKNOWN" for x in combined)
    return {
        "schema": "artwork-v2-immediate-source-only-v1",
        "selected": len(combined),
        "from_existing_d1_archive": len(existing),
        "from_unconfirmed_source_queue": len(selected),
        "new_external_poster_leads": result["poster_candidates"],
        "new_external_backdrop_leads": result["backdrop_candidates"],
        "total_candidate_posters_including_archived": sum(
            bool(x.get("poster_candidate")) for x in combined
        ),
        "status_counts": dict(status),
        "source_errors": errors,
        "d1_reads": 0, "d1_writes": 0, "new_catalogue_records": 0,
        "rights_automatically_approved": 0, "published_in_app": 0,
        "warning": ("External source QIDs are not confirmed in the app database. "
                    "All image URLs are discovery leads only; official looking "
                    "artwork is not proof of publication rights."),
        "candidates": combined,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive70", required=True, type=Path)
    parser.add_argument("--source-state", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()
    report = run(json.loads(args.archive70.read_text(encoding="utf-8")),
                 json.loads(args.source_state.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in report["candidates"]:
            poster = row.get("poster_candidate") or {}
            writer.writerow({
                "wikidata_qid": row["wikidata_qid"],
                "title": row["title"], "year": row["year"],
                "language": row.get("language") or "Unknown",
                "media_type": row["media_type"],
                "database_identity_confirmed": row["database_identity_confirmed"],
                "source_table": row["source_table"],
                "source_id": row.get("source_id") or "",
                "status": row.get("status"),
                "poster_candidate_url": poster.get("image_url", ""),
                "source_article": poster.get("file_page_url", ""),
                "rights_status": "UNVERIFIED_NOT_FOR_PUBLICATION",
                "published_in_app": False,
            })
    print("IMMEDIATE_SOURCE_ONLY_ARTWORK=" + json.dumps({
        key: report[key] for key in (
            "selected", "from_existing_d1_archive", "from_unconfirmed_source_queue",
            "new_external_poster_leads", "total_candidate_posters_including_archived",
            "source_errors", "d1_reads", "d1_writes", "published_in_app",
        )
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
