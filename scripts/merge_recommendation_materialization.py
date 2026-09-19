#!/usr/bin/env python3
"""Merge an immutable reviewed P1 materialization with a reviewed projection delta.

The merge is title-identity exact: unchanged parent titles are inherited,
reviewed exclusions are removed, newly added titles come only from delta
materialization, and every output shard must exactly partition the current
projection manifest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import enrich_recommendation_metadata as enrich
    import recommendation_metadata_audit as audit
    import recommendation_delta_materialization as delta_module
except ModuleNotFoundError:
    from scripts import enrich_recommendation_metadata as enrich
    from scripts import recommendation_metadata_audit as audit
    from scripts import recommendation_delta_materialization as delta_module


def dedupe_rows(rows: Iterable[Mapping[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(str(row.get(field) or "") for field in key_fields)
        by_key[key] = dict(row)
    return [by_key[key] for key in sorted(by_key)]


def merge_shard(
    parent: dict[str, Any],
    delta: dict[str, Any],
    *,
    removed_qids: set[str],
    expected_entries: list[Mapping[str, Any]],
    current_manifest: Mapping[str, Any],
    parent_manifest: Mapping[str, Any],
    shard_index: int,
    shard_count: int,
) -> dict[str, Any]:
    removed_title_ids = {f"wikidata:{qid}" for qid in removed_qids}

    parent_titles = [
        row for row in parent.get("title_rows", [])
        if str(row.get("wikidata_qid") or "") not in removed_qids
    ]
    parent_genres = [
        row for row in parent.get("title_genre_rows", [])
        if str(row.get("title_id") or "") not in removed_title_ids
    ]
    parent_credits = [
        row for row in parent.get("title_credit_rows", [])
        if str(row.get("title_id") or "") not in removed_title_ids
    ]

    title_rows = dedupe_rows(
        [*parent_titles, *delta.get("title_rows", [])],
        ("id",),
    )
    title_genre_rows = dedupe_rows(
        [*parent_genres, *delta.get("title_genre_rows", [])],
        ("title_id", "genre_id", "source_property", "source_url"),
    )
    title_credit_rows = dedupe_rows(
        [*parent_credits, *delta.get("title_credit_rows", [])],
        ("title_id", "person_id", "role", "source_property", "source_url"),
    )

    referenced_genres = {str(row["genre_id"]) for row in title_genre_rows}
    referenced_people = {str(row["person_id"]) for row in title_credit_rows}
    genre_rows = [
        row for row in dedupe_rows(
            [*parent.get("genre_rows", []), *delta.get("genre_rows", [])],
            ("id",),
        )
        if str(row.get("id") or "") in referenced_genres
    ]
    people_rows = [
        row for row in dedupe_rows(
            [*parent.get("people_rows", []), *delta.get("people_rows", [])],
            ("id",),
        )
        if str(row.get("id") or "") in referenced_people
    ]

    expected_qids = {str(row["wikidata_qid"]) for row in expected_entries}
    actual_qids = {str(row["wikidata_qid"]) for row in title_rows}
    if actual_qids != expected_qids:
        missing = sorted(expected_qids - actual_qids, key=audit.qid_number)
        extra = sorted(actual_qids - expected_qids, key=audit.qid_number)
        raise ValueError(
            f"shard {shard_index} title partition mismatch; missing={missing[:20]} extra={extra[:20]}"
        )
    if len(title_rows) != len(actual_qids):
        raise ValueError(f"shard {shard_index} contains duplicate title identities")

    valid_title_ids = {str(row["id"]) for row in title_rows}
    if any(str(row["title_id"]) not in valid_title_ids for row in title_genre_rows):
        raise ValueError(f"shard {shard_index} contains orphan title-genre rows")
    if any(str(row["title_id"]) not in valid_title_ids for row in title_credit_rows):
        raise ValueError(f"shard {shard_index} contains orphan title-credit rows")
    if {str(row["id"]) for row in genre_rows} != referenced_genres:
        raise ValueError(f"shard {shard_index} genre entity closure mismatch")
    if {str(row["id"]) for row in people_rows} != referenced_people:
        raise ValueError(f"shard {shard_index} people entity closure mismatch")

    delta_stats = delta.get("stats") or {}
    parent_stats = parent.get("stats") or {}
    result = {
        "schema_version": "recommendation-metadata-materialization-v2-rebaseline",
        "production_mutation": False,
        "shard_index": shard_index,
        "shard_count": shard_count,
        "title_rows": title_rows,
        "genre_rows": genre_rows,
        "people_rows": people_rows,
        "title_genre_rows": title_genre_rows,
        "title_credit_rows": title_credit_rows,
        "stats": {
            "candidate_titles": len(title_rows),
            "resolved_genres": len(genre_rows),
            "resolved_people": len(people_rows),
            "emitted_genre_relations": len(title_genre_rows),
            "emitted_credit_relations": len(title_credit_rows),
            "missing_title_entities": int(parent_stats.get("missing_title_entities") or 0)
            + int(delta_stats.get("missing_title_entities") or 0),
            "delta_unusable_claims": int(delta_stats.get("unusable_claims") or 0),
            "delta_skipped_relations_missing_label": int(
                delta_stats.get("skipped_relations_missing_label") or 0
            ),
        },
        "projection_manifest": {
            "schema_version": current_manifest["schema_version"],
            "candidate_count": current_manifest["candidate_count"],
            "movie_qid_count": current_manifest["movie_qid_count"],
            "series_qid_count": current_manifest["series_qid_count"],
            "sha256": current_manifest["sha256"],
        },
        "lineage": {
            "parent_projection_sha256": parent_manifest["sha256"],
            "current_projection_sha256": current_manifest["sha256"],
            "removed_qids": sorted(removed_qids, key=audit.qid_number),
            "inherited_parent_titles": len(parent_titles),
            "delta_titles": len(delta.get("title_rows", [])),
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-dir", required=True)
    parser.add_argument("--delta-dir", required=True)
    parser.add_argument("--current-manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--shard-count", type=int, default=8)
    args = parser.parse_args()

    parent_dir = Path(args.parent_dir)
    delta_dir = Path(args.delta_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    parent_manifest = delta_module.load_manifest(parent_dir / "recommendation-projection-manifest.json")
    current_manifest = delta_module.load_manifest(args.current_manifest)
    projection_delta = delta_module.manifest_delta(parent_manifest, current_manifest)
    removed = set(projection_delta["removed_qids"])

    all_titles: set[str] = set()
    total_genres = 0
    total_credits = 0
    shard_summaries: list[dict[str, Any]] = []

    for shard in range(args.shard_count):
        parent = json.loads(
            (parent_dir / f"recommendation-materialization-shard-{shard}.json").read_text(encoding="utf-8")
        )
        delta = json.loads(
            (delta_dir / f"recommendation-delta-shard-{shard}.json").read_text(encoding="utf-8")
        )
        expected_entries = [
            row for row in current_manifest["entries"]
            if audit.qid_number(row["wikidata_qid"]) % args.shard_count == shard
        ]
        removed_for_shard = {
            qid for qid in removed if audit.qid_number(qid) % args.shard_count == shard
        }
        merged = merge_shard(
            parent,
            delta,
            removed_qids=removed_for_shard,
            expected_entries=expected_entries,
            current_manifest=current_manifest,
            parent_manifest=parent_manifest,
            shard_index=shard,
            shard_count=args.shard_count,
        )
        for row in merged["title_rows"]:
            qid = str(row["wikidata_qid"])
            if qid in all_titles:
                raise SystemExit(f"title {qid} appears in more than one merged shard")
            all_titles.add(qid)
        total_genres += len(merged["title_genre_rows"])
        total_credits += len(merged["title_credit_rows"])

        report_path = out_dir / f"recommendation-materialization-shard-{shard}.json"
        sql_path = out_dir / f"recommendation-materialization-shard-{shard}.sql"
        report_path.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        sql = enrich.render_sql(merged)
        sql_path.write_text(
            f"-- Projection manifest SHA-256: {current_manifest['sha256']}\n"
            f"-- Projection candidate count: {current_manifest['candidate_count']}\n"
            f"-- Rebaseline parent SHA-256: {parent_manifest['sha256']}\n"
            + sql,
            encoding="utf-8",
        )
        shard_summaries.append(
            {
                "shard": shard,
                "titles": len(merged["title_rows"]),
                "genre_relations": len(merged["title_genre_rows"]),
                "credit_relations": len(merged["title_credit_rows"]),
                "inherited_parent_titles": merged["lineage"]["inherited_parent_titles"],
                "delta_titles": merged["lineage"]["delta_titles"],
            }
        )

    expected_all = {str(row["wikidata_qid"]) for row in current_manifest["entries"]}
    if all_titles != expected_all:
        raise SystemExit("merged shards do not exactly cover the current projection")

    summary = {
        "schema_version": "recommendation-metadata-materialization-v2-rebaseline-summary",
        "state": "complete",
        "production_mutation": False,
        "projection_manifest": {
            "schema_version": current_manifest["schema_version"],
            "candidate_count": current_manifest["candidate_count"],
            "movie_qid_count": current_manifest["movie_qid_count"],
            "series_qid_count": current_manifest["series_qid_count"],
            "sha256": current_manifest["sha256"],
        },
        "lineage": {
            "parent_projection_sha256": parent_manifest["sha256"],
            "unchanged_count": projection_delta["unchanged_count"],
            "added_count": projection_delta["added_count"],
            "removed_count": projection_delta["removed_count"],
            "removed_qids": projection_delta["removed_qids"],
        },
        "totals": {
            "candidate_titles": len(all_titles),
            "emitted_genre_relations": total_genres,
            "emitted_credit_relations": total_credits,
        },
        "shards": shard_summaries,
    }
    (out_dir / "recommendation-metadata-materialization-v2-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "recommendation-projection-manifest.json").write_text(
        json.dumps(current_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("P1_REBASELINE_SUMMARY=" + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
