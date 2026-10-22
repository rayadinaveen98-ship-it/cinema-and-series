#!/usr/bin/env python3
"""Aggregate existing production film and series counts by recorded language.

Uses three already-aggregated, read-only Wrangler JSON query results. Movies from
the exact-date and year-only tables are deduplicated by Wikidata QID (exact
movies take priority). This is database catalogue coverage, not official
original-language verification. No app or D1 writes are performed.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows

TABLES = ("movies", "catalogue_titles", "series_titles")
COUNTRIES_IN = {"IN"}
CSV_COLUMNS = (
    "language", "films", "series", "total", "indian_films", "indian_series",
    "indian_total",
)


def clean_language(value: object) -> str:
    raw = " ".join(str(value or "").strip().split())
    if raw.casefold() in ("", "unknown", "und", "n/a", "na", "null", "none"):
        return "Unknown"
    return raw


def summarize(results: dict[str, list[dict]]) -> dict:
    if set(results) != set(TABLES):
        raise ValueError("Expected exactly all three production catalogue tables")
    global_film = Counter()
    global_series = Counter()
    india_film = Counter()
    india_series = Counter()
    table_total = Counter()
    for table in TABLES:
        for row in results[table]:
            country = str(row.get("country_code") or "").strip().upper()
            language = clean_language(row.get("language"))
            count = row.get("title_count")
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                raise ValueError(f"Invalid grouped production title count from {table}")
            if not country:
                raise ValueError(f"Missing country code from {table} aggregate")
            table_total[table] += count
            group = global_series if table == "series_titles" else global_film
            group[language] += count
            if country in COUNTRIES_IN:
                indian = india_series if table == "series_titles" else india_film
                indian[language] += count
    languages = sorted(
        set(global_film) | set(global_series),
        key=lambda language: (-(global_film[language] + global_series[language]), language.casefold()),
    )
    detail = []
    for language in languages:
        detail.append({
            "language": language, "films": global_film[language],
            "series": global_series[language],
            "total": global_film[language] + global_series[language],
            "indian_films": india_film[language],
            "indian_series": india_series[language],
            "indian_total": india_film[language] + india_series[language],
        })
    films = sum(global_film.values())
    shows = sum(global_series.values())
    total = sum(x["total"] for x in detail)
    if total != films + shows or films != table_total["movies"] + table_total["catalogue_titles"]:
        raise ValueError("Aggregates do not reconcile to their source tables")
    return {
        "schema": "cinema-series-production-language-counts-v1",
        "source": "cloudflare_d1_production_read_only",
        "scope": "all recorded countries, all recorded languages",
        "movie_dedupe": "one per QID: exact-date movies preferred over year-only catalogue_titles",
        "recorded_language_not_original_language_verified": True,
        "database_writes": 0,
        "source_table_counts": dict(table_total),
        "film_count": films,
        "series_count": shows,
        "title_count": total,
        "language_count_including_unknown": len(languages),
        "indian_films": sum(india_film.values()),
        "indian_series": sum(india_series.values()),
        "indian_titles": sum(india_film.values()) + sum(india_series.values()),
        "languages": detail,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for table in TABLES:
        p.add_argument("--" + table.replace("_", "-"), required=True, type=Path)
    p.add_argument("--json", required=True, type=Path)
    p.add_argument("--csv", required=True, type=Path)
    args = p.parse_args()
    rows = {
        table: load_d1_rows(getattr(args, table))
        for table in TABLES
    }
    result = summarize(rows)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(result["languages"])
    print("PRODUCTION_LANGUAGE_COUNTS=" + json.dumps({
        key: result[key] for key in (
            "source_table_counts", "film_count", "series_count", "title_count",
            "language_count_including_unknown", "indian_films", "indian_series",
            "indian_titles",
        )
    }, sort_keys=True), flush=True)
    print("PRODUCTION_LANGUAGE_TOP30=" + json.dumps(result["languages"][:30], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
