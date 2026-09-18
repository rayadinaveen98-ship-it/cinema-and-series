#!/usr/bin/env python3
"""Recommendation Metadata Foundation V1 materializer.

Builds normalized recommendation-title, genre, person and relationship rows only
from explicit Wikidata claims already allowed by the P1 source contract:

- P136 genre
- P57 director
- P170 creator (Series only)
- P161 cast member

The command is dry-run by design. It writes a JSON report and SQL artifact to
local files; it never connects to or mutates D1. Production application belongs
to a separately guarded workflow after an audited main-branch analysis.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import recommendation_metadata_audit as audit
except ModuleNotFoundError:  # unittest imports from repository root
    from scripts import recommendation_metadata_audit as audit

LABEL_LANGUAGES = ("en", "mul")


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def entity_url(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{qid}"


def sql_quote(value: object) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def fetch_entity_labels(qids: list[str]) -> dict[str, str]:
    """Resolve canonical display labels without guessing.

    English is preferred. Wikidata's multilingual `mul` label is accepted as an
    explicit fallback. If neither exists, the entity is deliberately left
    unresolved and no relationship row depending on its label is emitted.
    """
    labels: dict[str, str] = {}
    unique = sorted({str(qid).upper() for qid in qids if audit.valid_qid(qid)}, key=audit.qid_number)
    for batch in chunks(unique, audit.ENTITY_BATCH):
        payload = audit.request_wikidata({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "labels",
            "languages": "|".join(LABEL_LANGUAGES),
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        })
        for qid, entity in (payload.get("entities") or {}).items():
            if not isinstance(entity, Mapping) or entity.get("missing"):
                continue
            entity_labels = entity.get("labels") or {}
            chosen = ""
            for language in LABEL_LANGUAGES:
                candidate = entity_labels.get(language)
                if isinstance(candidate, Mapping):
                    value = str(candidate.get("value") or "").strip()
                    if value:
                        chosen = value
                        break
            if chosen:
                labels[str(qid).upper()] = chosen
        time.sleep(audit.REQUEST_DELAY_SECONDS)
    return labels


def collect_relations(
    candidates: list[Mapping[str, Any]],
    entities: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], set[str], set[str], dict[str, int]]:
    """Collect explicit QID relations before label resolution."""
    relations: list[dict[str, Any]] = []
    genre_qids: set[str] = set()
    people_qids: set[str] = set()
    stats = {
        "missing_title_entities": 0,
        "unusable_claims": 0,
        "genre_relations": 0,
        "director_relations": 0,
        "creator_relations": 0,
        "cast_relations": 0,
    }

    for row in candidates:
        title_qid = str(row.get("wikidata_qid") or "").upper()
        media_type = str(row.get("media_type") or "")
        entity = entities.get(title_qid)
        if not isinstance(entity, Mapping) or entity.get("missing"):
            stats["missing_title_entities"] += 1
            continue

        genres, bad = audit.claim_entity_qids(entity, audit.GENRE_PROPERTY)
        stats["unusable_claims"] += bad
        directors, bad = audit.claim_entity_qids(entity, audit.DIRECTOR_PROPERTY)
        stats["unusable_claims"] += bad
        creators: list[str] = []
        if media_type == "series":
            creators, bad = audit.claim_entity_qids(entity, audit.CREATOR_PROPERTY)
            stats["unusable_claims"] += bad
        cast, bad = audit.claim_entity_qids(entity, audit.CAST_PROPERTY)
        stats["unusable_claims"] += bad

        for qid in genres:
            genre_qids.add(qid)
            relations.append({"title_qid": title_qid, "target_qid": qid, "kind": "genre", "role": None, "property": audit.GENRE_PROPERTY})
        for qid in directors:
            people_qids.add(qid)
            relations.append({"title_qid": title_qid, "target_qid": qid, "kind": "credit", "role": "director", "property": audit.DIRECTOR_PROPERTY})
        for qid in creators:
            people_qids.add(qid)
            relations.append({"title_qid": title_qid, "target_qid": qid, "kind": "credit", "role": "creator", "property": audit.CREATOR_PROPERTY})
        for qid in cast:
            people_qids.add(qid)
            relations.append({"title_qid": title_qid, "target_qid": qid, "kind": "credit", "role": "cast", "property": audit.CAST_PROPERTY})

        stats["genre_relations"] += len(genres)
        stats["director_relations"] += len(directors)
        stats["creator_relations"] += len(creators)
        stats["cast_relations"] += len(cast)

    return relations, genre_qids, people_qids, stats


def materialize(
    candidates: list[Mapping[str, Any]],
    entities: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, str],
) -> dict[str, Any]:
    relations, genre_qids, people_qids, stats = collect_relations(candidates, entities)

    title_rows = [
        {
            "id": f"wikidata:{str(row['wikidata_qid']).upper()}",
            "wikidata_qid": str(row["wikidata_qid"]).upper(),
            "media_type": str(row["media_type"]),
            "display_title": str(row.get("display_title") or "").strip(),
            "source_table": str(row["source_table"]),
            "source_id": str(row["source_id"]),
            "source_url": str(row["source_url"]),
        }
        for row in candidates
    ]

    genre_rows = [
        {"id": f"wikidata:{qid}", "wikidata_qid": qid, "name": labels[qid], "source_url": entity_url(qid)}
        for qid in sorted(genre_qids, key=audit.qid_number)
        if labels.get(qid)
    ]
    people_rows = [
        {"id": f"wikidata:{qid}", "wikidata_qid": qid, "name": labels[qid], "source_url": entity_url(qid)}
        for qid in sorted(people_qids, key=audit.qid_number)
        if labels.get(qid)
    ]

    resolved_genres = {row["wikidata_qid"] for row in genre_rows}
    resolved_people = {row["wikidata_qid"] for row in people_rows}
    genre_relations: list[dict[str, Any]] = []
    credit_relations: list[dict[str, Any]] = []
    missing_label_relations = 0
    for relation in relations:
        target = relation["target_qid"]
        if relation["kind"] == "genre":
            if target not in resolved_genres:
                missing_label_relations += 1
                continue
            genre_relations.append({
                "title_id": f"wikidata:{relation['title_qid']}",
                "genre_id": f"wikidata:{target}",
                "source_property": relation["property"],
                "source_url": entity_url(relation["title_qid"]),
            })
        else:
            if target not in resolved_people:
                missing_label_relations += 1
                continue
            credit_relations.append({
                "title_id": f"wikidata:{relation['title_qid']}",
                "person_id": f"wikidata:{target}",
                "role": relation["role"],
                "source_property": relation["property"],
                "source_url": entity_url(relation["title_qid"]),
            })

    return {
        "title_rows": title_rows,
        "genre_rows": genre_rows,
        "people_rows": people_rows,
        "title_genre_rows": genre_relations,
        "title_credit_rows": credit_relations,
        "stats": {
            **stats,
            "candidate_titles": len(candidates),
            "unique_genre_qids": len(genre_qids),
            "resolved_genres": len(genre_rows),
            "unique_people_qids": len(people_qids),
            "resolved_people": len(people_rows),
            "missing_label_entities": len((genre_qids | people_qids) - set(labels)),
            "skipped_relations_missing_label": missing_label_relations,
            "emitted_genre_relations": len(genre_relations),
            "emitted_credit_relations": len(credit_relations),
        },
    }


def render_sql(materialized: Mapping[str, Any]) -> str:
    lines = [
        "-- Recommendation Metadata Foundation V1 generated dry-run SQL.",
        "-- Apply only through the separately guarded production workflow.",
        "PRAGMA foreign_keys = ON;",
        "BEGIN;",
    ]

    for row in materialized["title_rows"]:
        lines.append(
            "INSERT INTO recommendation_titles (id,wikidata_qid,media_type,display_title,source_table,source_id,source_url) VALUES "
            f"({sql_quote(row['id'])},{sql_quote(row['wikidata_qid'])},{sql_quote(row['media_type'])},{sql_quote(row['display_title'])},{sql_quote(row['source_table'])},{sql_quote(row['source_id'])},{sql_quote(row['source_url'])}) "
            "ON CONFLICT(wikidata_qid) DO UPDATE SET "
            "display_title=excluded.display_title,source_table=excluded.source_table,source_id=excluded.source_id,source_url=excluded.source_url,updated_at=CURRENT_TIMESTAMP "
            "WHERE recommendation_titles.media_type=excluded.media_type;"
        )

    for row in materialized["genre_rows"]:
        lines.append(
            "INSERT INTO genres (id,wikidata_qid,name,source_url) VALUES "
            f"({sql_quote(row['id'])},{sql_quote(row['wikidata_qid'])},{sql_quote(row['name'])},{sql_quote(row['source_url'])}) "
            "ON CONFLICT(wikidata_qid) DO UPDATE SET name=excluded.name,source_url=excluded.source_url,updated_at=CURRENT_TIMESTAMP;"
        )

    for row in materialized["people_rows"]:
        lines.append(
            "INSERT INTO people (id,wikidata_qid,name,source_url) VALUES "
            f"({sql_quote(row['id'])},{sql_quote(row['wikidata_qid'])},{sql_quote(row['name'])},{sql_quote(row['source_url'])}) "
            "ON CONFLICT(wikidata_qid) DO UPDATE SET name=excluded.name,source_url=excluded.source_url,updated_at=CURRENT_TIMESTAMP;"
        )

    for row in materialized["title_genre_rows"]:
        lines.append(
            "INSERT OR IGNORE INTO title_genres (title_id,genre_id,source_property,source_url) VALUES "
            f"({sql_quote(row['title_id'])},{sql_quote(row['genre_id'])},{sql_quote(row['source_property'])},{sql_quote(row['source_url'])});"
        )

    for row in materialized["title_credit_rows"]:
        lines.append(
            "INSERT OR IGNORE INTO title_credits (title_id,person_id,role,source_property,source_url) VALUES "
            f"({sql_quote(row['title_id'])},{sql_quote(row['person_id'])},{sql_quote(row['role'])},{sql_quote(row['source_property'])},{sql_quote(row['source_url'])});"
        )

    lines.append("COMMIT;")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-titles", type=int, default=2000)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-sql", required=True)
    args = parser.parse_args()

    projection = audit.build_catalogue_projection(
        audit.load_d1_rows(args.movies),
        audit.load_d1_rows(args.catalogue),
        audit.load_d1_rows(args.series),
    )
    if projection["cross_type_collision_qids"]:
        raise SystemExit("cross-type identity collisions must be resolved before materialization")

    candidates = audit.shard_candidates(
        projection["candidates"], shard_index=args.shard_index, shard_count=args.shard_count
    )
    if len(candidates) > args.max_titles:
        raise SystemExit(f"shard contains {len(candidates)} candidates, above safety cap {args.max_titles}")

    title_entities = audit.fetch_claim_entities([row["wikidata_qid"] for row in candidates])
    relations, genre_qids, people_qids, _ = collect_relations(candidates, title_entities)
    related_qids = sorted(genre_qids | people_qids, key=audit.qid_number)
    labels = fetch_entity_labels(related_qids)
    result = materialize(candidates, title_entities, labels)
    result["schema_version"] = "recommendation-metadata-foundation-v1-materialization"
    result["production_mutation"] = False
    result["shard_index"] = args.shard_index
    result["shard_count"] = args.shard_count
    result["projection"] = {
        key: value for key, value in projection.items() if key != "candidates"
    }
    result["raw_relation_count"] = len(relations)

    Path(args.out_json).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.out_sql).write_text(render_sql(result), encoding="utf-8")
    print(json.dumps({
        "candidate_titles": result["stats"]["candidate_titles"],
        "resolved_genres": result["stats"]["resolved_genres"],
        "resolved_people": result["stats"]["resolved_people"],
        "emitted_genre_relations": result["stats"]["emitted_genre_relations"],
        "emitted_credit_relations": result["stats"]["emitted_credit_relations"],
        "skipped_relations_missing_label": result["stats"]["skipped_relations_missing_label"],
        "production_mutation": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
