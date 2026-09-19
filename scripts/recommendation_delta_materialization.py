#!/usr/bin/env python3
"""Materialize only identities added since a reviewed Recommendation P1 baseline.

Unchanged manifest entries reuse the immutable parent materialization. Removed
identities must be backed by the reviewed media-identity correction registry.
Changed common entries are never silently reused: they hard-fail and require a
fresh full materialization decision.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import enrich_recommendation_metadata as enrich
    import media_identity_corrections as identity
    import recommendation_metadata_audit as audit
except ModuleNotFoundError:
    from scripts import enrich_recommendation_metadata as enrich
    from scripts import media_identity_corrections as identity
    from scripts import recommendation_metadata_audit as audit


def load_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list) or not payload.get("sha256"):
        raise ValueError(f"invalid projection manifest: {path}")
    return payload


def manifest_delta(parent: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    parent_by_qid = {str(row["wikidata_qid"]): row for row in parent["entries"]}
    current_by_qid = {str(row["wikidata_qid"]): row for row in current["entries"]}
    parent_qids = set(parent_by_qid)
    current_qids = set(current_by_qid)

    changed = sorted(
        qid for qid in parent_qids & current_qids
        if parent_by_qid[qid] != current_by_qid[qid]
    )
    if changed:
        raise ValueError(f"common projection entries changed and cannot be inherited: {changed[:20]}")

    added = sorted(current_qids - parent_qids, key=audit.qid_number)
    removed = sorted(parent_qids - current_qids, key=audit.qid_number)
    corrections = identity.load_registry()
    unauthorized_removed = [
        qid for qid in removed
        if qid not in corrections or corrections[qid].get("disposition") != "exclude"
    ]
    if unauthorized_removed:
        raise ValueError(
            f"removed identities lack reviewed exclusion provenance: {unauthorized_removed[:20]}"
        )

    return {
        "added_qids": added,
        "removed_qids": removed,
        "unchanged_count": len(parent_qids & current_qids),
        "added_count": len(added),
        "removed_count": len(removed),
        "parent_by_qid": parent_by_qid,
        "current_by_qid": current_by_qid,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-manifest", required=True)
    parser.add_argument("--current-manifest", required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, default=8)
    parser.add_argument("--max-titles", type=int, default=500)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-sql", required=True)
    args = parser.parse_args()

    parent = load_manifest(args.parent_manifest)
    current = load_manifest(args.current_manifest)
    delta = manifest_delta(parent, current)
    candidates = [
        delta["current_by_qid"][qid]
        for qid in delta["added_qids"]
        if audit.qid_number(qid) % args.shard_count == args.shard_index
    ]
    if len(candidates) > args.max_titles:
        raise SystemExit(
            f"delta shard {args.shard_index} has {len(candidates)} titles, above cap {args.max_titles}"
        )

    title_entities = audit.fetch_claim_entities([row["wikidata_qid"] for row in candidates])
    relations, genre_qids, people_qids, _ = enrich.collect_relations(candidates, title_entities)
    labels = enrich.fetch_entity_labels(sorted(genre_qids | people_qids, key=audit.qid_number))
    result = enrich.materialize(candidates, title_entities, labels)
    result.update(
        {
            "schema_version": "recommendation-metadata-delta-materialization-v1",
            "production_mutation": False,
            "shard_index": args.shard_index,
            "shard_count": args.shard_count,
            "parent_projection_sha256": parent["sha256"],
            "current_projection_sha256": current["sha256"],
            "projection_delta": {
                "unchanged_count": delta["unchanged_count"],
                "added_count": delta["added_count"],
                "removed_count": delta["removed_count"],
                "removed_qids": delta["removed_qids"],
            },
            "raw_relation_count": len(relations),
        }
    )
    sql = enrich.render_sql(result)
    prefix = (
        f"-- Projection manifest SHA-256: {current['sha256']}\n"
        f"-- Parent projection SHA-256: {parent['sha256']}\n"
        f"-- Delta-only shard: {args.shard_index}/{args.shard_count - 1}\n"
    )
    Path(args.out_json).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.out_sql).write_text(prefix + sql, encoding="utf-8")
    print("P1_DELTA_MATERIALIZATION=" + json.dumps({
        "shard": args.shard_index,
        "candidate_titles": result["stats"]["candidate_titles"],
        "emitted_genre_relations": result["stats"]["emitted_genre_relations"],
        "emitted_credit_relations": result["stats"]["emitted_credit_relations"],
        "current_projection_sha256": current["sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
