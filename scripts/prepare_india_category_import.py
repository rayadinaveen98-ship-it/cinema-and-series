#!/usr/bin/env python3
"""Prepare a bounded Indian movie import from already-discovered Wikipedia entries.

Only exact 'Category:YYYY Indian films' members with an article, stable QID,
unambiguous year and a net-new snapshot classification qualify. Reuse the
idempotent SQL with fresh database duplicate checks. This lane does not claim
official verification and never invents a release day.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_identity_corrections as identity
from verify_indian_movie_candidates import QID, sql_for_movie


def eligible(item: dict) -> str:
    if item.get("classification") != "new_indian_category_candidates":
        return "not_new_india_category_candidate"
    year = item.get("year")
    if not isinstance(year, int) or not 1913 <= year <= 2026:
        return "uncertain_year"
    if f"Category:{year} Indian films" not in (item.get("source_categories") or []):
        return "missing_matching_year_india_category"
    qid = str(item.get("wikidata_qid") or "").upper()
    if not QID.fullmatch(qid):
        return "missing_valid_wikidata_id"
    if not identity.is_media_type_allowed(qid, "movie"):
        return "excluded_or_series_identity"
    page_id = item.get("page_id")
    if not isinstance(page_id, int) or page_id <= 0:
        return "missing_wikipedia_article"
    title = str(item.get("title") or "").strip()
    if not title or title.upper() == qid or title.casefold().startswith(("list of ", "lists of ")):
        return "unresolved_or_list_title"
    return "eligible"


def select_batch(report: dict, maximum: int) -> tuple[list[dict], dict]:
    if not 1 <= maximum <= 250:
        raise ValueError("pilot batch cap must be between 1 and 250")
    seen_qids = set()
    chosen = []
    reasons = Counter()
    rows = report.get("candidates") or []
    for item in sorted(rows, key=lambda row: (-int(row.get("year") or 0),
                                             str(row.get("title") or "").casefold())):
        reason = eligible(item)
        if reason != "eligible":
            reasons[reason] += 1
            continue
        qid = str(item["wikidata_qid"]).upper()
        if qid in seen_qids:
            reasons["duplicate_discovery_qid"] += 1
            continue
        seen_qids.add(qid)
        source_category = f"Category:{item['year']} Indian films"
        chosen.append({**item, "source_categories": [
            source_category,
            *[category for category in item["source_categories"] if category != source_category],
        ]})
    total_qualified = len(chosen)
    return chosen[:maximum], {
        "discovered_pages": len(rows),
        "eligible_source_category_records": total_qualified,
        "proposed_batch_count": min(total_qualified, maximum),
        "excluded_reasons": dict(reasons),
        "source_incomplete": bool(report.get("source", {}).get("source_incomplete")),
        "status": "Wikipedia category-based, unconfirmed movie records; NOT Wikidata-claim corroborated",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", type=Path, required=True)
    parser.add_argument("--max-import", type=int, default=100)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-sql", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.audit_json.read_text(encoding="utf-8"))
    selected, summary = select_batch(report, args.max_import)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps({"summary": summary, "selected": selected},
                                         indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.out_sql.parent.mkdir(parents=True, exist_ok=True)
    args.out_sql.write_text(
        "-- Bounded Wikipedia Indian-film category import. All records remain unconfirmed.\n"
        + "\n".join(sql_for_movie(item) for item in selected) + "\n", encoding="utf-8"
    )
    print("INDIA_CATEGORY_IMPORT_PLAN=" + json.dumps(summary, sort_keys=True))
    if not selected:
        raise SystemExit("No eligible movies. Import aborted before D1 write.")


if __name__ == "__main__":
    main()
