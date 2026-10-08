#!/usr/bin/env python3
"""Normalize read-only production D1 artwork evidence into the locked P2 audit inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.build_p2_artwork_audit_snapshot import build_snapshot, render_snapshot
from scripts import p2_artwork_coverage_audit as audit


def rows_from_wrangle_payload(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    def find_rows(value: Any) -> list[dict[str, Any]] | None:
        if isinstance(value, dict):
            results = value.get("results")
            if isinstance(results, list) and all(isinstance(row, dict) for row in results):
                return results
            for child in value.values():
                found = find_rows(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_rows(child)
                if found is not None:
                    return found
        return None

    rows = find_rows(payload)
    if rows is None:
        raise ValueError(f"unable to find D1 results rows in {path}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--movies", required=True, type=Path)
    parser.add_argument("--series", required=True, type=Path)
    parser.add_argument("--territory", required=True)
    parser.add_argument("--evaluated-at", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    movies = rows_from_wrangle_payload(args.movies)
    series = rows_from_wrangle_payload(args.series)

    titles: list[dict[str, Any]] = [
        {
            "media_type": "movie",
            "source_table": "movies",
            "source_id": str(row["id"]),
            "language": row.get("language_name") or "unknown",
        }
        for row in movies
    ]
    titles.extend(
        {
            "media_type": "series",
            "source_table": "series_titles",
            "source_id": str(row["id"]),
            "language": row.get("language_name") or "unknown",
        }
        for row in series
    )

    candidates: list[dict[str, Any]] = []
    for row in movies:
        source_key = (row.get("artwork_source") or "legacy_movie_artwork").strip() or "legacy_movie_artwork"
        source_page_url = (row.get("artwork_source_url") or "").strip() or None
        for role, field in (("poster", "poster_url"), ("backdrop", "backdrop_url")):
            delivery_url = (row.get(field) or "").strip()
            if not delivery_url:
                continue
            candidates.append(
                {
                    "media_type": "movie",
                    "source_table": "movies",
                    "source_id": str(row["id"]),
                    "source_key": source_key,
                    "source_asset_id": f"legacy:{row['id']}:{role}",
                    "source_page_url": source_page_url,
                    "delivery_url": delivery_url,
                    "presentation_role": role,
                    "publication_state": "DISCOVERED",
                    "rights_basis": "NO_RIGHTS_BASIS",
                    "hosting_mode": "REFERENCE_ONLY",
                    "link_exact": True,
                    "ambiguous_link": False,
                    "validity_eligible": True,
                    "takedown_clear": True,
                    "territory_eligible": True,
                    "attribution_required": False,
                }
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    titles_path = args.output_dir / "titles.json"
    candidates_path = args.output_dir / "candidates.json"
    snapshot_path = args.output_dir / "p2-artwork-audit-snapshot.json"
    report_path = args.output_dir / "p2-artwork-coverage-report.json"

    titles_path.write_text(
        json.dumps({"titles": titles}, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    candidates_path.write_text(
        json.dumps({"candidates": candidates}, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    snapshot = build_snapshot(
        titles,
        candidates,
        territory=args.territory,
        evaluated_at=args.evaluated_at,
    )
    snapshot_path.write_text(render_snapshot(snapshot), encoding="utf-8")
    report = audit.build_report(snapshot)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "titles": len(titles),
                "movies": len(movies),
                "series": len(series),
                "candidates": len(candidates),
                "territory": args.territory,
                "evaluated_at": args.evaluated_at,
                "input_sha256": report["input_attestation"]["sha256"],
                "publishable_candidates": report["candidates"]["publishable_image_candidates"],
                "fallback_only": report["coverage"]["fallback_only"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
