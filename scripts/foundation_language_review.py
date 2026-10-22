#!/usr/bin/env python3
"""Review-only join of archived production records and original-language evidence.

Exact QID, year and normalized title must agree. Never writes production D1,
creates SQL, or guesses language from country, cast, title or categories.
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
from production_catalogue_quality import (
    load_d1_rows, movie_projection, norm, known, valid_qid, year_from_date,
)

QID = re.compile(r"Q[1-9][0-9]*\Z")
FIELDS = ("source_table", "source_id", "wikidata_qid", "title", "year",
          "current_language", "proposed_language", "claim_property", "source_url",
          "confidence", "status")


def build(movies: list[dict], catalogue: list[dict], series: list[dict],
          checkpoint: dict) -> dict:
    if (checkpoint.get("schema") != "india-film-language-evidence-v1"
            or not isinstance(checkpoint.get("records"), dict)):
        raise ValueError("Invalid source-only original-language evidence checkpoint")
    films, overlap = movie_projection(movies, catalogue)
    sources = checkpoint["records"]
    proposals, holds = [], []
    counts = Counter()
    seen = set()
    for row in films:
        counts["projected_films"] += 1
        if known(row.get("language_name")):
            counts["films_with_known_language"] += 1
            continue
        counts["films_unknown_language"] += 1
        qid = str(row.get("wikidata_qid") or "").upper()
        country = str(row.get("country_code") or "").upper()
        if country != "IN":
            counts["non_indian_unknown_films"] += 1
            continue
        counts["indian_unknown_films"] += 1
        if not valid_qid(qid):
            counts["indian_unknown_films_without_qid"] += 1
            continue
        info = sources.get(qid)
        if not isinstance(info, dict):
            counts["indian_unknown_films_without_checkpoint_evidence"] += 1
            continue
        counts["indian_unknown_films_with_checkpoint_evidence"] += 1
        year = (year_from_date(row.get("release_date"))
                if row.get("_projection") == "movie" else row.get("release_year"))
        reason = None
        if info.get("qid") != qid or not QID.fullmatch(qid):
            reason = "qid_disagrees"
        elif not isinstance(year, int) or info.get("year") != year:
            reason = "release_year_mismatch"
        elif norm(info.get("title")) != norm(row.get("title")):
            reason = "title_mismatch"
        elif info.get("source_only") is not True or info.get("officially_verified") is not False:
            reason = "invalid_source_provenance"
        elif info.get("source_url") != "https://www.wikidata.org/wiki/" + qid:
            reason = "nonmatching_source_url"
        elif info.get("property") != "P364":
            reason = "not_explicit_original_language"
        elif info.get("status") != "single_language_evidence":
            reason = "ambiguous_or_missing_language_claim"
        elif not isinstance(info.get("language"), str) or not known(info.get("language")):
            reason = "unknown_source_language"
        if reason:
            counts["held_" + reason] += 1
            holds.append({"wikidata_qid": qid, "source_id": row.get("id"),
                          "title": row.get("title"), "reason": reason})
            continue
        if qid in seen:
            raise ValueError("Duplicate canonical film QID in selected output")
        seen.add(qid)
        proposals.append({
            "source_table": "movies" if row["_projection"] == "movie" else "catalogue_titles",
            "source_id": str(row["id"]), "wikidata_qid": qid,
            "title": row["title"], "year": year,
            "current_language": row.get("language_name") or "Unknown",
            "proposed_language": info["language"], "claim_property": "P364",
            "source_url": info["source_url"], "confidence": "source_evidence_only",
            "status": "REVIEW_REQUIRED",
        })
    counts["series_records"] = len(series)
    counts["series_unknown_language"] = sum(
        not known(x.get("language_name")) for x in series)
    counts["overlapping_film_table_records_excluded"] = overlap
    counts["source_checkpoint_records"] = len(sources)
    counts["review_proposals"] = len(proposals)
    counts["held_evidence_rows"] = len(holds)
    if counts["films_with_known_language"] + counts["films_unknown_language"] != counts["projected_films"]:
        raise AssertionError("Film accounting drift")
    if counts["films_unknown_language"] + counts["series_unknown_language"] < len(proposals):
        raise AssertionError("Too many language proposals")
    return {
        "schema": "foundation-v2-language-review-v1",
        "read_only": True, "d1_reads_this_run": 0, "d1_writes": 0,
        "publication_performed": False, "automatic_corrections": 0,
        "baseline_existing_only": True,
        "source": "archived_production_snapshot_plus_existing_P364_checkpoint",
        "counts": dict(counts), "proposals": proposals, "holds": holds,
        "note": ("Wikidata P364 is source evidence only. Review current item identity "
                 "and claims before authorizing D1 changes. No SQL generated."),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("movies", "catalogue", "series", "checkpoint", "out", "csv"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    result = build(
        load_d1_rows(args.movies), load_d1_rows(args.catalogue),
        load_d1_rows(args.series),
        json.loads(args.checkpoint.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(result["proposals"])
    print("DATA_FOUNDATION_LANGUAGE_REVIEW=" + json.dumps(result["counts"], sort_keys=True),
          flush=True)


if __name__ == "__main__":
    main()
