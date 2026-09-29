#!/usr/bin/env python3
"""Build the final machine-readable P1 completion attestation.

This script is read-only. It consumes evidence already produced by the V3 final
verification path and fails closed unless every locked completion condition is
proven: corrected projection, exact normalized graph, zero recommendation
integrity violations, exact reviewed source-cleanup state, and Catalogue
Quality V1 S0=0/S1=0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "p1-completion-attestation-v1"
CANONICAL_SERIES_ID = "series-wd-Q3146368"
CANONICAL_SERIES_QID = "Q3146368"


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_d1_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    rows: list[dict[str, Any]] = []
    for batch in payload if isinstance(payload, list) else [payload]:
        if isinstance(batch, Mapping):
            rows.extend(dict(row) for row in (batch.get("results") or []))
    return rows


def load_d1_single_row(path: str | Path) -> dict[str, Any]:
    rows = load_d1_rows(path)
    if len(rows) != 1:
        raise ValueError(f"expected exactly one D1 row in {path}, got {len(rows)}")
    return rows[0]


def int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected integer-compatible value, got {value!r}") from exc


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_completion_attestation(
    *,
    reviewed_attestation: Mapping[str, Any],
    reviewed_attestation_sha256: str,
    projection_manifest: Mapping[str, Any],
    graph_verification: Mapping[str, Any],
    integrity: Mapping[str, Any],
    catalogue_quality: Mapping[str, Any],
    source_movies: list[Mapping[str, Any]],
    source_catalogue: list[Mapping[str, Any]],
    source_series: list[Mapping[str, Any]],
    expected_attestation_sha256: str,
    expected_projection_sha256: str,
    expected_graph_sha256: str,
    expected_candidates: int,
    expected_movies: int,
    expected_series: int,
    expected_genres: int,
    expected_people: int,
    expected_genre_relations: int,
    expected_credit_relations: int,
) -> dict[str, Any]:
    if reviewed_attestation_sha256 != expected_attestation_sha256:
        raise ValueError(
            "reviewed artifact attestation SHA mismatch: "
            f"expected={expected_attestation_sha256} actual={reviewed_attestation_sha256}"
        )

    if reviewed_attestation.get("projection_sha256") != expected_projection_sha256:
        raise ValueError("reviewed attestation projection SHA mismatch")
    if reviewed_attestation.get("global_materialization_sha256") != expected_graph_sha256:
        raise ValueError("reviewed attestation graph SHA mismatch")
    if int_value(reviewed_attestation.get("candidate_count")) != expected_candidates:
        raise ValueError("reviewed attestation candidate count mismatch")

    reviewed_totals = reviewed_attestation.get("totals") or {}
    expected_graph_counts = {
        "candidate_titles": expected_candidates,
        "genres": expected_genres,
        "people": expected_people,
        "emitted_genre_relations": expected_genre_relations,
        "emitted_credit_relations": expected_credit_relations,
    }
    actual_reviewed_counts = {key: int_value(reviewed_totals.get(key)) for key in expected_graph_counts}
    if actual_reviewed_counts != expected_graph_counts:
        raise ValueError(
            f"reviewed attestation graph counts mismatch: expected={expected_graph_counts} actual={actual_reviewed_counts}"
        )

    projection = {
        "sha256": str(projection_manifest.get("sha256") or ""),
        "candidate_count": int_value(projection_manifest.get("candidate_count")),
        "movie_qid_count": int_value(projection_manifest.get("movie_qid_count")),
        "series_qid_count": int_value(projection_manifest.get("series_qid_count")),
        "cross_type_collision_count": int_value(projection_manifest.get("cross_type_collision_count")),
    }
    expected_projection = {
        "sha256": expected_projection_sha256,
        "candidate_count": expected_candidates,
        "movie_qid_count": expected_movies,
        "series_qid_count": expected_series,
        "cross_type_collision_count": 0,
    }
    if projection != expected_projection:
        raise ValueError(f"production projection mismatch: expected={expected_projection} actual={projection}")

    if graph_verification.get("state") != "verified":
        raise ValueError("final graph verification is not verified")
    if bool(graph_verification.get("production_mutation")):
        raise ValueError("final graph verification unexpectedly reports production mutation")
    if graph_verification.get("global_materialization_sha256") != expected_graph_sha256:
        raise ValueError("final graph verification SHA mismatch")
    graph_counts = graph_verification.get("counts") or {}
    actual_graph_counts = {key: int_value(graph_counts.get(key)) for key in expected_graph_counts}
    if actual_graph_counts != expected_graph_counts:
        raise ValueError(f"final graph counts mismatch: expected={expected_graph_counts} actual={actual_graph_counts}")

    graph_health_keys = (
        "orphan_genre_relations",
        "orphan_credit_relations",
        "invalid_genre_provenance",
        "invalid_credit_provenance",
    )
    graph_health = {key: int_value(graph_verification.get(key)) for key in graph_health_keys}
    if any(graph_health.values()):
        raise ValueError(f"final graph verification health is not clean: {graph_health}")

    integrity_keys = (
        "orphan_genres",
        "orphan_credits",
        "invalid_genre_provenance",
        "invalid_credit_provenance",
    )
    integrity_summary = {key: int_value(integrity.get(key)) for key in integrity_keys}
    if any(integrity_summary.values()):
        raise ValueError(f"production recommendation integrity is not clean: {integrity_summary}")

    severity = (catalogue_quality.get("finding_summary") or {}).get("by_severity") or {}
    quality_summary = {"S0": int_value(severity.get("S0")), "S1": int_value(severity.get("S1"))}
    if any(quality_summary.values()):
        raise ValueError(f"Catalogue Quality V1 is not clean: {quality_summary}")

    if source_movies or source_catalogue:
        raise ValueError(
            f"reviewed source cleanup is incomplete: movies={list(source_movies)} catalogue={list(source_catalogue)}"
        )
    series_pairs = {
        (str(row.get("id") or ""), str(row.get("wikidata_qid") or ""))
        for row in source_series
    }
    expected_series_pairs = {(CANONICAL_SERIES_ID, CANONICAL_SERIES_QID)}
    if series_pairs != expected_series_pairs:
        raise ValueError(f"reviewed source cleanup canonical Series state mismatch: {sorted(series_pairs)}")

    core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "state": "verified",
        "p1_completion_eligible": True,
        "production_mutation": False,
        "reviewed_materialization": {
            "artifact_attestation_sha256": reviewed_attestation_sha256,
            "projection_sha256": expected_projection_sha256,
            "global_materialization_sha256": expected_graph_sha256,
        },
        "production_projection": projection,
        "production_graph": {
            "global_materialization_sha256": expected_graph_sha256,
            "counts": {
                "recommendation_titles": expected_candidates,
                "genres": expected_genres,
                "people": expected_people,
                "title_genres": expected_genre_relations,
                "title_credits": expected_credit_relations,
            },
            "health": graph_health,
        },
        "production_integrity": integrity_summary,
        "catalogue_quality": quality_summary,
        "source_cleanup": {
            "state": "complete",
            "canonical_series_identity": {
                "id": CANONICAL_SERIES_ID,
                "wikidata_qid": CANONICAL_SERIES_QID,
            },
        },
    }
    return {**core, "evidence_sha256": canonical_sha256(core)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--projection-manifest", required=True)
    parser.add_argument("--graph-verification", required=True)
    parser.add_argument("--integrity-json", required=True)
    parser.add_argument("--catalogue-quality", required=True)
    parser.add_argument("--source-movies", required=True)
    parser.add_argument("--source-catalogue", required=True)
    parser.add_argument("--source-series", required=True)
    parser.add_argument("--expected-attestation-sha256", required=True)
    parser.add_argument("--expected-projection-sha256", required=True)
    parser.add_argument("--expected-graph-sha256", required=True)
    parser.add_argument("--expected-candidates", required=True, type=int)
    parser.add_argument("--expected-movies", required=True, type=int)
    parser.add_argument("--expected-series", required=True, type=int)
    parser.add_argument("--expected-genres", required=True, type=int)
    parser.add_argument("--expected-people", required=True, type=int)
    parser.add_argument("--expected-genre-relations", required=True, type=int)
    parser.add_argument("--expected-credit-relations", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    attestation_path = Path(args.attestation)
    reviewed_attestation_sha256 = hashlib.sha256(attestation_path.read_bytes()).hexdigest()
    result = build_completion_attestation(
        reviewed_attestation=load_json(attestation_path),
        reviewed_attestation_sha256=reviewed_attestation_sha256,
        projection_manifest=load_json(args.projection_manifest),
        graph_verification=load_json(args.graph_verification),
        integrity=load_d1_single_row(args.integrity_json),
        catalogue_quality=load_json(args.catalogue_quality),
        source_movies=load_d1_rows(args.source_movies),
        source_catalogue=load_d1_rows(args.source_catalogue),
        source_series=load_d1_rows(args.source_series),
        expected_attestation_sha256=args.expected_attestation_sha256,
        expected_projection_sha256=args.expected_projection_sha256,
        expected_graph_sha256=args.expected_graph_sha256,
        expected_candidates=args.expected_candidates,
        expected_movies=args.expected_movies,
        expected_series=args.expected_series,
        expected_genres=args.expected_genres,
        expected_people=args.expected_people,
        expected_genre_relations=args.expected_genre_relations,
        expected_credit_relations=args.expected_credit_relations,
    )
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P1_COMPLETION_ATTESTATION_VERIFIED=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
