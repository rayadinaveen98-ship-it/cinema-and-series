#!/usr/bin/env python3
"""Combine 1970s/1980s/1990s India source discoveries without using D1.

Each input is an offline historical source-only report. The merged file is a
deduplicated discovery queue, NOT a list of confirmed new films. No SQL is
created and production is never accessed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def merge_source_reports(reports: list[dict]) -> dict:
    by_identity: dict[str, dict] = {}
    input_rows = 0
    for report in reports:
        if report.get("schema_version") != "indian-offline-discovery-v1":
            raise ValueError("Only genuine source-only discovery reports can be merged")
        if report.get("production_snapshot_available") or report.get("production_import_authorized"):
            raise ValueError("Production-reviewed reports must not be treated as raw source evidence")
        for item in report.get("candidates", []):
            input_rows += 1
            qid = str(item.get("wikidata_qid") or "").upper()
            page_id = int(item["page_id"])
            if page_id <= 0:
                raise ValueError("Invalid Wikipedia page ID")
            key = qid if qid.startswith("Q") and qid[1:].isdigit() else f"enwiki:{page_id}"
            evidence = by_identity.get(key)
            if evidence is None:
                evidence = {
                    "page_id": page_id, "wikidata_qid": qid or None,
                    "title": item["title"],
                    "years": set(), "languages": set(), "categories": set(),
                    "india_category": False, "seen_in_decades": set(),
                    "source_url": f"https://en.wikipedia.org/?curid={page_id}",
                }
                by_identity[key] = evidence
            evidence["years"].update(int(y) for y in item.get("observed_years", [])
                                      if isinstance(y, int))
            if isinstance(item.get("year"), int):
                evidence["years"].add(item["year"])
            evidence["languages"].update(item.get("observed_languages") or [])
            evidence["categories"].update(item.get("source_categories") or [])
            evidence["india_category"] = evidence["india_category"] or bool(item.get("india_category"))
            evidence["seen_in_decades"].add(f"{report['years'][0]}–{report['years'][1]}")
    merged = []
    conflicts = 0
    for row in by_identity.values():
        years = sorted(row["years"])
        languages = sorted(row["languages"])
        if len(years) > 1:
            conflicts += 1
        merged.append({
            "page_id": row["page_id"],
            "wikidata_qid": row["wikidata_qid"],
            "title": row["title"],
            "year": years[0] if len(years) == 1 else None,
            "observed_years": years,
            "language": languages[0] if len(languages) == 1 else "Unknown / multiple",
            "observed_languages": languages,
            "india_category": row["india_category"],
            "source_categories": sorted(row["categories"]),
            "source_url": row["source_url"],
            "source_decades": sorted(row["seen_in_decades"]),
            "classification": "unreconciled_needs_production_dedup",
        })
    merged.sort(key=lambda item: (-(item.get("year") or 0), item["title"].casefold()))
    return {
        "schema_version": "indian-historical-source-merge-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "production_snapshot_available": False,
        "production_import_authorized": False,
        "summary": {
            "source_report_count": len(reports),
            "input_page_leads": input_rows,
            "deduplicated_source_identities": len(merged),
            "duplicates_across_reports": input_rows - len(merged),
            "indian_category_evidence": sum(item["india_category"] for item in merged),
            "conflicting_observed_years": conflicts,
            "net_new_confirmed_against_production": None,
            "production_rows_imported": 0,
        },
        "by_decade": {
            str(report["years"][0]): {
                "source_page_leads": report["summary"]["discovered_unique_pages"],
                "source_incomplete": report["source"].get("source_incomplete"),
                "next_category_offset": report["source"].get("next_category_offset"),
            } for report in reports
        },
        "candidates": merged,
    }


def markdown(report: dict) -> str:
    x = report["summary"]
    lines = [
        "# India historical source leads — deduplicated queue",
        "",
        "**No database access, no production imports, no claim of net-new films.**",
        "",
        f"- Input source leads: **{x['input_page_leads']:,}**",
        f"- Unique source identities: **{x['deduplicated_source_identities']:,}**",
        f"- Cross-report duplicates: **{x['duplicates_across_reports']:,}**",
        f"- Indian-films year category leads: **{x['indian_category_evidence']:,}**",
        f"- Conflicting observed years (held for review): **{x['conflicting_observed_years']:,}**",
        "- Confirmed net new vs production: **NOT CHECKED**",
        "- Production imports: **0**",
        "",
        "## By decade",
        "",
        "| Decade start | Article leads | Source scan incomplete | Resume offset |",
        "| --- | ---: | --- | ---: |",
    ]
    for name, item in sorted(report["by_decade"].items()):
        lines.append(f"| {name} | {item['source_page_leads']:,} | "
                     f"{item['source_incomplete']} | {item['next_category_offset']} |")
    lines.extend([
        "",
        "## Mandatory next gates",
        "",
        "After the D1 free-tier read quota resets, compare this evidence to fresh "
        "movie and series catalogue identities, confirm film type/country/year, "
        "and only then prepare guarded production upserts.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, nargs="+", required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-md", type=Path, required=True)
    args = p.parse_args()
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.source]
    report = merge_source_reports(reports)
    for path, body in (
        (args.out_json, json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
        (args.out_md, markdown(report)),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print("INDIA_HISTORICAL_MERGED_SOURCES=" + json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
