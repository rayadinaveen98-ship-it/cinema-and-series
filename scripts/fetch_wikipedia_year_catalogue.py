#!/usr/bin/env python3
"""Build a broad year-precision movie catalogue from English Wikipedia.

Wikipedia year + country/language categories provide an honest release year.
The discovery query also requests Wikipedia pageprops, so a Wikidata QID is
captured in the same request whenever available. A slower page-ID fallback is
used only for pages whose QID was not returned during discovery.

No fake day/month is created. Rows land in `catalogue_titles`; exact-day
release intelligence in `movies` remains untouched and higher-trust.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from dataclasses import dataclass
from pathlib import Path

import fetch_mediawiki_backfill as base

OUT = Path("data/generated/wikipedia-year-catalogue.json")
MAX_TITLES_PER_RUN = 4000
CATEGORY_MEMBER_CAP = 140
PAGEPROP_BATCH = 50
REQUEST_DELAY_SECONDS = 0.50
QID_FALLBACK_DELAY_SECONDS = 1.0
MAX_CONSECUTIVE_CATEGORY_FAILURES = 40
FAILURE_COOLDOWN_EVERY = 5
FAILURE_COOLDOWN_SECONDS = 8


@dataclass(frozen=True)
class Discovery:
    page_id: int
    title: str
    release_year: int
    country_code: str
    language: str | None
    category: str
    wikidata_qid: str | None = None


def category_year(category: str) -> int:
    match = re.search(r"Category:(\d{4})\b", category)
    if not match:
        raise ValueError(f"category lacks leading release year: {category}")
    return int(match.group(1))


def _interleave(values_a: list[base.Seed], values_b: list[base.Seed]) -> list[base.Seed]:
    result: list[base.Seed] = []
    maximum = max(len(values_a), len(values_b))
    for index in range(maximum):
        if index < len(values_a):
            result.append(values_a[index])
        if index < len(values_b):
            result.append(values_b[index])
    return result


def ordered_seeds(profile: str) -> list[base.Seed]:
    seeds = base.build_seeds(profile)
    by_year: dict[int, list[base.Seed]] = {}
    for seed in seeds:
        by_year.setdefault(category_year(seed.category), []).append(seed)

    ordered: list[base.Seed] = []
    for year in sorted(by_year, reverse=True):
        year_seeds = by_year[year]
        india = sorted(
            (seed for seed in year_seeds if seed.group.startswith("india-")),
            key=lambda seed: seed.group.casefold(),
        )
        global_countries = sorted(
            (seed for seed in year_seeds if not seed.group.startswith("india-")),
            key=lambda seed: seed.group.casefold(),
        )
        ordered.extend(_interleave(india, global_countries))
    return ordered


def category_members(seed: base.Seed, cap: int = CATEGORY_MEMBER_CAP) -> list[Discovery]:
    """Discover article rows and QIDs in one MediaWiki request family."""
    rows: list[Discovery] = []
    continuation: str | None = None
    year = category_year(seed.category)
    while len(rows) < cap:
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": seed.category,
            "gcmnamespace": "0",
            "gcmtype": "page",
            "gcmlimit": str(min(500, cap - len(rows))),
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        }
        if continuation:
            params["gcmcontinue"] = continuation
        payload = base.request_json(base.ENWIKI_API, params)
        for page in payload.get("query", {}).get("pages", []):
            title = str(page.get("title") or "").strip()
            page_id = int(page.get("pageid") or 0)
            qid = str(page.get("pageprops", {}).get("wikibase_item") or "").strip() or None
            if qid and not qid.startswith("Q"):
                qid = None
            if not title or page_id <= 0 or title.casefold().startswith("list of "):
                continue
            rows.append(
                Discovery(
                    page_id=page_id,
                    title=title,
                    release_year=year,
                    country_code=seed.country_code,
                    language=seed.language,
                    category=seed.category,
                    wikidata_qid=qid,
                )
            )
            if len(rows) >= cap:
                break
        continuation = payload.get("continue", {}).get("gcmcontinue")
        if not continuation:
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return rows


def discover(profile: str, maximum: int) -> tuple[dict[int, list[Discovery]], list[dict]]:
    by_page: dict[int, list[Discovery]] = {}
    reports: list[dict] = []
    consecutive_failures = 0
    for seed in ordered_seeds(profile):
        if len(by_page) >= maximum:
            break
        try:
            rows = category_members(seed)
            consecutive_failures = 0
            qids = sum(1 for row in rows if row.wikidata_qid)
            reports.append({"category": seed.category, "status": "ok", "pages": len(rows), "qids": qids, "group": seed.group})
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            consecutive_failures += 1
            reports.append({"category": seed.category, "status": "deferred", "error": str(exc)[:180], "group": seed.group})
            if consecutive_failures % FAILURE_COOLDOWN_EVERY == 0:
                time.sleep(FAILURE_COOLDOWN_SECONDS)
            if consecutive_failures >= MAX_CONSECUTIVE_CATEGORY_FAILURES:
                break
            continue
        for row in rows:
            by_page.setdefault(row.page_id, []).append(row)
            if len(by_page) >= maximum:
                break
        time.sleep(REQUEST_DELAY_SECONDS)
    return by_page, reports


def captured_qids(by_page: dict[int, list[Discovery]]) -> dict[int, str]:
    resolved: dict[int, str] = {}
    for page_id, rows in by_page.items():
        for row in rows:
            if row.wikidata_qid:
                resolved[page_id] = row.wikidata_qid
                break
    return resolved


def chunks(values: list[int], size: int):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def resolve_qids(page_ids: list[int]) -> tuple[dict[int, str], list[dict]]:
    """Fallback resolver for only the pages missing a QID during discovery."""
    resolved: dict[int, str] = {}
    reports: list[dict] = []
    consecutive_failures = 0
    for batch_index, batch in enumerate(chunks(page_ids, PAGEPROP_BATCH)):
        try:
            payload = base.request_json(
                base.ENWIKI_API,
                {
                    "action": "query",
                    "prop": "pageprops",
                    "ppprop": "wikibase_item",
                    "pageids": "|".join(str(value) for value in batch),
                    "format": "json",
                    "formatversion": "2",
                    "origin": "*",
                },
                post=True,
            )
            found = 0
            for page in payload.get("query", {}).get("pages", []):
                page_id = int(page.get("pageid") or 0)
                qid = str(page.get("pageprops", {}).get("wikibase_item") or "").strip()
                if page_id > 0 and qid.startswith("Q"):
                    resolved[page_id] = qid
                    found += 1
            consecutive_failures = 0
            reports.append({"batch": batch_index, "status": "ok", "requested": len(batch), "resolved": found})
        except Exception as exc:
            consecutive_failures += 1
            reports.append({"batch": batch_index, "status": "deferred", "requested": len(batch), "error": str(exc)[:180]})
            if consecutive_failures % 3 == 0:
                time.sleep(FAILURE_COOLDOWN_SECONDS)
        time.sleep(QID_FALLBACK_DELAY_SECONDS)
    return resolved, reports


def merge_discoveries(by_page: dict[int, list[Discovery]], qids: dict[int, str]) -> list[dict]:
    movies: list[dict] = []
    for page_id, discoveries in by_page.items():
        years = sorted({item.release_year for item in discoveries})
        release_year = years[0]
        countries = sorted({item.country_code for item in discoveries if item.country_code})
        languages = sorted({item.language for item in discoveries if item.language})
        country_code = "IN" if "IN" in countries else (countries[0] if countries else "XX")
        language = languages[0] if len(languages) == 1 else ("Unknown" if not languages else languages[0])
        title = discoveries[0].title
        qid = qids.get(page_id)
        movies.append(
            {
                "id": f"wd-{qid}" if qid else f"enwiki-{page_id}",
                "wikidata_qid": qid,
                "wikipedia_page_id": page_id,
                "title": title,
                "release_year": release_year,
                "observed_release_years": years,
                "date_precision": "year",
                "language": language,
                "languages": languages,
                "country_code": country_code,
                "country_codes": countries,
                "source_category": discoveries[0].category,
                "source_categories": sorted({item.category for item in discoveries}),
                "source_url": f"https://en.wikipedia.org/?curid={page_id}",
                "verification_status": "unconfirmed",
            }
        )
    movies.sort(key=lambda item: (-item["release_year"], item["title"].casefold(), item["id"]))
    return movies


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(movies: list[dict]) -> str:
    statements = ["-- Wikipedia-native year-precision catalogue discovery; exact-day movies are untouched."]
    for movie in movies:
        statements.append(
            "INSERT INTO catalogue_titles "
            "(id, wikidata_qid, wikipedia_page_id, title, release_year, date_precision, language_name, country_code, source_category, source_url, verification_status, updated_at) VALUES ("
            f"{sql_quote(movie['id'])}, {sql_quote(movie.get('wikidata_qid'))}, {int(movie['wikipedia_page_id'])}, "
            f"{sql_quote(movie['title'])}, {int(movie['release_year'])}, 'year', {sql_quote(movie['language'])}, "
            f"{sql_quote(movie['country_code'])}, {sql_quote(movie['source_category'])}, {sql_quote(movie['source_url'])}, 'unconfirmed', CURRENT_TIMESTAMP) "
            "ON CONFLICT DO UPDATE SET "
            "wikidata_qid=COALESCE(excluded.wikidata_qid, catalogue_titles.wikidata_qid), "
            "title=excluded.title, release_year=excluded.release_year, language_name=CASE WHEN catalogue_titles.language_name='Unknown' THEN excluded.language_name ELSE catalogue_titles.language_name END, "
            "country_code=CASE WHEN excluded.country_code='IN' THEN 'IN' WHEN catalogue_titles.country_code='XX' THEN excluded.country_code ELSE catalogue_titles.country_code END, "
            "source_category=excluded.source_category, source_url=excluded.source_url, updated_at=CURRENT_TIMESTAMP;"
        )
    return "\n".join(statements) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch broad year-precision movie catalogue from Wikipedia categories")
    parser.add_argument("--profile", choices=("bootstrap", "india", "global-recent", "rotate", "all-historical"), default="global-recent")
    parser.add_argument("--max-titles", type=int, default=MAX_TITLES_PER_RUN)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--sql-out", type=Path, default=Path("data/generated/wikipedia-year-catalogue-upsert.sql"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_TITLES_PER_RUN, args.max_titles))
    by_page, category_reports = discover(args.profile, maximum)
    if not by_page:
        print("No Wikipedia catalogue pages discovered.")
        return 1

    qids = captured_qids(by_page)
    missing_page_ids = [page_id for page_id in by_page if page_id not in qids]
    fallback_qids, qid_reports = resolve_qids(missing_page_ids) if missing_page_ids else ({}, [])
    qids.update(fallback_qids)
    movies = merge_discoveries(by_page, qids)[:maximum]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile": args.profile,
                "source": "english_wikipedia_categories",
                "date_precision": "year",
                "max_titles_per_run": maximum,
                "selection_policy": "Wikipedia year/category membership only; stable page identity; QID captured from Wikipedia pageprops during discovery when available; no invented day/month",
                "category_report": category_reports,
                "qid_resolution_report": qid_reports,
                "movies": movies,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    args.sql_out.parent.mkdir(parents=True, exist_ok=True)
    args.sql_out.write_text(build_sql(movies), encoding="utf-8")
    native_count = len(captured_qids(by_page))
    print(
        f"Wikipedia year catalogue wrote {len(movies)} title(s); "
        f"{len(qids)} have Wikidata QIDs ({native_count} captured during discovery); exact-day release table untouched"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
