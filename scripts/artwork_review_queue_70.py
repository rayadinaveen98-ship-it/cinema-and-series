#!/usr/bin/env python3
"""Rank archived 70-title artwork leads for human review without D1 or new searches.

A matching Wikipedia pageimage is *not* a license to reuse the image in the
application. This report never publishes or approves artwork.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_artwork70_snapshot import audit

BLOCKED = {
    "MEDIA_TYPE_MISMATCH_HOLD",
    "YEAR_MISMATCH_REVIEW",
    "POSTER_FILENAME_IDENTITY_REVIEW",
}
LANGUAGE_ORDER = {
    "Telugu": 0, "Tamil": 1, "Malayalam": 2, "Hindi": 3,
    "Kannada": 4, "Bengali": 5, "Marathi": 6,
}
FIELDS = (
    "review_priority", "action", "source_table", "source_id", "wikidata_qid",
    "title", "year", "language", "media_type", "identity_status",
    "poster_source", "poster_filename", "poster_page_url", "poster_preview_url",
    "backdrop_source", "backdrop_page_url", "backdrop_preview_url", "rights_status",
    "approved_for_publication",
)


def make_queue(snapshot: dict) -> dict:
    checked = audit(snapshot)
    entries = []
    for item in checked["candidates"]:
        poster = item.get("poster_candidate") or {}
        backdrop = item.get("backdrop_candidate") or {}
        status = item["status"]
        if status in BLOCKED:
            priority, action = 0, "RESOLVE_IDENTITY_BEFORE_IMAGE_REVIEW"
        elif poster:
            priority, action = 1, "CHECK_ORIGINAL_POSTER_AND_USAGE_RIGHTS"
        elif backdrop:
            priority, action = 2, "BACKDROP_ONLY_FIND_POSTER"
        else:
            priority, action = 3, "NO_POSTER_FOUND_FIND_TRUSTED_SOURCE"

        entries.append({
            "review_priority": priority,
            "action": action,
            "source_table": item["source_table"],
            "source_id": item["source_id"],
            "wikidata_qid": item["wikidata_qid"],
            "title": item["title"],
            "year": item["year"],
            "language": item["language"],
            "media_type": item["media_type"],
            "identity_status": status,
            "poster_source": poster.get("source") or "",
            "poster_filename": poster.get("pageimage_filename") or "",
            "poster_page_url": poster.get("file_page_url") or "",
            "poster_preview_url": poster.get("image_url") or "",
            "backdrop_source": backdrop.get("source") or "",
            "backdrop_page_url": backdrop.get("file_page_url") or "",
            "backdrop_preview_url": backdrop.get("image_url") or "",
            "rights_status": "UNVERIFIED_NOT_FOR_PUBLICATION",
            "approved_for_publication": False,
        })
    entries.sort(key=lambda r: (
        r["review_priority"],
        LANGUAGE_ORDER.get(str(r["language"]), 10),
        -(r["year"] if isinstance(r["year"], int) else 0),
        str(r["title"]).casefold(),
        str(r["wikidata_qid"]),
    ))
    counts = Counter(row["action"] for row in entries)
    return {
        "schema": "artwork70-manual-review-queue-v1",
        "selected_count": len(entries),
        "poster_leads": checked["poster_candidates"],
        "backdrop_leads": checked["backdrop_candidates"],
        "unresolved_identity_flags": sum(row["review_priority"] == 0 for row in entries),
        "ready_for_publication": 0,
        "rights_automatically_approved": 0,
        "database_reads": 0,
        "database_writes": 0,
        "new_external_searches": 0,
        "publication_performed": False,
        "action_counts": dict(counts),
        "notice": (
            "Image URLs are review leads only. Wikipedia article images may be "
            "non-free. Independently verify title identity, source authority, "
            "usage rights, license and attribution before any publication."
        ),
        "queue": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()

    snapshot = json.loads(args.input.read_text(encoding="utf-8"))
    result = make_queue(snapshot)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    with args.csv.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(result["queue"])
    print("ARTWORK70_REVIEW_QUEUE=" + json.dumps({
        "selected_count": result["selected_count"],
        "poster_leads": result["poster_leads"],
        "unresolved_identity_flags": result["unresolved_identity_flags"],
        "action_counts": result["action_counts"],
        "database_reads": 0,
        "publication_performed": False,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
