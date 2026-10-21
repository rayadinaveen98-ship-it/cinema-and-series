#!/usr/bin/env python3
"""Re-audit actual previously discovered 70 images without D1 or live web calls."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from artwork_fast_70 import attach_candidates, QID


def audit(snapshot: dict) -> dict:
    rows = snapshot.get("candidates")
    if (snapshot.get("schema") != "existing-title-artwork-pilot-v1"
            or snapshot.get("d1_writes") != 0
            or snapshot.get("publication_performed") is not False
            or not isinstance(rows, list)
            or len(rows) != snapshot.get("selected_count")
            or len(rows) > 70):
        raise ValueError("Not an audited, read-only 70-title artwork snapshot")
    selected, article_images = [], {}
    all_ids = set()
    for row in rows:
        if row.get("approved_for_publication") is not False or row.get("production_written") is not False:
            raise ValueError("Refusing previously published asset list")
        qid = str(row.get("wikidata_qid") or "")
        identity = (row.get("source_table"), row.get("source_id"))
        if not QID.fullmatch(qid) or identity in all_ids:
            raise ValueError("Duplicate/invalid source identity")
        all_ids.add(identity)
        selected.append({
            k: row.get(k) for k in
            ("source_table","source_id","wikidata_qid","title","year",
             "language","country","media_type")
        })
        image = row.get("image") or {}
        if image.get("source") == "wikipedia_article_pageimage":
            article_images[qid] = image
    result = attach_candidates(selected, article_images, {}, {"offline_review":0})
    result["input"] = "archived_70_title_image_pilot"
    result["new_database_queries"] = 0
    result["new_external_searches"] = 0
    result["rights_automatically_approved"] = 0
    result["review_blockers"] = [
        {
            "source_table": row["source_table"],
            "source_id": row["source_id"],
            "wikidata_qid": row["wikidata_qid"],
            "title": row["title"],
            "year": row["year"],
            "status": row["status"],
            "article_year": row.get("article_year"),
            "article_media_type": row.get("article_media_type"),
            "source_url": (row.get("image") or {}).get("file_page_url"),
            "file_name": row.get("file_name"),
        }
        for row in result["candidates"]
        if row["status"] in ("YEAR_MISMATCH_REVIEW","MEDIA_TYPE_MISMATCH_HOLD",
                            "POSTER_FILENAME_IDENTITY_REVIEW")
    ]
    return result


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--review-csv",required=True,type=Path)
    args=p.parse_args()
    report=audit(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    with args.review_csv.open("w",encoding="utf-8",newline="") as dest:
        writer=csv.DictWriter(dest,fieldnames=[
            "source_table","source_id","wikidata_qid","title","year",
            "status","article_year","article_media_type","source_url","file_name"
        ])
        writer.writeheader()
        writer.writerows(report["review_blockers"])
    print("OFFLINE_70_ARTWORK_IDENTITY_AUDIT="+json.dumps({
        "examined":report["selected_count"],
        "poster_candidates":report["poster_candidates"],
        "media_type_mismatch_holds":report["media_type_mismatch_holds"],
        "year_mismatch_holds":report["year_mismatch_holds"],
        "poster_filename_review_count":report["poster_filename_review_count"],
        "blockers":report["review_blockers"],
        "database_queries":0,
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
