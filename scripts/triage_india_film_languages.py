#!/usr/bin/env python3
"""Produce a read-only, identity-checked queue of unresolved film-language evidence.

Consumes only the persisted source-stage SQLite and source-evidence checkpoint.
No Wikidata requests, Cloudflare credentials, production database, or writes to
either input. Entries are review leads, never verified metadata or SQL updates.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

QID = re.compile(r"Q[1-9][0-9]*")
SCHEMA = "india-film-language-evidence-v1"

# Smaller numbers appear first in the downloadable human-review queue.
PRIORITY = {
    "invalid_identity": 0,
    "not_in_stage": 0,
    "identity_mismatch": 0,
    "source_flags_invalid": 0,
    "conflicting_or_multiple_languages": 1,
    "unrecognized_language": 1,
    "unexpected_evidence": 1,
    "general_language_only_P407": 2,
    "no_language_claim": 3,
}

ACTIONS = {
    "invalid_identity": "Verify the film identifier; do not promote the record.",
    "not_in_stage": "Recheck the Wikidata film identity against the staged catalogue.",
    "identity_mismatch": "Reconcile title and release year before reviewing language.",
    "source_flags_invalid": "Inspect unexpected source/verification flags.",
    "conflicting_or_multiple_languages": "Review original-language P364 claims and conflicts.",
    "unrecognized_language": "Identify the claimed language QID using the source.",
    "unexpected_evidence": "Review the source claim and record status manually.",
    "general_language_only_P407": "Find explicit original-language evidence (P364).",
    "no_language_claim": "Look for supported original-language evidence elsewhere.",
}


def clean_title(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def read_stage(path: Path) -> dict[str, dict]:
    with sqlite3.connect(str(path)) as db:
        rows = db.execute(
            "SELECT qid,title,year FROM films "
            "WHERE year_conflict=0 AND title_conflict=0"
        ).fetchall()
    stage = {}
    for qid, title, year in rows:
        if not isinstance(qid, str) or not QID.fullmatch(qid):
            raise ValueError("Invalid staged film QID")
        if qid in stage:
            raise ValueError("Duplicate staged film QID")
        if not isinstance(year, int) or not isinstance(title, str):
            raise ValueError("Malformed staged film identity")
        stage[qid] = {"title": title, "year": year}
    return stage


def triage(stage: dict[str, dict], checkpoint: dict) -> dict:
    if checkpoint.get("schema") != SCHEMA:
        raise ValueError("Unsupported language-evidence checkpoint")
    records = checkpoint.get("records")
    if not isinstance(records, dict):
        raise ValueError("Missing source evidence records")

    queue = []
    counts = Counter()
    decades = Counter()
    accepted = 0
    for qid, record in records.items():
        film = stage.get(qid)
        if not isinstance(record, dict) or not QID.fullmatch(str(qid)) or record.get("qid") != qid:
            category = "invalid_identity"
        elif film is None:
            category = "not_in_stage"
        elif (record.get("year") != film["year"]
              or clean_title(record.get("title")) != clean_title(film["title"])):
            category = "identity_mismatch"
        elif record.get("source_only") is not True or record.get("officially_verified") is not False:
            category = "source_flags_invalid"
        elif record.get("status") == "single_language_evidence" and record.get("property") == "P364":
            if isinstance(record.get("language"), str) and record["language"].strip():
                accepted += 1
                continue
            category = "unexpected_evidence"
        elif record.get("status") == "single_language_evidence" and record.get("property") == "P407":
            category = "general_language_only_P407"
        elif record.get("status") == "ambiguous_multilingual_or_conflicting":
            category = "conflicting_or_multiple_languages"
        elif record.get("status") == "unrecognized_language":
            category = "unrecognized_language"
        elif record.get("status") == "missing_claim":
            category = "no_language_claim"
        else:
            category = "unexpected_evidence"

        source = record if isinstance(record, dict) else {}
        year = film["year"] if film is not None else source.get("year")
        if not isinstance(year, int):
            year = None
        lang_ids = source.get("language_qids")
        lang_ids = sorted(x for x in lang_ids if isinstance(x, str) and QID.fullmatch(x)) if isinstance(lang_ids, list) else []
        row = {
            "qid": qid,
            "title": film["title"] if film is not None else source.get("title"),
            "year": year,
            "category": category,
            "priority": PRIORITY[category],
            "source_url": ("https://www.wikidata.org/wiki/" + qid) if QID.fullmatch(str(qid)) else None,
            "language_claim_qids": lang_ids,
            "claim_property": source.get("property"),
            "evidence_status": source.get("status"),
            "suggested_review": ACTIONS[category],
            "production_update_allowed": False,
        }
        queue.append(row)
        counts[category] += 1
        if year is not None:
            decades[str((year // 10) * 10)] += 1

    queue.sort(key=lambda row: (row["priority"], row["year"] if row["year"] is not None else 9999, str(row["qid"])))
    report = {
        "schema": "india-film-language-review-queue-v1",
        "source_only": True, "d1_reads": 0, "d1_writes": 0,
        "production_updates": 0, "official_verifications": 0,
        "stage_film_identities": len(stage),
        "checkpoint_records": len(records),
        "accepted_source_p364": accepted,
        "needs_review": len(queue),
        "by_category": dict(sorted(counts.items())),
        "by_decade": dict(sorted(decades.items(), key=lambda item: int(item[0]))),
        "review_queue": queue,
        "note": "Source research queue only. Review before any separate production reconciliation.",
    }
    if report["accepted_source_p364"] + report["needs_review"] != len(records):
        raise AssertionError("Source evidence was dropped from triage accounting")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
    report = triage(read_stage(args.stage), checkpoint)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("INDIA_LANGUAGE_REVIEW_QUEUE=" + json.dumps({
        key: report[key] for key in ("checkpoint_records", "accepted_source_p364",
                                    "needs_review", "by_category", "by_decade",
                                    "d1_reads", "d1_writes")
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
