#!/usr/bin/env python3
"""Build a deterministic Recommendation Metadata P1 catalogue projection manifest.

The manifest fingerprints the exact QID-backed recommendation projection used by
analysis. A guarded production write can recapture the catalogue and require an
identical fingerprint before applying analyzed SQL, preventing same-count source
or identity drift from being silently accepted.

Reviewed media-identity corrections are applied before canonical projection.
They are explicit, provenance-backed decisions, not title/category inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

try:
    import recommendation_metadata_audit as audit
    import media_identity_corrections as identity
except ModuleNotFoundError:
    from scripts import recommendation_metadata_audit as audit
    from scripts import media_identity_corrections as identity

MANIFEST_FIELDS = (
    "wikidata_qid",
    "media_type",
    "display_title",
    "source_table",
    "source_id",
    "source_url",
)


def canonical_entries(candidates: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    entries = []
    for row in candidates:
        entries.append({field: str(row.get(field) or "") for field in MANIFEST_FIELDS})
    entries.sort(key=lambda row: (audit.qid_number(row["wikidata_qid"]), row["media_type"]))
    return entries


def fingerprint(entries: list[Mapping[str, Any]]) -> str:
    canonical = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(
    exact_movies: list[Mapping[str, Any]],
    catalogue_movies: list[Mapping[str, Any]],
    series_rows: list[Mapping[str, Any]],
) -> dict[str, Any]:
    corrections = identity.load_registry()
    exact_movies_filtered, exact_suppressed = identity.filter_rows(exact_movies, "movie", corrections=corrections)
    catalogue_filtered, catalogue_suppressed = identity.filter_rows(catalogue_movies, "movie", corrections=corrections)
    series_filtered, series_suppressed = identity.filter_rows(series_rows, "series", corrections=corrections)

    projection = audit.build_catalogue_projection(
        exact_movies_filtered,
        catalogue_filtered,
        series_filtered,
    )
    collisions = projection["cross_type_collision_qids"]
    if collisions:
        raise ValueError(f"cross-type Wikidata identity collision detected: {collisions[:20]}")
    entries = canonical_entries(projection["candidates"])
    suppressed = sorted(
        set(exact_suppressed) | set(catalogue_suppressed) | set(series_suppressed),
        key=audit.qid_number,
    )
    return {
        "schema_version": "recommendation-projection-manifest-v2",
        "candidate_count": len(entries),
        "movie_qid_count": projection["movie_qid_count"],
        "series_qid_count": projection["series_qid_count"],
        "suppressed_catalogue_overlap_count": projection["suppressed_catalogue_overlap_count"],
        "suppressed_media_identity_correction_count": len(suppressed),
        "suppressed_media_identity_correction_qids": suppressed,
        "cross_type_collision_count": 0,
        "sha256": fingerprint(entries),
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True)
    parser.add_argument("--catalogue", required=True)
    parser.add_argument("--series", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    manifest = build_manifest(
        audit.load_d1_rows(args.movies),
        audit.load_d1_rows(args.catalogue),
        audit.load_d1_rows(args.series),
    )
    Path(args.out_json).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("RECOMMENDATION_PROJECTION_MANIFEST=" + json.dumps({
        "candidate_count": manifest["candidate_count"],
        "movie_qid_count": manifest["movie_qid_count"],
        "series_qid_count": manifest["series_qid_count"],
        "suppressed_media_identity_correction_count": manifest["suppressed_media_identity_correction_count"],
        "sha256": manifest["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
