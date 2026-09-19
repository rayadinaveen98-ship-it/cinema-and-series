#!/usr/bin/env python3
"""Verify normalized P1 production data against the reviewed V3 graph.

Counts alone cannot prove that production contains the exact reviewed metadata.
This verifier loads D1 JSON snapshots, strips database-only timestamps by
selecting the reviewed fields explicitly, canonicalizes each normalized table,
and requires the complete graph SHA-256 to equal the V3 artifact attestation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import recommendation_metadata_audit as audit
    import repartition_recommendation_materialization as repartition
except ModuleNotFoundError:
    from scripts import recommendation_metadata_audit as audit
    from scripts import repartition_recommendation_materialization as repartition

TITLE_FIELDS = ("id", "wikidata_qid", "media_type", "display_title", "source_table", "source_id", "source_url")
GENRE_FIELDS = ("id", "wikidata_qid", "name", "source_url")
PEOPLE_FIELDS = ("id", "wikidata_qid", "name", "source_url")
TITLE_GENRE_FIELDS = ("title_id", "genre_id", "source_property", "source_url")
TITLE_CREDIT_FIELDS = ("title_id", "person_id", "role", "source_property", "source_url")


def project_fields(rows: Iterable[Mapping[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [{field: row.get(field) for field in fields} for row in rows]


def canonical_production_graph(
    titles: list[Mapping[str, Any]],
    genres: list[Mapping[str, Any]],
    people: list[Mapping[str, Any]],
    title_genres: list[Mapping[str, Any]],
    title_credits: list[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    graph = {
        "title_rows": repartition.dedupe_rows(project_fields(titles, TITLE_FIELDS), ("id",)),
        "genre_rows": repartition.dedupe_rows(project_fields(genres, GENRE_FIELDS), ("id",)),
        "people_rows": repartition.dedupe_rows(project_fields(people, PEOPLE_FIELDS), ("id",)),
        "title_genre_rows": repartition.dedupe_rows(
            project_fields(title_genres, TITLE_GENRE_FIELDS),
            ("title_id", "genre_id", "source_property", "source_url"),
        ),
        "title_credit_rows": repartition.dedupe_rows(
            project_fields(title_credits, TITLE_CREDIT_FIELDS),
            ("title_id", "person_id", "role", "source_property", "source_url"),
        ),
    }
    return graph


def verify_graph(graph: Mapping[str, list[dict[str, Any]]], attestation: Mapping[str, Any]) -> dict[str, Any]:
    expected_graph_sha = str(attestation.get("global_materialization_sha256") or "")
    actual_graph_sha = repartition.materialization_fingerprint(graph)
    if actual_graph_sha != expected_graph_sha:
        raise ValueError(
            f"production materialization graph mismatch: expected={expected_graph_sha} actual={actual_graph_sha}"
        )

    totals = attestation.get("totals") or {}
    expected_counts = {
        "candidate_titles": int(totals.get("candidate_titles") or 0),
        "genres": int(totals.get("genres") or 0),
        "people": int(totals.get("people") or 0),
        "emitted_genre_relations": int(totals.get("emitted_genre_relations") or 0),
        "emitted_credit_relations": int(totals.get("emitted_credit_relations") or 0),
    }
    actual_counts = {
        "candidate_titles": len(graph["title_rows"]),
        "genres": len(graph["genre_rows"]),
        "people": len(graph["people_rows"]),
        "emitted_genre_relations": len(graph["title_genre_rows"]),
        "emitted_credit_relations": len(graph["title_credit_rows"]),
    }
    if actual_counts != expected_counts:
        raise ValueError(f"production normalized counts mismatch: expected={expected_counts} actual={actual_counts}")

    title_ids = {row["id"] for row in graph["title_rows"]}
    genre_ids = {row["id"] for row in graph["genre_rows"]}
    people_ids = {row["id"] for row in graph["people_rows"]}
    orphan_genres = [
        row for row in graph["title_genre_rows"]
        if row["title_id"] not in title_ids or row["genre_id"] not in genre_ids
    ]
    orphan_credits = [
        row for row in graph["title_credit_rows"]
        if row["title_id"] not in title_ids or row["person_id"] not in people_ids
    ]
    if orphan_genres or orphan_credits:
        raise ValueError(
            f"production contains orphan relationships: genres={len(orphan_genres)} credits={len(orphan_credits)}"
        )

    invalid_genre_provenance = [row for row in graph["title_genre_rows"] if row["source_property"] != "P136"]
    allowed_credit_properties = {"director": "P57", "creator": "P170", "cast": "P161"}
    invalid_credit_provenance = [
        row for row in graph["title_credit_rows"]
        if allowed_credit_properties.get(str(row["role"])) != row["source_property"]
    ]
    if invalid_genre_provenance or invalid_credit_provenance:
        raise ValueError(
            "production contains invalid recommendation provenance: "
            f"genre={len(invalid_genre_provenance)} credit={len(invalid_credit_provenance)}"
        )

    if any(row.get("media_type") not in {"movie", "series"} for row in graph["title_rows"]):
        raise ValueError("production contains invalid recommendation media type")
    if any(not audit.valid_qid(row.get("wikidata_qid")) for row in graph["title_rows"]):
        raise ValueError("production contains invalid recommendation title QID")

    return {
        "state": "verified",
        "production_mutation": False,
        "global_materialization_sha256": actual_graph_sha,
        "counts": actual_counts,
        "orphan_genre_relations": 0,
        "orphan_credit_relations": 0,
        "invalid_genre_provenance": 0,
        "invalid_credit_provenance": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", required=True)
    parser.add_argument("--genres", required=True)
    parser.add_argument("--people", required=True)
    parser.add_argument("--title-genres", required=True)
    parser.add_argument("--title-credits", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    graph = canonical_production_graph(
        audit.load_d1_rows(args.titles),
        audit.load_d1_rows(args.genres),
        audit.load_d1_rows(args.people),
        audit.load_d1_rows(args.title_genres),
        audit.load_d1_rows(args.title_credits),
    )
    attestation = json.loads(Path(args.attestation).read_text(encoding="utf-8"))
    result = verify_graph(graph, attestation)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P1_V3_PRODUCTION_GRAPH_VERIFIED=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
