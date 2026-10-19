#!/usr/bin/env python3
"""Prepare conservative P364 film-language updates from sourced evidence.

Inputs:
  - immutable source-only Wikidata language checkpoint
  - fresh read-only D1 snapshot of year-precision films with unknown language

No internet or Cloudflare access in this script. The output is reviewable
SQL; applying it is a separate guarded production operation.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Mapping

SCHEMA = "india-film-language-evidence-v1"
QID_RE = re.compile(r"^Q[1-9][0-9]*$")
LANGUAGES = frozenset({
    "Telugu", "Tamil", "Hindi", "Malayalam", "Kannada", "Bengali",
    "Marathi", "Punjabi", "Gujarati", "Odia", "Assamese", "Bhojpuri",
    "English", "Urdu", "Sanskrit", "Nepali", "Konkani", "Sindhi",
    "Kashmiri", "Manipuri", "Maithili", "Dogri", "Japanese", "French",
    "Arabic", "Persian", "German", "Spanish",
})
UNKNOWN = frozenset({"", "unknown", "xx", "und", "n/a", "na", "none", "null"})


def normalized(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def unknown_language(value: object) -> bool:
    return normalized(value) in UNKNOWN


def sql_quote(value: object) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def d1_rows(payload: object) -> list[dict]:
    batches = payload if isinstance(payload, list) else [payload]
    if not batches or not all(isinstance(batch, dict) and isinstance(batch.get("results"), list) for batch in batches):
        raise ValueError("Invalid D1 snapshot: expected results arrays")
    return [row for batch in batches for row in batch["results"] if isinstance(row, dict)]


def reconcile(checkpoint: Mapping, rows: list[dict], max_updates: int = 1000) -> dict:
    if checkpoint.get("schema") != SCHEMA or not isinstance(checkpoint.get("records"), dict):
        raise ValueError("Invalid source checkpoint")
    if not 1 <= max_updates <= 1500:
        raise ValueError("Unsafe update cap")
    index: dict[str, dict] = {}
    reasons = Counter()
    for row in rows:
        qid = row.get("wikidata_qid")
        if not isinstance(qid, str) or not QID_RE.fullmatch(qid):
            reasons["invalid_d1_id"] += 1
            continue
        if qid in index:
            raise ValueError("Duplicate QID in D1 reconciliation snapshot: " + qid)
        index[qid] = row

    proposals = []
    for qid in sorted(checkpoint["records"], key=lambda q: (int(q[1:]) if QID_RE.fullmatch(q) else 0, q)):
        source = checkpoint["records"][qid]
        if not isinstance(source, dict) or not QID_RE.fullmatch(qid):
            reasons["bad_source_record"] += 1
            continue
        if (source.get("status") != "single_language_evidence"
                or source.get("property") != "P364"
                or source.get("source_only") is not True
                or source.get("officially_verified") is not False
                or source.get("language") not in LANGUAGES
                or source.get("qid") != qid
                or source.get("source_url") != f"https://www.wikidata.org/wiki/{qid}"):
            reasons["not_strict_p364_evidence"] += 1
            continue
        row = index.get(qid)
        if row is None:
            reasons["not_in_unknown_production_snapshot"] += 1
            continue
        if not unknown_language(row.get("language_name")):
            reasons["already_known_language"] += 1
            continue
        if str(row.get("country_code") or "").upper() != "IN":
            reasons["not_indian_film"] += 1
            continue
        if normalized(row.get("title")) != normalized(source.get("title")) or not normalized(source.get("title")):
            reasons["title_mismatch"] += 1
            continue
        if (not isinstance(source.get("year"), int)
                or row.get("release_year") != source["year"]):
            reasons["year_mismatch"] += 1
            continue
        proposal = {
            "id": str(row["id"]), "qid": qid, "title": row["title"],
            "year": source["year"], "language": source["language"],
            "language_source": "wikidata:P364",
            "language_source_url": source["source_url"],
        }
        if not proposal["id"]:
            reasons["missing_row_id"] += 1
            continue
        proposals.append(proposal)
        if len(proposals) >= max_updates:
            break
    return {"schema": "india-film-language-reconciliation-v1",
            "source_records": len(checkpoint["records"]),
            "production_snapshot_rows": len(rows),
            "selected": proposals, "selected_count": len(proposals),
            "rejected_reasons": dict(sorted(reasons.items())),
            "production_writes": 0}


def guarded_update_sql(row: dict) -> str:
    # Every field is checked again by D1, so a stale snapshot cannot overwrite
    # a corrected language or a reidentified film between audit and apply.
    return (
        "UPDATE catalogue_titles SET "
        f"language_name={sql_quote(row['language'])}, "
        "language_source='wikidata:P364', "
        f"language_source_url={sql_quote(row['language_source_url'])}, "
        "updated_at=CURRENT_TIMESTAMP "
        f"WHERE id={sql_quote(row['id'])} "
        f"AND wikidata_qid={sql_quote(row['qid'])} "
        f"AND title={sql_quote(row['title'])} COLLATE NOCASE "
        f"AND release_year={int(row['year'])} AND country_code='IN' "
        "AND (language_name IS NULL OR LOWER(TRIM(language_name)) IN "
        "('', 'unknown', 'xx', 'und', 'n/a', 'na', 'none', 'null')) "
        "AND (language_source IS NULL OR TRIM(language_source)='');"
    )


def output_files(result: dict, target: Path, chunk_size: int = 100) -> None:
    if not 1 <= chunk_size <= 150:
        raise ValueError("Unsafe SQL chunk")
    target.mkdir(parents=True, exist_ok=True)
    (target / "reconciliation.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    rows = result["selected"]
    for i in range(0, len(rows), chunk_size):
        sql = "-- Film language evidence from explicit Wikidata P364; no release verification.\n"
        sql += "\n".join(guarded_update_sql(row) for row in rows[i:i + chunk_size]) + "\n"
        (target / f"language-{i // chunk_size:03d}.sql").write_text(sql, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--production-snapshot", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--max-updates", type=int, default=1000)
    args = parser.parse_args()
    result = reconcile(
        json.loads(args.checkpoint.read_text(encoding="utf-8")),
        d1_rows(json.loads(args.production_snapshot.read_text(encoding="utf-8"))),
        args.max_updates,
    )
    output_files(result, args.out_dir)
    print("INDIA_FILM_LANGUAGE_RECONCILIATION=" + json.dumps({
        k: v for k, v in result.items() if k != "selected"
    }, sort_keys=True), flush=True)
    print("INDIA_FILM_LANGUAGE_SAMPLE=" + json.dumps(result["selected"][:12], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
