#!/usr/bin/env python3
"""Read-only Indian movie expansion discovery and production-deduplication audit.

Wikipedia article/category membership is discovery evidence, not proof that a
page is a film or that an Indian-language film was produced in India.
No D1 writes, SQL output, artwork scraping or fabricated release dates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_mediawiki_backfill as wiki
from production_catalogue_quality import load_d1_rows, norm, valid_qid, year_from_date

LANGUAGE_CATEGORIES = {
    "Telugu": "Telugu-language films",
    "Tamil": "Tamil-language films",
    "Malayalam": "Malayalam-language films",
    "Kannada": "Kannada-language films",
    "Hindi": "Hindi-language films",
    "Bengali": "Bengali-language films",
    "Marathi": "Marathi-language films",
    "Punjabi": "Punjabi-language films",
    "Gujarati": "Gujarati-language films",
    "Odia": "Odia-language films",
    "Assamese": "Assamese-language films",
    "Bhojpuri": "Bhojpuri-language films",
}
PAGE_CAP = 500
PAGEPROPS_BATCH = 50
REQUEST_PAUSE = 0.24
QID_PATTERN = re.compile(r"^Q[1-9][0-9]*$")


def category_seeds(start_year: int, end_year: int):
    """Include confirmed India category and explicitly weaker language signals."""
    for year in range(end_year, start_year - 1, -1):
        yield (f"Category:{year} Indian films", year, None, "india_category")
        for language, suffix in LANGUAGE_CATEGORIES.items():
            yield (f"Category:{year} {suffix}", year, language, "language_category")


def category_pages(category: str, cap: int = PAGE_CAP) -> list[dict]:
    collected: list[dict] = []
    continuation = None
    while len(collected) < cap:
        params = {
            "action": "query", "list": "categorymembers", "cmtitle": category,
            "cmnamespace": "0", "cmtype": "page",
            "cmlimit": str(min(500, cap - len(collected))),
            "format": "json", "formatversion": "2",
        }
        if continuation:
            params["cmcontinue"] = continuation
        payload = wiki.request_json(wiki.ENWIKI_API, params)
        for page in payload.get("query", {}).get("categorymembers", []):
            name = str(page.get("title") or "").strip()
            page_id = int(page.get("pageid") or 0)
            if page_id <= 0 or not name or name.casefold().startswith(("list of ", "lists of ")):
                continue
            collected.append({"page_id": page_id, "title": name})
        continuation = payload.get("continue", {}).get("cmcontinue")
        if not continuation:
            break
        time.sleep(REQUEST_PAUSE)
    return collected


def resolve_page_qids(page_ids: list[int]) -> tuple[dict[int, str], int]:
    mapping: dict[int, str] = {}
    failed_batches = 0
    for index in range(0, len(page_ids), PAGEPROPS_BATCH):
        batch = page_ids[index:index + PAGEPROPS_BATCH]
        try:
            payload = wiki.request_json(
                wiki.ENWIKI_API,
                {"action": "query", "prop": "pageprops", "ppprop": "wikibase_item",
                 "pageids": "|".join(map(str, batch)), "format": "json",
                 "formatversion": "2"},
                post=True,
            )
            for page in payload.get("query", {}).get("pages", []):
                qid = str(page.get("pageprops", {}).get("wikibase_item") or "").upper()
                if QID_PATTERN.fullmatch(qid):
                    mapping[int(page["pageid"])] = qid
        except Exception as exc:
            failed_batches += 1
            print(f"Pageprops batch {index // PAGEPROPS_BATCH} deferred: {str(exc)[:150]}")
        time.sleep(REQUEST_PAUSE)
    return mapping, failed_batches


def discover(start_year: int, end_year: int, max_candidates: int, max_categories: int = 0) -> tuple[list[dict], dict]:
    by_page: dict[int, dict] = {}
    reports = []
    seeds = category_seeds(start_year, end_year)
    incomplete = False
    for index, (category, year, language, evidence) in enumerate(seeds):
        if max_categories and index >= max_categories:
            incomplete = True
            break
        if len(by_page) >= max_candidates:
            incomplete = True
            break
        try:
            pages = category_pages(category)
            status = "ok"
        except Exception as exc:
            pages = []
            status = "error"
            print(f"Category deferred {category}: {str(exc)[:150]}")
        reports.append({"category": category, "status": status, "articles": len(pages)})
        if status != "ok":
            incomplete = True
        for page in pages:
            page_id = page["page_id"]
            if page_id not in by_page and len(by_page) >= max_candidates:
                incomplete = True
                break
            item = by_page.setdefault(page_id, {
                "page_id": page_id, "title": page["title"],
                "years": set(), "languages": set(), "categories": set(),
                "india_category": False,
            })
            item["years"].add(year)
            item["categories"].add(category)
            if language:
                item["languages"].add(language)
            if evidence == "india_category":
                item["india_category"] = True
        time.sleep(REQUEST_PAUSE)
    qids, failed_qid_batches = resolve_page_qids(sorted(by_page))
    if failed_qid_batches:
        incomplete = True
    records = []
    for page_id in sorted(by_page):
        item = by_page[page_id]
        languages = sorted(item["languages"])
        years = sorted(item["years"])
        records.append({
            "page_id": page_id,
            "wikidata_qid": qids.get(page_id),
            "title": item["title"],
            "year": years[0] if len(years) == 1 else None,
            "observed_years": years,
            "language": languages[0] if len(languages) == 1 else "Unknown / multiple",
            "observed_languages": languages,
            "india_category": item["india_category"],
            "source_categories": sorted(item["categories"]),
            "source_url": f"https://en.wikipedia.org/?curid={page_id}",
        })
    meta = {
        "categories_attempted": len(reports),
        "categories_failed": sum(p["status"] != "ok" for p in reports),
        "qid_resolution_failed_batches": failed_qid_batches,
        "source_incomplete": incomplete,
        "category_report": reports,
    }
    return records, meta


def audit(candidates: list[dict], exact_movies: list[dict], year_movies: list[dict], source_meta: dict | None = None) -> dict:
    existing_qids: set[str] = set()
    existing_pages: set[int] = set()
    existing_title_year: set[tuple[str, int]] = set()

    for row in exact_movies + year_movies:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if valid_qid(qid):
            existing_qids.add(qid)
        page_id = row.get("wikipedia_page_id")
        if page_id:
            try:
                existing_pages.add(int(page_id))
            except (TypeError, ValueError):
                pass
        year = year_from_date(row.get("release_date"))
        if year is None:
            try:
                year = int(row["release_year"])
            except (KeyError, ValueError, TypeError):
                pass
        if isinstance(year, int) and norm(row.get("title")):
            existing_title_year.add((norm(row["title"]), year))

    seen_pages = set()
    seen_qids = set()
    classifications = Counter()
    language_counts: dict[str, Counter] = defaultdict(Counter)
    reviewed = []
    for item in candidates:
        page_id = int(item["page_id"])
        qid = str(item.get("wikidata_qid") or "").strip().upper()
        year = item.get("year")
        title = norm(item.get("title"))
        if page_id in seen_pages or (QID_PATTERN.fullmatch(qid) and qid in seen_qids):
            classifications["duplicate_inside_discovery"] += 1
            continue
        seen_pages.add(page_id)
        if QID_PATTERN.fullmatch(qid):
            seen_qids.add(qid)
        if page_id in existing_pages or (QID_PATTERN.fullmatch(qid) and qid in existing_qids):
            bucket = "already_in_production"
        elif not title or not isinstance(year, int) or not (1913 <= year <= 2027):
            bucket = "needs_identity_or_year_review"
        elif (title, year) in existing_title_year:
            bucket = "possible_existing_title_year_match"
        elif item.get("india_category"):
            bucket = "new_indian_category_candidates"
        else:
            bucket = "new_language_only_candidates"
        classifications[bucket] += 1
        language = str(item.get("language") or "Unknown / multiple")
        language_counts[language][bucket] += 1
        reviewed.append({**item, "classification": bucket})

    summary = {
        "discovered_unique_pages": len(seen_pages),
        "already_in_production": classifications["already_in_production"],
        "possible_existing_title_year_match": classifications["possible_existing_title_year_match"],
        "needs_identity_or_year_review": classifications["needs_identity_or_year_review"],
        "new_indian_category_candidates": classifications["new_indian_category_candidates"],
        "new_language_only_candidates": classifications["new_language_only_candidates"],
        "total_net_new_discovery_candidates": (
            classifications["new_indian_category_candidates"] + classifications["new_language_only_candidates"]
        ),
        "duplicate_inside_discovery": classifications["duplicate_inside_discovery"],
        "production_exact_movie_rows": len(exact_movies),
        "production_year_movie_rows": len(year_movies),
    }
    return {
        "schema_version": "india-movie-discovery-audit-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "source": source_meta or {},
        "by_language": {key: dict(value) for key, value in sorted(language_counts.items())},
        "candidates": reviewed,
    }


def markdown_report(report: dict) -> str:
    summary = report["summary"]
    source = report["source"]
    text = [
        "# India movie expansion — read-only discovery audit",
        "",
        "**This is not an import, a total market count, or a confirmed count of Indian films.** "
        "Wikipedia category pages are discovery leads requiring film/country validation.",
        "",
        f"Source audit incomplete: **{source.get('source_incomplete', 'unknown')}**; "
        f"failed categories: **{source.get('categories_failed', 0)}**; "
        f"failed pageprops batches: **{source.get('qid_resolution_failed_batches', 0)}**.",
        "",
        "| Metric | Count |", "| --- | ---: |",
    ]
    for key, value in summary.items():
        text.append(f"| {key.replace('_', ' ')} | {value:,} |")
    text.extend(["", "## Candidate breakdown by source language", "",
                 "| Language label | New India category | New language-only | Existing | Needs review |",
                 "| --- | ---: | ---: | ---: | ---: |"])
    for language, counts in report["by_language"].items():
        review = counts.get("possible_existing_title_year_match", 0) + counts.get("needs_identity_or_year_review", 0)
        text.append(
            f"| {language} | {counts.get('new_indian_category_candidates', 0):,} | "
            f"{counts.get('new_language_only_candidates', 0):,} | "
            f"{counts.get('already_in_production', 0):,} | {review:,} |"
        )
    text.extend(["", "### Caveats", "",
        "- Language-category membership does not by itself establish Indian production.",
        "- Category membership alone does not guarantee a page represents a film.",
        "- A title+year collision stays in review, not counted as new.",
        "- Country/type, provenance and duplicate checks are required before any production import.",
        "- No database mutations or artwork publication happen in this audit.",
    ])
    return "\n".join(text) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--max-candidates", type=int, default=8000)
    parser.add_argument("--max-categories", type=int, default=0)
    parser.add_argument("--exact-movies", type=Path, required=True)
    parser.add_argument("--year-movies", type=Path, required=True)
    parser.add_argument("--candidates-file", type=Path, help="Optional offline discovery fixture")
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()
    if not (1913 <= args.start_year <= args.end_year <= 2026):
        parser.error("year bounds must be between 1913 and 2026")
    if not (1 <= args.max_candidates <= 15000):
        parser.error("--max-candidates must be 1..15000")

    if args.candidates_file:
        candidates = json.loads(args.candidates_file.read_text(encoding="utf-8"))
        meta = {"source_incomplete": False, "mode": "offline"}
    else:
        candidates, meta = discover(args.start_year, args.end_year, args.max_candidates, args.max_categories)
    if not candidates:
        raise SystemExit("No discovery candidates obtained; refusing a misleading zero-yield audit")

    report = audit(candidates, load_d1_rows(args.exact_movies), load_d1_rows(args.year_movies), meta)
    for path, body in ((args.out_json, json.dumps(report, indent=2, ensure_ascii=False) + "\n"),
                       (args.out_md, markdown_report(report))):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print("INDIA_MOVIE_AUDIT_SUMMARY=" + json.dumps(report["summary"], sort_keys=True))
    print("INDIA_MOVIE_AUDIT_SOURCE=" + json.dumps({k: v for k, v in meta.items() if k != "category_report"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
