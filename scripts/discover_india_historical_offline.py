#!/usr/bin/env python3
"""Read-only India-film discovery without consuming Cloudflare D1 rows.

Use this during a D1 free-tier quota pause. A discovery lead is NOT a
net-new title or eligible for import until compared to a live D1 snapshot.
Never generates SQL or writes production data.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_indian_movie_growth import discover


def build_report(candidates: list[dict], source: dict, start_year: int, end_year: int) -> dict:
    by_language = Counter(item.get("language") or "Unknown / multiple" for item in candidates)
    qid_count = sum(bool(item.get("wikidata_qid")) for item in candidates)
    stronger = sum(bool(item.get("india_category")) for item in candidates)
    output = []
    for item in candidates:
        output.append({**item, "classification": "unreconciled_needs_production_dedup"})
    return {
        "schema_version": "indian-offline-discovery-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "years": [start_year, end_year],
        "production_snapshot_available": False,
        "production_import_authorized": False,
        "summary": {
            "discovered_unique_pages": len(candidates),
            "pages_with_wikidata_qid": qid_count,
            "india_category_leads": stronger,
            "verified_net_new_movies": None,
            "imported_movies": 0,
        },
        "by_language": dict(sorted(by_language.items())),
        "source": source,
        "candidates": output,
    }


def markdown(report: dict) -> str:
    summary = report["summary"]
    source = report["source"]
    lines = [
        "# India historical movie discovery — offline production reconciliation pending",
        "",
        "**READ-ONLY SOURCE DISCOVERY. This is not an import or a net-new count.**",
        "Cloudflare D1 was intentionally not accessed. Film identity, country, "
        "year and production duplicate gates remain outstanding.",
        "",
        f"- Years: {report['years'][0]}–{report['years'][1]}",
        f"- Unique Wikipedia article leads: {summary['discovered_unique_pages']:,}",
        f"- With Wikidata QID: {summary['pages_with_wikidata_qid']:,}",
        f"- Membership in Indian-films year category: {summary['india_category_leads']:,}",
        f"- Category requests failed: {source.get('categories_failed', 0)}",
        f"- Interrupted/incomplete scan: {source.get('source_incomplete')}",
        f"- Next category offset: {source.get('next_category_offset')}",
        "- Confirmed net-new vs production: NOT CHECKED",
        "- Production imports: ZERO",
        "",
        "## Language lead counts",
        "",
        "| Language marker | Leads |",
        "| --- | ---: |",
    ]
    for name, count in report["by_language"].items():
        lines.append(f"| {name} | {count:,} |")
    lines.extend([
        "",
        "## Import gate",
        "",
        "After D1's daily limit resets, compare these leads with an up-to-date "
        "production snapshot; then corroborate film type/country and prevent "
        "QID, Wikipedia page, title/year and movie/series collisions before writing.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start-year", type=int, required=True)
    p.add_argument("--end-year", type=int, required=True)
    p.add_argument("--category-offset", type=int, default=0)
    p.add_argument("--max-categories", type=int, default=20)
    p.add_argument("--max-candidates", type=int, default=8000)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-md", type=Path, required=True)
    args = p.parse_args()
    if not 1913 <= args.start_year <= args.end_year <= 2026:
        p.error("years must be 1913..2026")
    if args.category_offset < 0 or not 1 <= args.max_categories <= 50:
        p.error("category offset must be nonnegative, max categories 1..50")
    if not 1 <= args.max_candidates <= 15000:
        p.error("max candidates must be 1..15000")
    candidates, source = discover(args.start_year, args.end_year, args.max_candidates,
                                  args.max_categories, args.category_offset)
    if not candidates:
        raise SystemExit("No source candidates obtained; refusing misleading zero-yield audit")
    report = build_report(candidates, source, args.start_year, args.end_year)
    for path, body in (
        (args.out_json, json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
        (args.out_md, markdown(report)),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print("INDIA_OFFLINE_DISCOVERY=" + json.dumps({
        **report["summary"],
        "years": report["years"],
        "source_incomplete": source["source_incomplete"],
        "next_category_offset": source["next_category_offset"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
