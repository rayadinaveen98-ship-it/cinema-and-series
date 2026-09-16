#!/usr/bin/env python3
"""Merge catalogue discovery payloads without weakening evidence policy.

The historical catalogue can be discovered through multiple Wikimedia paths:
WDQS/SPARQL and the normal MediaWiki/Wikibase Action APIs. During a partial
WDQS outage, some shards may succeed while others are rate-limited. This helper
combines every successful acquisition instead of treating a partial primary
response as complete.

Identity is always the stable Wikidata QID. Rows are never merged by title.
All imported rows remain unconfirmed discovery data and keep the earliest
observed day-precision release date. A per-run cap protects Cloudflare D1 Free.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

MAX_MOVIES_PER_RUN = 5000


def clean_list(values) -> list[str]:
    return sorted({str(value).strip() for value in (values or []) if str(value).strip()})


def movie_qid(movie: dict) -> str:
    return str(movie.get("wikidata_qid") or "").strip()


def merged_movie(qid: str, rows: list[dict]) -> dict:
    base = next((row for row in rows if str(row.get("title") or "").strip() not in {"", qid}), rows[0])

    dates = set()
    languages = set()
    country_codes = set()
    countries = set()
    acquisition_paths = set()

    for row in rows:
        release_date = str(row.get("release_date") or "").strip()
        if release_date:
            dates.add(release_date)
        dates.update(clean_list(row.get("candidate_dates")))
        languages.update(clean_list(row.get("languages")))
        country_codes.update(clean_list(row.get("country_codes")))
        countries.update(clean_list(row.get("countries")))
        if row.get("country_code"):
            country_codes.add(str(row["country_code"]).strip())
        if row.get("acquisition_path"):
            acquisition_paths.add(str(row["acquisition_path"]).strip())

    dates = {value for value in dates if len(value) == 10 and value[4:5] == "-" and value[7:8] == "-"}
    if not dates:
        raise ValueError(f"{qid} has no day-precision release date")

    if "Unknown" in languages and len(languages) > 1:
        languages.discard("Unknown")
    codes = sorted(code for code in country_codes if code and code != "XX")
    if not codes:
        codes = ["XX"]
    primary_country = "IN" if "IN" in codes else codes[0]

    return {
        "wikidata_qid": qid,
        "title": str(base.get("title") or qid).strip(),
        "release_date": sorted(dates)[0],
        "candidate_dates": sorted(dates),
        "languages": sorted(languages) or ["Unknown"],
        "country_code": primary_country,
        "country_codes": codes,
        "countries": sorted(countries),
        "source_url": str(base.get("source_url") or f"https://www.wikidata.org/wiki/{qid}"),
        "verification_status": "unconfirmed",
        "selection_reason": "hybrid_wikimedia_discovery_earliest_day_precision_open_data_candidate",
        "merge_strategy": "earliest",
        "acquisition_paths": sorted(acquisition_paths),
    }


def merge_payloads(payloads: list[dict], maximum: int) -> dict:
    usable = [payload for payload in payloads if payload.get("movies")]
    if not usable:
        raise ValueError("no usable catalogue payloads supplied")

    # Select identities round-robin so a large partial WDQS shard cannot crowd
    # out the fallback source before the per-run D1 safety cap is reached.
    movie_lists = [list(payload.get("movies") or []) for payload in usable]
    positions = [0] * len(movie_lists)
    selected_qids: list[str] = []
    selected = set()

    while len(selected_qids) < maximum:
        progressed = False
        for index, movies in enumerate(movie_lists):
            while positions[index] < len(movies):
                movie = movies[positions[index]]
                positions[index] += 1
                qid = movie_qid(movie)
                if not qid or qid in selected:
                    continue
                selected.add(qid)
                selected_qids.append(qid)
                progressed = True
                break
            if len(selected_qids) >= maximum:
                break
        if not progressed:
            break

    rows_by_qid: dict[str, list[dict]] = {qid: [] for qid in selected_qids}
    for payload in usable:
        path = str(payload.get("acquisition_path") or "unknown")
        for movie in payload.get("movies") or []:
            qid = movie_qid(movie)
            if qid not in rows_by_qid:
                continue
            item = dict(movie)
            item["acquisition_path"] = path
            rows_by_qid[qid].append(item)

    movies = [merged_movie(qid, rows_by_qid[qid]) for qid in selected_qids if rows_by_qid[qid]]
    movies.sort(key=lambda item: (item["release_date"], item["title"].casefold(), item["wikidata_qid"]))

    profiles = clean_list(payload.get("profile") for payload in usable)
    source_paths = clean_list(payload.get("acquisition_path") or "unknown" for payload in usable)
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "profile": profiles[0] if len(profiles) == 1 else "+".join(profiles),
        "acquisition_path": "hybrid" if len(source_paths) > 1 else source_paths[0],
        "source_acquisitions": source_paths,
        "merge_strategy": "earliest",
        "max_movies_per_run": maximum,
        "selection_policy": "QID-only hybrid Wikimedia discovery; round-robin source balance; verified/supported D1 dates remain protected by SQL layer",
        "movies": movies,
        "source_reports": [
            {
                "acquisition_path": str(payload.get("acquisition_path") or "unknown"),
                "profile": payload.get("profile"),
                "movies": len(payload.get("movies") or []),
                "shards": payload.get("shards") or [],
                "category_report": payload.get("category_report") or [],
            }
            for payload in usable
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge Wikidata/MediaWiki catalogue discovery payloads")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-movies", type=int, default=MAX_MOVIES_PER_RUN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_MOVIES_PER_RUN, args.max_movies))
    payloads = []
    for path in args.inputs:
        if not path.exists() or path.stat().st_size == 0:
            continue
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    if not payloads:
        print("No Wikimedia acquisition payloads available to merge.")
        return 1

    merged = merge_payloads(payloads, maximum)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"merged {len(payloads)} Wikimedia acquisition payload(s) into "
        f"{len(merged['movies'])} unique QID movie(s) via {merged['acquisition_path']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
