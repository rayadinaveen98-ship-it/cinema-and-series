#!/usr/bin/env python3
"""Build a broad SeriesRun catalogue from English Wikipedia categories.

Series Engine V1 intentionally keeps episodic works separate from movie rows.
Discovery uses strong series-shaped Wikipedia categories and captures stable
Wikipedia page IDs plus Wikidata QIDs in the same MediaWiki request. Year is
stored only when the source category explicitly encodes a debut year; static
language/web/miniseries categories do not invent a first-air date.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import fetch_mediawiki_backfill as base

OUT = Path("data/generated/wikipedia-series-catalogue.json")
MAX_SERIES_PER_RUN = 3500
CATEGORY_PAGE_CAP = 220
REQUEST_DELAY_SECONDS = 0.40
MAX_CONSECUTIVE_FAILURES = 35
FAILURE_COOLDOWN_EVERY = 5
FAILURE_COOLDOWN_SECONDS = 8


@dataclass(frozen=True)
class Seed:
    category: str
    country_code: str
    language: str | None
    series_kind: str
    group: str
    first_air_year: int | None = None


@dataclass(frozen=True)
class Discovery:
    page_id: int
    qid: str | None
    title: str
    country_code: str
    language: str | None
    series_kind: str
    category: str
    first_air_year: int | None


INDIA_LANGUAGES = (
    ("Hindi", "Hindi-language television shows"),
    ("Telugu", "Telugu-language television shows"),
    ("Tamil", "Tamil-language television shows"),
    ("Malayalam", "Malayalam-language television shows"),
    ("Kannada", "Kannada-language television shows"),
    ("Bengali", "Bengali-language television shows"),
    ("Marathi", "Marathi-language television shows"),
    ("Punjabi", "Punjabi-language television shows"),
)

INDIA_WEB_LANGUAGES = (
    ("Hindi", "Hindi-language web series"),
    ("Telugu", "Telugu-language web series"),
    ("Tamil", "Tamil-language web series"),
    ("Malayalam", "Malayalam-language web series"),
    ("Bengali", "Bengali-language web series"),
)

COUNTRY_DEBUT_SUFFIXES = (
    ("IN", "Indian television series debuts"),
    ("US", "American television series debuts"),
    ("GB", "British television series debuts"),
    ("KR", "South Korean television series debuts"),
    ("JP", "Japanese television series debuts"),
    ("CN", "Chinese television series debuts"),
    ("CA", "Canadian television series debuts"),
    ("AU", "Australian television series debuts"),
    ("FR", "French television series debuts"),
    ("DE", "German television series debuts"),
    ("ES", "Spanish television series debuts"),
    ("BR", "Brazilian television series debuts"),
    ("MX", "Mexican television series debuts"),
    ("TR", "Turkish television series debuts"),
    ("PK", "Pakistani television series debuts"),
    ("BD", "Bangladeshi television series debuts"),
)

STATIC_WEB_CATEGORIES = (
    ("IN", None, "Indian web series"),
    ("US", None, "American web series"),
    ("GB", None, "British web series"),
    ("KR", None, "South Korean web series"),
)

MINISERIES_CATEGORIES = (
    ("IN", "Indian television miniseries"),
    ("US", "American television miniseries"),
    ("GB", "British television miniseries"),
    ("AU", "Australian television miniseries"),
    ("CA", "Canadian television miniseries"),
)

KIND_PRIORITY = {"unknown": 0, "series": 1, "anthology": 2, "web_series": 3, "miniseries": 4}


def _year_range_desc(start: int, end: int) -> range:
    return range(end, start - 1, -1)


def build_seeds(profile: str, today: date | None = None) -> list[Seed]:
    current = today or date.today()
    seeds: list[Seed] = []

    if profile in {"bootstrap", "india"}:
        for language, suffix in INDIA_LANGUAGES:
            seeds.append(Seed(f"Category:{suffix}", "IN", language, "series", f"india-{language}"))
        for language, suffix in INDIA_WEB_LANGUAGES:
            seeds.append(Seed(f"Category:{suffix}", "IN", language, "web_series", f"india-web-{language}"))
        seeds.append(Seed("Category:Indian web series", "IN", None, "web_series", "india-web"))
        for code, suffix in MINISERIES_CATEGORIES[:1]:
            seeds.append(Seed(f"Category:{suffix}", code, None, "miniseries", f"miniseries-{code}"))

    if profile in {"bootstrap", "global-recent"}:
        start_year = 2010 if profile == "bootstrap" else 2015
        for year in _year_range_desc(start_year, current.year):
            for code, suffix in COUNTRY_DEBUT_SUFFIXES:
                seeds.append(Seed(f"Category:{year} {suffix}", code, None, "series", f"debut-{code}", year))
        for code, language, suffix in STATIC_WEB_CATEGORIES:
            seeds.append(Seed(f"Category:{suffix}", code, language, "web_series", f"web-{code}"))
        for code, suffix in MINISERIES_CATEGORIES:
            seeds.append(Seed(f"Category:{suffix}", code, None, "miniseries", f"miniseries-{code}"))

    if profile in {"rotate", "all-historical"}:
        if profile == "all-historical":
            years = list(_year_range_desc(1950, 2009))
        else:
            historical = list(_year_range_desc(1950, 2009))
            offset = max(0, (current - date(2026, 9, 16)).days) * 4
            years = [historical[(offset + index) % len(historical)] for index in range(4)]
        for year in years:
            for code, suffix in COUNTRY_DEBUT_SUFFIXES:
                seeds.append(Seed(f"Category:{year} {suffix}", code, None, "series", f"historical-{code}", year))

    if not seeds:
        raise ValueError(f"unknown profile: {profile}")
    return seeds


def _looks_like_series_page(title: str) -> bool:
    lowered = title.casefold().strip()
    if not lowered or lowered.startswith("list of "):
        return False
    if lowered.startswith("list of episodes") or lowered.startswith("episodes of "):
        return False
    if re.search(r"\bseason\s+\d+\b", lowered):
        return False
    if re.search(r"\bseries\s+\d+\b", lowered):
        return False
    return True


def category_members(seed: Seed, cap: int = CATEGORY_PAGE_CAP) -> list[Discovery]:
    rows: list[Discovery] = []
    continuation: str | None = None
    while len(rows) < cap:
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": seed.category,
            "gcmnamespace": "0",
            "gcmtype": "page",
            "gcmlimit": str(min(100, cap - len(rows))),
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
            if page_id <= 0 or not _looks_like_series_page(title):
                continue
            qid = str(page.get("pageprops", {}).get("wikibase_item") or "").strip() or None
            if qid and not qid.startswith("Q"):
                qid = None
            rows.append(
                Discovery(
                    page_id=page_id,
                    qid=qid,
                    title=title,
                    country_code=seed.country_code,
                    language=seed.language,
                    series_kind=seed.series_kind,
                    category=seed.category,
                    first_air_year=seed.first_air_year,
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
    failures = 0
    group_buckets: dict[str, list[Seed]] = {}
    for seed in build_seeds(profile):
        group_buckets.setdefault(seed.group, []).append(seed)
    groups = [values for _, values in sorted(group_buckets.items())]
    positions = [0] * len(groups)

    while len(by_page) < maximum and groups:
        progressed = False
        for index, group in enumerate(groups):
            if positions[index] >= len(group):
                continue
            seed = group[positions[index]]
            positions[index] += 1
            progressed = True
            try:
                rows = category_members(seed)
                failures = 0
                reports.append({"category": seed.category, "status": "ok", "pages": len(rows), "group": seed.group})
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
                failures += 1
                reports.append({"category": seed.category, "status": "deferred", "error": str(exc)[:180], "group": seed.group})
                if failures % FAILURE_COOLDOWN_EVERY == 0:
                    time.sleep(FAILURE_COOLDOWN_SECONDS)
                if failures >= MAX_CONSECUTIVE_FAILURES:
                    return by_page, reports
                continue
            for row in rows:
                by_page.setdefault(row.page_id, []).append(row)
                if len(by_page) >= maximum:
                    break
            time.sleep(REQUEST_DELAY_SECONDS)
            if len(by_page) >= maximum:
                break
        if not progressed:
            break
    return by_page, reports


def merge_discoveries(by_page: dict[int, list[Discovery]]) -> list[dict]:
    rows: list[dict] = []
    for page_id, discoveries in by_page.items():
        qids = sorted({item.qid for item in discoveries if item.qid})
        qid = qids[0] if qids else None
        years = sorted({item.first_air_year for item in discoveries if item.first_air_year is not None})
        countries = sorted({item.country_code for item in discoveries if item.country_code})
        languages = sorted({item.language for item in discoveries if item.language})
        kinds = sorted({item.series_kind for item in discoveries}, key=lambda value: KIND_PRIORITY.get(value, 0), reverse=True)
        country_code = "IN" if "IN" in countries else (countries[0] if countries else "XX")
        language = languages[0] if languages else "Unknown"
        title = discoveries[0].title
        rows.append(
            {
                "id": f"series-wd-{qid}" if qid else f"series-enwiki-{page_id}",
                "wikidata_qid": qid,
                "wikipedia_page_id": page_id,
                "title": title,
                "series_kind": kinds[0] if kinds else "unknown",
                "language": language,
                "languages": languages,
                "country_code": country_code,
                "country_codes": countries,
                "first_air_year": years[0] if years else None,
                "observed_first_air_years": years,
                "lifecycle_status": "unknown",
                "source_category": discoveries[0].category,
                "source_categories": sorted({item.category for item in discoveries}),
                "source_url": f"https://en.wikipedia.org/?curid={page_id}",
                "verification_status": "unconfirmed",
            }
        )
    rows.sort(key=lambda item: (-(item["first_air_year"] or 0), item["title"].casefold(), item["id"]))
    return rows


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(series: list[dict]) -> str:
    statements = ["-- Wikipedia-native SeriesRun discovery; movie tables are intentionally untouched."]
    for item in series:
        first_year = "NULL" if item.get("first_air_year") is None else str(int(item["first_air_year"]))
        statements.append(
            "INSERT INTO series_titles "
            "(id, wikidata_qid, wikipedia_page_id, title, series_kind, language_name, country_code, first_air_year, lifecycle_status, source_category, source_url, verification_status, updated_at) VALUES ("
            f"{sql_quote(item['id'])}, {sql_quote(item.get('wikidata_qid'))}, {int(item['wikipedia_page_id'])}, {sql_quote(item['title'])}, "
            f"{sql_quote(item['series_kind'])}, {sql_quote(item['language'])}, {sql_quote(item['country_code'])}, {first_year}, 'unknown', "
            f"{sql_quote(item['source_category'])}, {sql_quote(item['source_url'])}, 'unconfirmed', CURRENT_TIMESTAMP) "
            "ON CONFLICT DO UPDATE SET "
            "wikidata_qid=COALESCE(series_titles.wikidata_qid, excluded.wikidata_qid), "
            "title=excluded.title, "
            "series_kind=CASE WHEN series_titles.series_kind IN ('unknown','series') AND excluded.series_kind NOT IN ('unknown','series') THEN excluded.series_kind ELSE series_titles.series_kind END, "
            "language_name=CASE WHEN series_titles.language_name='Unknown' THEN excluded.language_name ELSE series_titles.language_name END, "
            "country_code=CASE WHEN excluded.country_code='IN' THEN 'IN' WHEN series_titles.country_code='XX' THEN excluded.country_code ELSE series_titles.country_code END, "
            "first_air_year=CASE WHEN series_titles.first_air_year IS NULL THEN excluded.first_air_year WHEN excluded.first_air_year IS NULL THEN series_titles.first_air_year ELSE MIN(series_titles.first_air_year, excluded.first_air_year) END, "
            "source_category=excluded.source_category, source_url=excluded.source_url, updated_at=CURRENT_TIMESTAMP;"
        )
    return "\n".join(statements) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch broad SeriesRun catalogue from Wikipedia categories")
    parser.add_argument("--profile", choices=("bootstrap", "india", "global-recent", "rotate", "all-historical"), default="bootstrap")
    parser.add_argument("--max-series", type=int, default=MAX_SERIES_PER_RUN)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--sql-out", type=Path, default=Path("data/generated/wikipedia-series-catalogue-upsert.sql"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_SERIES_PER_RUN, args.max_series))
    by_page, category_report = discover(args.profile, maximum)
    if not by_page:
        print("No Wikipedia series pages discovered.")
        return 1
    series = merge_discoveries(by_page)[:maximum]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile": args.profile,
                "source": "english_wikipedia_series_categories",
                "identity_policy": "SeriesRun identity; stable Wikipedia page ID; Wikidata QID captured in discovery request when available; franchise lineage remains separate",
                "date_policy": "first_air_year only when an explicit debut-year category supports it; no invented day/month",
                "max_series_per_run": maximum,
                "category_report": category_report,
                "series": series,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    args.sql_out.parent.mkdir(parents=True, exist_ok=True)
    args.sql_out.write_text(build_sql(series), encoding="utf-8")
    qid_count = sum(1 for item in series if item.get("wikidata_qid"))
    year_count = sum(1 for item in series if item.get("first_air_year") is not None)
    print(f"Wikipedia series catalogue wrote {len(series)} SeriesRun title(s); {qid_count} with QIDs; {year_count} with explicit first-air year")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
