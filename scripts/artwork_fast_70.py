#!/usr/bin/env python3
"""50 movies + 20 series: exact-existing-title rapid artwork candidate discovery.

Reads only bounded D1-exported identity snapshots, then tries the matched film
or series' actual Wikipedia article image. Wikimedia Commons P18 remains a
secondary lead, NOT the only source. Nothing is auto-licensed or published.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from existing_title_artwork_pilot import (
    commons_by_filename, p18_by_qid, read_wrangle_rows,
)
from wikipedia_film_posters_pilot import article_sitelinks, film_page_images

QID = re.compile(r"Q[1-9][0-9]*\Z")
QUOTAS = {"movies": 35, "catalogue_titles": 15, "series_titles": 20}
LANGUAGE = {"Telugu", "Tamil", "Malayalam", "Hindi", "Kannada", "Bengali", "Marathi"}


def select(rows_by_table: dict[str, list[dict]]) -> list[dict]:
    seen = set()
    chosen = []
    order = {"Telugu": 0, "Tamil": 1, "Malayalam": 2, "Hindi": 3,
             "Kannada": 4, "Bengali": 5, "Marathi": 6}
    for table, maximum in QUOTAS.items():
        taken = 0
        ranked = sorted(rows_by_table.get(table, []),
            key=lambda r: (order.get(str(r.get("language_name")), 10),
                           -(r.get("year") if isinstance(r.get("year"), int) else 0),
                           str(r.get("title") or "")))
        for row in ranked:
            qid = str(row.get("wikidata_qid") or "")
            title = str(row.get("title") or "").strip()
            year = row.get("year")
            if (not QID.fullmatch(qid) or not title or qid == title or
                    qid in seen or not isinstance(year, int) or year < 1888 or year > 2035 or
                    str(row.get("language_name") or "") not in LANGUAGE):
                continue
            chosen.append({
                "source_table": table,
                "source_id": str(row.get("id")),
                "media_type": "series" if table == "series_titles" else "movie",
                "wikidata_qid": qid,
                "title": title, "year": year,
                "language": row["language_name"],
                "country": str(row.get("country_code") or "XX"),
                "status": "SEARCH_PENDING", "match_basis": None,
                "image": None, "poster_candidate": None, "backdrop_candidate": None,
                "file_name": None, "approved_for_publication": False,
                "production_written": False,
            })
            taken += 1
            seen.add(qid)
            if taken == maximum:
                break
    return chosen


def shape(image: dict | None) -> str:
    if not isinstance(image, dict):
        return "unknown"
    try:
        width, height = float(image.get("width")), float(image.get("height"))
        if width <= 0 or height <= 0:
            return "unknown"
        if height / width >= 1.25:
            return "poster"
        if width / height >= 1.25:
            return "backdrop"
    except (TypeError, ValueError, OverflowError, ZeroDivisionError):
        pass
    return "unknown"


def attach_candidates(
    chosen: list[dict],
    article_images: dict[str, dict],
    commons_images: dict[str, dict],
    errors: dict[str, int],
) -> dict:
    output = []
    counts = Counter()
    for row in chosen:
        item = dict(row)
        qid = item["wikidata_qid"]
        article = article_images.get(qid)
        commons = commons_images.get(qid)
        viable = []
        for source in (article, commons):
            if isinstance(source, dict) and isinstance(source.get("image_url"), str):
                viable.append(source)
        for source in viable:
            if shape(source) == "poster" and not item["poster_candidate"]:
                item["poster_candidate"] = source
            if shape(source) == "backdrop" and not item["backdrop_candidate"]:
                item["backdrop_candidate"] = source
        item["image"] = item["poster_candidate"] or item["backdrop_candidate"] or (viable[0] if viable else None)
        item["file_name"] = (item["image"] or {}).get("pageimage_filename")
        item["match_basis"] = (item["image"] or {}).get("match_basis")
        if item["poster_candidate"]:
            item["status"] = "POSTER_CANDIDATE_REVIEW"
        elif item["backdrop_candidate"]:
            item["status"] = "BACKDROP_CANDIDATE_REVIEW"
        elif viable:
            item["status"] = "IMAGE_UNSUITABLE_ORIENTATION_REVIEW"
        else:
            item["status"] = "NO_IMAGE_FOUND"
        item["approved_for_publication"] = False
        item["production_written"] = False
        counts[item["status"]] += 1
        output.append(item)
    return {
        "schema": "existing-title-artwork-pilot-v1",
        "read_only": True, "d1_writes": 0, "publication_performed": False,
        "selected_count": len(output), "selected_by_table": dict(Counter(x["source_table"] for x in output)),
        "status_counts": dict(counts),
        "poster_candidates": sum(bool(x["poster_candidate"]) for x in output),
        "backdrop_candidates": sum(bool(x["backdrop_candidate"]) for x in output),
        "visible_artwork_candidates": sum(bool(x["image"]) for x in output),
        "source_errors": errors,
        "warning": "Article preview is not a reusable artwork license; review the actual image, year and publication terms.",
        "candidates": output,
    }


def run(rows: dict[str, list[dict]], *,
        get_links=article_sitelinks, get_images=film_page_images,
        get_p18=p18_by_qid, get_commons=commons_by_filename) -> dict:
    selected = select(rows)
    qids = [x["wikidata_qid"] for x in selected]
    sites, link_errors = get_links(qids)
    article_images, page_errors = get_images(sites)
    need_secondary = [q for q in qids if q not in article_images or shape(article_images.get(q)) != "poster"]
    try:
        claims = get_p18(need_secondary)
        commons_by_name = get_commons(list(claims.values())) if claims else {}
        commons = {
            q: {
                **commons_by_name[name.replace("_", " ").casefold()],
                "source": "wikidata_p18_commons",
                "match_basis": "EXACT_WIKIDATA_QID_P18",
                "rights_status": "REVIEW_REQUIRED",
            }
            for q, name in claims.items()
            if name.replace("_", " ").casefold() in commons_by_name
        }
        commons_errors = 0
    except (OSError, ValueError, TimeoutError):
        commons = {}
        commons_errors = 1
    return attach_candidates(selected, article_images, commons, {
        "wikidata_sitelink_batches": link_errors,
        "wikipedia_pageimage_batches": page_errors,
        "commons_batches": commons_errors,
    })


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    for table in QUOTAS:
        parser.add_argument("--"+table.replace("_","-"), type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    rows={table: read_wrangle_rows(getattr(args,table)) for table in QUOTAS}
    result=run(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("ARTWORK_FAST70="+json.dumps({
        k:result[k] for k in ("selected_count","selected_by_table","poster_candidates",
                             "backdrop_candidates","visible_artwork_candidates","source_errors")
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
