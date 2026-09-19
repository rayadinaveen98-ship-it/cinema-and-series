#!/usr/bin/env python3
"""Repartition a reviewed P1 parent+delta materialization into quota-safe shards.

The immutable parent evidence is partitioned by QID modulo 8 and the reviewed
projection delta is partitioned the same way. This helper first reconstructs the
current reviewed materialization globally, removes only provenance-backed
reviewed exclusions, then repartitions by a configurable physical shard count.

This lets production move from the original 8 logical shards to smaller physical
shards without re-querying Wikidata or weakening evidence lineage. In addition
to the title-projection fingerprint, V3 records deterministic SHA-256 hashes for
the complete normalized metadata graph and for every physical shard so a later
production writer can lock the exact reviewed relationships, not only titles.
"""
from __future__ import annotations

import argparse
import hashlib
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

MATERIALIZATION_KEYS = (
    "title_rows",
    "genre_rows",
    "people_rows",
    "title_genre_rows",
    "title_credit_rows",
)


def dedupe_rows(rows: Iterable[Mapping[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(str(row.get(field) or "") for field in key_fields)
        value = dict(row)
        existing = by_key.get(key)
        if existing is not None and existing != value:
            raise ValueError(f"conflicting duplicate row for key {key}")
        by_key[key] = value
    return [by_key[key] for key in sorted(by_key)]


def materialization_fingerprint(rows: Mapping[str, list[dict[str, Any]]]) -> str:
    """Hash the complete normalized graph in a deterministic JSON form."""
    canonical_rows = {key: rows.get(key) or [] for key in MATERIALIZATION_KEYS}
    canonical = json.dumps(
        canonical_rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_reviewed_rows(directory: Path, *, prefix: str, shard_count: int) -> dict[str, list[dict[str, Any]]]:
    buckets = {key: [] for key in MATERIALIZATION_KEYS}
    for shard in range(shard_count):
        payload = json.loads((directory / f"{prefix}-{shard}.json").read_text(encoding="utf-8"))
        if payload.get("production_mutation") is not False:
            raise ValueError(f"input shard {shard} is not read-only evidence")
        for key in buckets:
            buckets[key].extend(payload.get(key) or [])
    return buckets


def rebuild_global(
    parent_rows: Mapping[str, list[dict[str, Any]]],
    delta_rows: Mapping[str, list[dict[str, Any]]],
    *,
    removed_qids: set[str],
    current_manifest: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    removed_title_ids = {f"wikidata:{qid}" for qid in removed_qids}

    title_rows = dedupe_rows(
        [
            *[
                row for row in parent_rows["title_rows"]
                if str(row.get("wikidata_qid") or "") not in removed_qids
            ],
            *delta_rows["title_rows"],
        ],
        ("id",),
    )
    title_genre_rows = dedupe_rows(
        [
            *[
                row for row in parent_rows["title_genre_rows"]
                if str(row.get("title_id") or "") not in removed_title_ids
            ],
            *delta_rows["title_genre_rows"],
        ],
        ("title_id", "genre_id", "source_property", "source_url"),
    )
    title_credit_rows = dedupe_rows(
        [
            *[
                row for row in parent_rows["title_credit_rows"]
                if str(row.get("title_id") or "") not in removed_title_ids
            ],
            *delta_rows["title_credit_rows"],
        ],
        ("title_id", "person_id", "role", "source_property", "source_url"),
    )

    expected_qids = {str(row["wikidata_qid"]) for row in current_manifest["entries"]}
    actual_qids = {str(row["wikidata_qid"]) for row in title_rows}
    if actual_qids != expected_qids or len(title_rows) != len(actual_qids):
        missing = sorted(expected_qids - actual_qids, key=audit.qid_number)
        extra = sorted(actual_qids - expected_qids, key=audit.qid_number)
        raise ValueError(f"global title partition mismatch; missing={missing[:20]} extra={extra[:20]}")

    valid_title_ids = {str(row["id"]) for row in title_rows}
    if any(str(row["title_id"]) not in valid_title_ids for row in title_genre_rows):
        raise ValueError("global materialization contains orphan title-genre rows")
    if any(str(row["title_id"]) not in valid_title_ids for row in title_credit_rows):
        raise ValueError("global materialization contains orphan title-credit rows")

    all_genres = dedupe_rows([*parent_rows["genre_rows"], *delta_rows["genre_rows"]], ("id",))
    all_people = dedupe_rows([*parent_rows["people_rows"], *delta_rows["people_rows"]], ("id",))
    genre_by_id = {str(row["id"]): row for row in all_genres}
    people_by_id = {str(row["id"]): row for row in all_people}
    referenced_genres = {str(row["genre_id"]) for row in title_genre_rows}
    referenced_people = {str(row["person_id"]) for row in title_credit_rows}
    missing_genres = sorted(referenced_genres - set(genre_by_id))
    missing_people = sorted(referenced_people - set(people_by_id))
    if missing_genres or missing_people:
        raise ValueError(
            f"global entity closure mismatch; genres={missing_genres[:20]} people={missing_people[:20]}"
        )

    return {
        "title_rows": title_rows,
        "genre_rows": [genre_by_id[key] for key in sorted(referenced_genres)],
        "people_rows": [people_by_id[key] for key in sorted(referenced_people)],
        "title_genre_rows": title_genre_rows,
        "title_credit_rows": title_credit_rows,
    }


def physical_shard(global_rows: Mapping[str, list[dict[str, Any]]], shard: int, shard_count: int) -> dict[str, list[dict[str, Any]]]:
    title_rows = [
        row for row in global_rows["title_rows"]
        if audit.qid_number(row["wikidata_qid"]) % shard_count == shard
    ]
    title_ids = {str(row["id"]) for row in title_rows}
    title_genre_rows = [row for row in global_rows["title_genre_rows"] if str(row["title_id"]) in title_ids]
    title_credit_rows = [row for row in global_rows["title_credit_rows"] if str(row["title_id"]) in title_ids]
    genre_ids = {str(row["genre_id"]) for row in title_genre_rows}
    people_ids = {str(row["person_id"]) for row in title_credit_rows}
    genre_by_id = {str(row["id"]): row for row in global_rows["genre_rows"]}
    people_by_id = {str(row["id"]): row for row in global_rows["people_rows"]}
    return {
        "title_rows": sorted(title_rows, key=lambda row: audit.qid_number(row["wikidata_qid"])),
        "genre_rows": [genre_by_id[key] for key in sorted(genre_ids)],
        "people_rows": [people_by_id[key] for key in sorted(people_ids)],
        "title_genre_rows": title_genre_rows,
        "title_credit_rows": title_credit_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-dir", required=True)
    parser.add_argument("--delta-dir", required=True)
    parser.add_argument("--current-manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--parent-shard-count", type=int, default=8)
    parser.add_argument("--delta-shard-count", type=int, default=8)
    parser.add_argument("--output-shard-count", type=int, default=16)
    args = parser.parse_args()

    if args.output_shard_count < 1:
        raise SystemExit("output shard count must be positive")

    parent_dir = Path(args.parent_dir)
    delta_dir = Path(args.delta_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    parent_manifest = delta_module.load_manifest(parent_dir / "recommendation-projection-manifest.json")
    current_manifest = delta_module.load_manifest(args.current_manifest)
    projection_delta = delta_module.manifest_delta(parent_manifest, current_manifest)
    removed = set(projection_delta["removed_qids"])

    parent_rows = load_reviewed_rows(
        parent_dir, prefix="recommendation-materialization-shard", shard_count=args.parent_shard_count
    )
    delta_rows = load_reviewed_rows(
        delta_dir, prefix="recommendation-delta-shard", shard_count=args.delta_shard_count
    )
    global_rows = rebuild_global(
        parent_rows, delta_rows, removed_qids=removed, current_manifest=current_manifest
    )
    global_materialization_sha256 = materialization_fingerprint(global_rows)

    all_qids: set[str] = set()
    shard_summaries: list[dict[str, Any]] = []
    for shard in range(args.output_shard_count):
        rows = physical_shard(global_rows, shard, args.output_shard_count)
        shard_qids = {str(row["wikidata_qid"]) for row in rows["title_rows"]}
        overlap = all_qids & shard_qids
        if overlap:
            raise SystemExit(f"physical shards overlap: {sorted(overlap, key=audit.qid_number)[:20]}")
        all_qids |= shard_qids
        shard_materialization_sha256 = materialization_fingerprint(rows)
        report = {
            "schema_version": "recommendation-metadata-materialization-v3-repartitioned",
            "production_mutation": False,
            "shard_index": shard,
            "shard_count": args.output_shard_count,
            "materialization_sha256": shard_materialization_sha256,
            "global_materialization_sha256": global_materialization_sha256,
            **rows,
            "stats": {
                "candidate_titles": len(rows["title_rows"]),
                "resolved_genres": len(rows["genre_rows"]),
                "resolved_people": len(rows["people_rows"]),
                "emitted_genre_relations": len(rows["title_genre_rows"]),
                "emitted_credit_relations": len(rows["title_credit_rows"]),
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
                "removed_qids": sorted(removed, key=audit.qid_number),
                "physical_partition": f"qid_mod_{args.output_shard_count}",
            },
        }
        (out_dir / f"recommendation-materialization-physical-shard-{shard}.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        sql = enrich.render_sql(report)
        (out_dir / f"recommendation-materialization-physical-shard-{shard}.sql").write_text(
            f"-- Projection manifest SHA-256: {current_manifest['sha256']}\n"
            f"-- Projection candidate count: {current_manifest['candidate_count']}\n"
            f"-- Global materialization SHA-256: {global_materialization_sha256}\n"
            f"-- Shard materialization SHA-256: {shard_materialization_sha256}\n"
            f"-- Rebaseline parent SHA-256: {parent_manifest['sha256']}\n"
            f"-- Physical partition: QID modulo {args.output_shard_count} = {shard}\n"
            + sql,
            encoding="utf-8",
        )
        shard_summaries.append({
            "shard": shard,
            "titles": len(rows["title_rows"]),
            "genre_relations": len(rows["title_genre_rows"]),
            "credit_relations": len(rows["title_credit_rows"]),
            "materialization_sha256": shard_materialization_sha256,
        })

    expected_qids = {str(row["wikidata_qid"]) for row in current_manifest["entries"]}
    if all_qids != expected_qids:
        raise SystemExit("physical shards do not exactly cover current projection")

    summary = {
        "schema_version": "recommendation-metadata-materialization-v3-repartitioned-summary",
        "state": "complete",
        "production_mutation": False,
        "materialization_sha256": global_materialization_sha256,
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
        "physical_shard_count": args.output_shard_count,
        "totals": {
            "candidate_titles": len(global_rows["title_rows"]),
            "genres": len(global_rows["genre_rows"]),
            "people": len(global_rows["people_rows"]),
            "emitted_genre_relations": len(global_rows["title_genre_rows"]),
            "emitted_credit_relations": len(global_rows["title_credit_rows"]),
        },
        "shards": shard_summaries,
    }
    (out_dir / "recommendation-metadata-materialization-v3-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "recommendation-projection-manifest.json").write_text(
        json.dumps(current_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("P1_REPARTITIONED_SUMMARY=" + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
