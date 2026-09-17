#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

try:
    import recommendation_metadata_audit as base
except ModuleNotFoundError:
    from scripts import recommendation_metadata_audit as base

INDIA_LANGUAGES = (
    "Telugu", "Tamil", "Malayalam", "Kannada", "Hindi",
    "Bengali", "Marathi", "Gujarati", "Punjabi",
)


def normalize_language(value: object) -> str:
    text = str(value or "").strip()
    for language in INDIA_LANGUAGES:
        if text.casefold() == language.casefold():
            return language
    return "Other/Unknown"


def language_map(exact_movies, catalogue_movies, series_rows) -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for row in exact_movies:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if base.valid_qid(qid):
            result[("movie", qid)] = normalize_language(row.get("language_name"))
    for row in catalogue_movies:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if base.valid_qid(qid) and ("movie", qid) not in result:
            result[("movie", qid)] = normalize_language(row.get("language_name"))
    for row in series_rows:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if base.valid_qid(qid):
            result[("series", qid)] = normalize_language(row.get("language_name"))
    return result


def audit_cohorts(candidates: list[Mapping[str, Any]], entities: Mapping[str, Mapping[str, Any]], languages: Mapping[tuple[str, str], str]) -> dict[str, Any]:
    blocks: dict[str, dict[str, int]] = defaultdict(lambda: {
        "titles": 0, "genre": 0, "people": 0, "ready": 0,
        "movie_titles": 0, "movie_ready": 0, "series_titles": 0, "series_ready": 0,
    })

    for row in candidates:
        qid = str(row.get("wikidata_qid") or "").upper()
        media_type = str(row.get("media_type") or "")
        language = languages.get((media_type, qid), "Other/Unknown")
        block = blocks[language]
        block["titles"] += 1
        block[f"{media_type}_titles"] += 1

        entity = entities.get(qid)
        if not isinstance(entity, Mapping) or entity.get("missing"):
            continue

        genres, _ = base.claim_entity_qids(entity, base.GENRE_PROPERTY)
        directors, _ = base.claim_entity_qids(entity, base.DIRECTOR_PROPERTY)
        creators = []
        if media_type == "series":
            creators, _ = base.claim_entity_qids(entity, base.CREATOR_PROPERTY)
        cast, _ = base.claim_entity_qids(entity, base.CAST_PROPERTY)
        has_people = bool(directors or creators or cast)
        ready = bool(genres and has_people)

        if genres:
            block["genre"] += 1
        if has_people:
            block["people"] += 1
        if ready:
            block["ready"] += 1
            block[f"{media_type}_ready"] += 1

    ordered: dict[str, dict[str, Any]] = {}
    for language in (*INDIA_LANGUAGES, "Other/Unknown"):
        values = blocks[language]
        total = values["titles"]
        ordered[language] = {
            **values,
            "genre_percent": round(values["genre"] / total * 100.0, 2) if total else 0.0,
            "people_percent": round(values["people"] / total * 100.0, 2) if total else 0.0,
            "ready_percent": round(values["ready"] / total * 100.0, 2) if total else 0.0,
        }
    return ordered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-titles", type=int, default=2000)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    exact_movies = base.load_d1_rows(args.movies)
    catalogue_movies = base.load_d1_rows(args.catalogue)
    series_rows = base.load_d1_rows(args.series)
    projection = base.build_catalogue_projection(exact_movies, catalogue_movies, series_rows)
    shard = base.shard_candidates(projection["candidates"], shard_index=args.shard_index, shard_count=args.shard_count)
    if len(shard) > args.max_titles:
        raise SystemExit(f"shard contains {len(shard)} candidates, above safety cap {args.max_titles}")

    entities = base.fetch_claim_entities([row["wikidata_qid"] for row in shard])
    cohorts = audit_cohorts(shard, entities, language_map(exact_movies, catalogue_movies, series_rows))
    report = {
        "schema_version": "recommendation-metadata-india-cohort-audit-v1",
        "candidate_count": len(shard),
        "cohorts": cohorts,
        "production_mutation": False,
    }
    Path(args.out_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(shard), "production_mutation": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
