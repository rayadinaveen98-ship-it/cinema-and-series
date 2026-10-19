#!/usr/bin/env python3
"""Read-only audit of decade/language coverage in source-backed Indian film claims.

No network, production database, or SQL write access. This is NOT an import or
claim that source-language evidence is officially verified.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

QID = re.compile(r"Q[1-9][0-9]*")


def clean_title(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def audit(stage: dict[str, dict], checkpoint: dict) -> dict:
    if checkpoint.get("schema") != "india-film-language-evidence-v1":
        raise ValueError("Unexpected source-checkpoint schema")
    records = checkpoint.get("records")
    if not isinstance(records, dict):
        raise ValueError("Missing evidence records")
    source_by_decade = Counter()
    checked_by_decade = Counter()
    original_by_decade = Counter()
    original_by_language = Counter()
    status_counts = Counter()
    mismatched_years = []
    mismatched_titles = []
    missing_stage = []
    invalid_records = []
    for qid, info in stage.items():
        if not QID.fullmatch(qid) or not isinstance(info["year"], int):
            raise ValueError("Invalid staged film identity")
        source_by_decade[10 * (info["year"] // 10)] += 1
    for qid, record in records.items():
        if not QID.fullmatch(qid) or not isinstance(record, dict) or record.get("qid") != qid:
            invalid_records.append(qid)
            continue
        staged = stage.get(qid)
        if staged is None:
            missing_stage.append(qid)
            continue
        if staged["year"] != record.get("year"):
            mismatched_years.append(qid)
            continue
        if clean_title(staged["title"]) != clean_title(record.get("title")):
            mismatched_titles.append(qid)
            continue
        decade = 10 * (staged["year"] // 10)
        checked_by_decade[decade] += 1
        status = record.get("status")
        status_counts[status or "missing_status"] += 1
        if (status == "single_language_evidence"
                and record.get("property") == "P364"
                and record.get("source_only") is True
                and record.get("officially_verified") is False
                and isinstance(record.get("language"), str)):
            original_by_decade[decade] += 1
            original_by_language[record["language"]] += 1

    totals = {}
    for decade in sorted(source_by_decade):
        source_n = source_by_decade[decade]
        checked = checked_by_decade[decade]
        strict = original_by_decade[decade]
        totals[str(decade)] = {
            "source_films": source_n, "reviewed_identities": checked,
            "strict_original_language": strict, "pending": source_n - checked,
            "coverage_pct": round(100 * strict / source_n, 2) if source_n else 0,
        }
    report = {
        "schema": "india-film-language-coverage-audit-v1",
        "source_only": True, "d1_reads": 0, "d1_writes": 0,
        "staged_qids": len(stage), "checkpoint_records": len(records),
        "matched_reviewed_identities": sum(checked_by_decade.values()),
        "strict_original_language": sum(original_by_decade.values()),
        "by_decade": totals,
        "strict_languages": dict(sorted(original_by_language.items(),
                                         key=lambda entry: (-entry[1], entry[0]))),
        "status_counts": dict(sorted(status_counts.items())),
        "held_for_review": {
            "not_in_stage": {"count": len(missing_stage), "sample": missing_stage[:12]},
            "year_mismatch": {"count": len(mismatched_years), "sample": mismatched_years[:12]},
            "title_mismatch": {"count": len(mismatched_titles), "sample": mismatched_titles[:12]},
            "invalid_identity": {"count": len(invalid_records), "sample": invalid_records[:12]},
        },
        "note": "Wikidata P364 language evidence, not official film or release-date verification.",
    }
    if sum(x["source_films"] for x in totals.values()) != len(stage):
        raise AssertionError("Decade source count mismatch")
    if sum(x["reviewed_identities"] for x in totals.values()) != report["matched_reviewed_identities"]:
        raise AssertionError("Decade review count mismatch")
    if sum(x["strict_original_language"] for x in totals.values()) != report["strict_original_language"]:
        raise AssertionError("Decade language count mismatch")
    return report


def read_stage(path: Path) -> dict[str, dict]:
    with sqlite3.connect(str(path)) as conn:
        rows = conn.execute(
            "SELECT qid,title,year FROM films WHERE year_conflict=0 AND title_conflict=0"
        ).fetchall()
    stage = {}
    for qid, title, year in rows:
        if qid in stage:
            raise ValueError("Duplicate staged film QID")
        stage[qid] = {"title": title, "year": year}
    return stage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(read_stage(args.stage), json.loads(args.checkpoint.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("INDIA_LANGUAGE_COVERAGE_AUDIT=" + json.dumps({
        key: report[key] for key in ["staged_qids", "checkpoint_records",
                                    "matched_reviewed_identities",
                                    "strict_original_language", "held_for_review"]
    }, sort_keys=True), flush=True)
    print("INDIA_LANGUAGE_DECADE_COVERAGE=" + json.dumps(report["by_decade"], sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
