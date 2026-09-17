#!/usr/bin/env python3
"""Read-only Recommendation Metadata Foundation V1 audit.

The audit projects the current Movie + Series catalogue onto stable Wikidata
identities, then measures explicit recommendation metadata availability from:

- P136 genre
- P57 director
- P170 creator (Series only)
- P161 cast member

It does not mutate D1, infer metadata, or auto-resolve movie/series identity
collisions. Exact-date movie rows win over the year-precision movie projection
when both share a Wikidata QID, matching Catalogue Quality V1 counting rules.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import fetch_mediawiki_backfill as base
except ModuleNotFoundError:  # unittest imports from repository root
    from scripts import fetch_mediawiki_backfill as base

GENRE_PROPERTY = "P136"
DIRECTOR_PROPERTY = "P57"
CREATOR_PROPERTY = "P170"
CAST_PROPERTY = "P161"
ENTITY_BATCH = 25
REQUEST_DELAY_SECONDS = 0.75
MAX_BATCH_RETRIES = 6
MAX_BACKOFF_SECONDS = 45
TRANSIENT_MEDIAWIKI_ERRORS = {"maxlag", "ratelimited"}
QID_RE = re.compile(r"^Q\d+$", re.IGNORECASE)


def valid_qid(value: object) -> bool:
    return bool(QID_RE.fullmatch(str(value or "").strip()))


def qid_number(value: object) -> int:
    text = str(value or "").strip().upper()
    if not valid_qid(text):
        raise ValueError(f"invalid Wikidata QID: {value!r}")
    return int(text[1:])


def load_d1_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for batch in payload:
            if isinstance(batch, dict) and isinstance(batch.get("results"), list):
                rows.extend(row for row in batch["results"] if isinstance(row, dict))
        return rows
    if isinstance(payload, dict):
        for key in ("results", "rows"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    raise ValueError(f"{path}: unsupported D1 JSON shape")


def _source_url(row: Mapping[str, Any], qid: str) -> str:
    value = str(row.get("source_url") or "").strip()
    return value or f"https://www.wikidata.org/wiki/{qid}"


def _project_row(row: Mapping[str, Any], media_type: str, source_table: str) -> dict[str, Any]:
    qid = str(row.get("wikidata_qid") or "").strip().upper()
    return {
        "id": f"wikidata:{qid}",
        "wikidata_qid": qid,
        "media_type": media_type,
        "display_title": str(row.get("title") or "").strip(),
        "source_table": source_table,
        "source_id": str(row.get("id") or "").strip(),
        "source_url": _source_url(row, qid),
    }


def build_catalogue_projection(
    exact_movies: Iterable[Mapping[str, Any]],
    catalogue_movies: Iterable[Mapping[str, Any]],
    series_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one QID-backed recommendation identity per projected title.

    Exact-date movies take precedence over year-only movie rows. A QID found in
    both Movie and Series projections is reported as a collision and excluded
    from the audit candidate set.
    """
    movie_by_qid: dict[str, dict[str, Any]] = {}
    suppressed_catalogue_overlaps = 0

    for row in exact_movies:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if valid_qid(qid):
            movie_by_qid[qid] = _project_row(row, "movie", "movies")

    for row in catalogue_movies:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if not valid_qid(qid):
            continue
        if qid in movie_by_qid:
            suppressed_catalogue_overlaps += 1
            continue
        movie_by_qid[qid] = _project_row(row, "movie", "catalogue_titles")

    series_by_qid: dict[str, dict[str, Any]] = {}
    for row in series_rows:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if valid_qid(qid):
            series_by_qid[qid] = _project_row(row, "series", "series_titles")

    collisions = sorted(set(movie_by_qid) & set(series_by_qid), key=qid_number)
    candidates = [row for qid, row in movie_by_qid.items() if qid not in collisions]
    candidates.extend(row for qid, row in series_by_qid.items() if qid not in collisions)
    candidates.sort(key=lambda row: qid_number(row["wikidata_qid"]))

    return {
        "candidates": candidates,
        "movie_qid_count": len(movie_by_qid),
        "series_qid_count": len(series_by_qid),
        "suppressed_catalogue_overlap_count": suppressed_catalogue_overlaps,
        "cross_type_collision_qids": collisions,
    }


def shard_candidates(
    rows: Iterable[Mapping[str, Any]], *, shard_index: int = 0, shard_count: int = 1
) -> list[dict[str, Any]]:
    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError(f"shard_index must be between 0 and {shard_count - 1}")
    output = [
        dict(row)
        for row in rows
        if qid_number(row.get("wikidata_qid")) % shard_count == shard_index
    ]
    output.sort(key=lambda row: qid_number(row["wikidata_qid"]))
    return output


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def retry_after_seconds(exc: urllib.error.HTTPError) -> int:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    try:
        return max(1, int(raw)) if raw else 0
    except (TypeError, ValueError):
        return 0


def mediawiki_retry_delay(error: Mapping[str, Any], attempt: int) -> int:
    exponential = min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2))
    lag = error.get("lag")
    try:
        lag_delay = max(1, int(float(lag)) + 1) if lag is not None else 0
    except (TypeError, ValueError):
        lag_delay = 0
    return min(MAX_BACKOFF_SECONDS, max(exponential, lag_delay))


def request_wikidata(params: dict[str, str]) -> dict[str, Any]:
    request_params = {**params, "maxlag": "5"}
    last_error: Exception | None = None
    for attempt in range(MAX_BATCH_RETRIES):
        try:
            payload = base.request_json(base.WIKIDATA_API, request_params, post=False)
            api_error = payload.get("error") if isinstance(payload, Mapping) else None
            if isinstance(api_error, Mapping):
                code = str(api_error.get("code") or "unknown").strip().casefold()
                info = str(api_error.get("info") or "").strip()
                if code in TRANSIENT_MEDIAWIKI_ERRORS:
                    if attempt + 1 >= MAX_BATCH_RETRIES:
                        raise RuntimeError(
                            f"Wikidata transient API error persisted after {MAX_BATCH_RETRIES} attempts: "
                            f"{code}: {info}"
                        )
                    time.sleep(mediawiki_retry_delay(api_error, attempt))
                    continue
                raise RuntimeError(f"Wikidata API error {code}: {info}")
            if not isinstance(payload, dict):
                raise RuntimeError("Wikidata API returned a non-object JSON payload")
            return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt + 1 >= MAX_BATCH_RETRIES:
                raise
            exponential = min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2))
            time.sleep(min(MAX_BACKOFF_SECONDS, max(retry_after_seconds(exc), exponential)))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 >= MAX_BATCH_RETRIES:
                raise
            time.sleep(min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2)))
    raise RuntimeError(f"unreachable Wikidata request failure: {last_error}")


def fetch_claim_entities(qids: list[str]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for batch in chunks(qids, ENTITY_BATCH):
        payload = request_wikidata({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        })
        for qid, entity in (payload.get("entities") or {}).items():
            if isinstance(entity, dict):
                entities[str(qid).upper()] = entity
        time.sleep(REQUEST_DELAY_SECONDS)
    return entities


def claim_entity_qids(entity: Mapping[str, Any], property_id: str) -> tuple[list[str], int]:
    """Return unique valid entity QIDs and count unusable non-deprecated claims."""
    values: list[str] = []
    unusable = 0
    for claim in ((entity.get("claims") or {}).get(property_id) or []):
        if not isinstance(claim, Mapping) or claim.get("rank") == "deprecated":
            continue
        mainsnak = claim.get("mainsnak") or {}
        if mainsnak.get("snaktype") != "value":
            unusable += 1
            continue
        value = (mainsnak.get("datavalue") or {}).get("value")
        qid = value.get("id") if isinstance(value, Mapping) else None
        if not valid_qid(qid):
            unusable += 1
            continue
        values.append(str(qid).upper())
    return sorted(set(values), key=qid_number), unusable


def audit_candidates(
    candidates: list[Mapping[str, Any]],
    entities: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    media = {
        "movie": {"titles": 0, "genre": 0, "director_or_creator": 0, "cast": 0, "people": 0, "ready": 0},
        "series": {"titles": 0, "genre": 0, "director_or_creator": 0, "cast": 0, "people": 0, "ready": 0},
    }
    relation_counts = {"P136": 0, "P57": 0, "P170": 0, "P161": 0}
    unique_genres: set[str] = set()
    unique_people: set[str] = set()
    unusable_claim_count = 0
    missing_entity_count = 0
    high_fanout_cast_titles = 0
    samples: list[dict[str, Any]] = []

    for row in candidates:
        qid = str(row.get("wikidata_qid") or "").upper()
        media_type = str(row.get("media_type") or "")
        media[media_type]["titles"] += 1
        entity = entities.get(qid)
        if not isinstance(entity, Mapping) or entity.get("missing"):
            missing_entity_count += 1
            continue

        genres, bad = claim_entity_qids(entity, GENRE_PROPERTY)
        unusable_claim_count += bad
        directors, bad = claim_entity_qids(entity, DIRECTOR_PROPERTY)
        unusable_claim_count += bad
        creators: list[str] = []
        if media_type == "series":
            creators, bad = claim_entity_qids(entity, CREATOR_PROPERTY)
            unusable_claim_count += bad
        cast, bad = claim_entity_qids(entity, CAST_PROPERTY)
        unusable_claim_count += bad

        relation_counts[GENRE_PROPERTY] += len(genres)
        relation_counts[DIRECTOR_PROPERTY] += len(directors)
        relation_counts[CREATOR_PROPERTY] += len(creators)
        relation_counts[CAST_PROPERTY] += len(cast)
        unique_genres.update(genres)
        unique_people.update(directors)
        unique_people.update(creators)
        unique_people.update(cast)

        if genres:
            media[media_type]["genre"] += 1
        if directors or creators:
            media[media_type]["director_or_creator"] += 1
        if cast:
            media[media_type]["cast"] += 1
        has_people = bool(directors or creators or cast)
        if has_people:
            media[media_type]["people"] += 1
        ready = bool(genres and has_people)
        if ready:
            media[media_type]["ready"] += 1
        if len(cast) > 50:
            high_fanout_cast_titles += 1

        if len(samples) < 20 and (genres or directors or creators or cast):
            samples.append({
                "wikidata_qid": qid,
                "media_type": media_type,
                "title": row.get("display_title"),
                "genre_count": len(genres),
                "director_count": len(directors),
                "creator_count": len(creators),
                "cast_count": len(cast),
                "recommendation_ready": ready,
            })

    for values in media.values():
        total = values["titles"]
        values["ready_percent"] = round((values["ready"] / total * 100.0), 2) if total else 0.0
        values["genre_percent"] = round((values["genre"] / total * 100.0), 2) if total else 0.0
        values["people_percent"] = round((values["people"] / total * 100.0), 2) if total else 0.0

    return {
        "candidate_count": len(candidates),
        "media": media,
        "relation_counts": relation_counts,
        "unique_genre_qid_count": len(unique_genres),
        "unique_people_qid_count": len(unique_people),
        "missing_entity_count": missing_entity_count,
        "unusable_claim_count": unusable_claim_count,
        "high_fanout_cast_title_count": high_fanout_cast_titles,
        "samples": samples,
        "production_mutation": False,
    }


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

    projection = build_catalogue_projection(
        load_d1_rows(args.movies), load_d1_rows(args.catalogue), load_d1_rows(args.series)
    )
    shard = shard_candidates(
        projection["candidates"], shard_index=args.shard_index, shard_count=args.shard_count
    )
    if len(shard) > args.max_titles:
        raise SystemExit(
            f"shard contains {len(shard)} candidates, above safety cap {args.max_titles}; increase only after review"
        )

    entities = fetch_claim_entities([row["wikidata_qid"] for row in shard])
    audit = audit_candidates(shard, entities)
    report = {
        "schema_version": "recommendation-metadata-foundation-v1-audit",
        "source_contract": {
            "genre": "wikidata:P136",
            "director": "wikidata:P57",
            "creator_series_only": "wikidata:P170",
            "cast": "wikidata:P161",
            "inference": False,
        },
        "projection": {
            "movie_qid_count": projection["movie_qid_count"],
            "series_qid_count": projection["series_qid_count"],
            "suppressed_catalogue_overlap_count": projection["suppressed_catalogue_overlap_count"],
            "cross_type_collision_qids": projection["cross_type_collision_qids"],
        },
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        **audit,
    }
    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_count": report["candidate_count"],
        "movie_ready": report["media"]["movie"]["ready"],
        "series_ready": report["media"]["series"]["ready"],
        "unique_genres": report["unique_genre_qid_count"],
        "unique_people": report["unique_people_qid_count"],
        "cross_type_collisions": len(report["projection"]["cross_type_collision_qids"]),
        "production_mutation": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
