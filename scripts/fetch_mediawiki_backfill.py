#!/usr/bin/env python3
"""MediaWiki/Wikibase fallback for broad film catalogue discovery.

The primary historical/global path uses WDQS because SPARQL is expressive, but
WDQS can enter aggressive outage rate-limiting. This fallback deliberately uses
normal Wikimedia Action APIs instead:

1. discover English Wikipedia film pages from year/language and year/country
   categories via `categorymembers`;
2. resolve page titles to Wikidata entities with `wbgetentities`;
3. keep only entities with a day-precision P577 release date;
4. emit the same backfill payload consumed by `wikidata_to_sql.py`.

This is catalogue discovery, not first-party verification. Every row remains
`unconfirmed`, uses a stable Wikidata QID, and is capped per run before D1 sync.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ENWIKI_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
OUT = Path("data/generated/wikidata-backfill.json")
USER_AGENT = "CinemaAndSeries/0.3 (public GitHub project; Wikimedia API catalogue fallback)"
MAX_MOVIES_PER_RUN = 5000
ENTITY_BATCH = 35
LABEL_BATCH = 50
CATEGORY_PAGE_CAP = 750
REQUEST_DELAY_SECONDS = 0.06
MAX_INLINE_RETRY_SECONDS = 30


@dataclass(frozen=True)
class Seed:
    category: str
    country_code: str
    language: str | None
    group: str


INDIA_LANGUAGES = (
    ("Hindi", "Hindi-language films"),
    ("Telugu", "Telugu-language films"),
    ("Tamil", "Tamil-language films"),
    ("Malayalam", "Malayalam-language films"),
    ("Kannada", "Kannada-language films"),
    ("Bengali", "Bengali-language films"),
    ("Marathi", "Marathi-language films"),
    ("Punjabi", "Punjabi-language films"),
)

COUNTRY_CATEGORIES = (
    ("US", "American films"),
    ("GB", "British films"),
    ("KR", "South Korean films"),
    ("JP", "Japanese films"),
    ("CN", "Chinese films"),
    ("HK", "Hong Kong films"),
    ("TW", "Taiwanese films"),
    ("CA", "Canadian films"),
    ("AU", "Australian films"),
    ("NZ", "New Zealand films"),
    ("FR", "French films"),
    ("DE", "German films"),
    ("IT", "Italian films"),
    ("ES", "Spanish films"),
    ("BR", "Brazilian films"),
    ("MX", "Mexican films"),
    ("AR", "Argentine films"),
    ("TR", "Turkish films"),
    ("IR", "Iranian films"),
    ("ID", "Indonesian films"),
    ("TH", "Thai films"),
    ("PH", "Philippine films"),
    ("PK", "Pakistani films"),
    ("BD", "Bangladeshi films"),
    ("LK", "Sri Lankan films"),
    ("NG", "Nigerian films"),
    ("EG", "Egyptian films"),
)


def year_range_desc(start: int, end: int) -> range:
    return range(end, start - 1, -1)


def build_seeds(profile: str, today: date | None = None) -> list[Seed]:
    current = today or date.today()
    seeds: list[Seed] = []

    if profile in {"bootstrap", "india"}:
        start = 1990 if profile == "bootstrap" else 1950
        for year in year_range_desc(start, 2024):
            for language, suffix in INDIA_LANGUAGES:
                seeds.append(Seed(f"Category:{year} {suffix}", "IN", language, f"india-{language}"))

    if profile in {"bootstrap", "global-recent"}:
        for year in year_range_desc(2015, 2024):
            for code, suffix in COUNTRY_CATEGORIES:
                seeds.append(Seed(f"Category:{year} {suffix}", code, None, f"country-{code}"))

    if profile in {"rotate", "all-historical"}:
        if profile == "all-historical":
            years = list(year_range_desc(1950, 2014))
        else:
            # A deterministic four-year historical slice per day. Over time this
            # walks the full 1950-2014 range without hammering Wikimedia APIs.
            historical_years = list(year_range_desc(1950, 2014))
            offset = max(0, (current - date(2026, 9, 16)).days) * 4
            years = [historical_years[(offset + index) % len(historical_years)] for index in range(4)]
        for year in years:
            for language, suffix in INDIA_LANGUAGES:
                seeds.append(Seed(f"Category:{year} {suffix}", "IN", language, f"india-{language}"))
            for code, suffix in COUNTRY_CATEGORIES:
                seeds.append(Seed(f"Category:{year} {suffix}", code, None, f"country-{code}"))

    if not seeds:
        raise ValueError(f"unknown profile: {profile}")
    return seeds


def request_json(endpoint: str, params: dict[str, str], *, post: bool = False) -> dict:
    encoded = urllib.parse.urlencode(params).encode("utf-8")
    url = endpoint if post else f"{endpoint}?{encoded.decode('utf-8')}"
    request = urllib.request.Request(
        url,
        data=encoded if post else None,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        method="POST" if post else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code != 429:
            raise
        raw = exc.headers.get("Retry-After") if exc.headers else None
        try:
            delay = int(raw) if raw else 5
        except ValueError:
            delay = 5
        if delay > MAX_INLINE_RETRY_SECONDS:
            raise
        time.sleep(max(2, delay))
        with urllib.request.urlopen(request, timeout=35) as response:
            return json.load(response)


def category_members(seed: Seed) -> list[str]:
    titles: list[str] = []
    continuation: str | None = None
    while len(titles) < CATEGORY_PAGE_CAP:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": seed.category,
            "cmnamespace": "0",
            "cmtype": "page",
            "cmlimit": "500",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        }
        if continuation:
            params["cmcontinue"] = continuation
        payload = request_json(ENWIKI_API, params)
        members = payload.get("query", {}).get("categorymembers", [])
        for member in members:
            title = str(member.get("title") or "").strip()
            if not title or title.lower().startswith("list of "):
                continue
            titles.append(title)
            if len(titles) >= CATEGORY_PAGE_CAP:
                break
        continuation = payload.get("continue", {}).get("cmcontinue")
        if not continuation:
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return titles


def discover_titles(seeds: list[Seed], maximum: int) -> tuple[list[str], dict[str, list[Seed]], list[dict]]:
    by_group: dict[str, list[str]] = {}
    metadata: dict[str, list[Seed]] = {}
    reports: list[dict] = []

    for seed in seeds:
        try:
            titles = category_members(seed)
            reports.append({"category": seed.category, "status": "ok", "pages": len(titles), "group": seed.group})
        except Exception as exc:
            reports.append({"category": seed.category, "status": "deferred", "error": str(exc)[:180], "group": seed.group})
            continue
        bucket = by_group.setdefault(seed.group, [])
        seen_bucket = set(bucket)
        for title in titles:
            metadata.setdefault(title, []).append(seed)
            if title not in seen_bucket:
                bucket.append(title)
                seen_bucket.add(title)
        time.sleep(REQUEST_DELAY_SECONDS)

    groups = [values for _, values in sorted(by_group.items()) if values]
    positions = [0] * len(groups)
    chosen: list[str] = []
    seen: set[str] = set()
    while len(chosen) < maximum and groups:
        progressed = False
        for index, titles in enumerate(groups):
            while positions[index] < len(titles):
                title = titles[positions[index]]
                positions[index] += 1
                if title in seen:
                    continue
                seen.add(title)
                chosen.append(title)
                progressed = True
                break
            if len(chosen) >= maximum:
                break
        if not progressed:
            break
    return chosen, metadata, reports


def chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def claim_time_dates(entity: dict) -> list[str]:
    dates: set[str] = set()
    for claim in entity.get("claims", {}).get("P577", []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not isinstance(value, dict) or int(value.get("precision") or 0) < 11:
            continue
        raw = str(value.get("time") or "")
        if len(raw) >= 11:
            candidate = raw.lstrip("+")[:10]
            if len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-":
                dates.add(candidate)
    return sorted(dates)


def item_ids(entity: dict, property_id: str) -> list[str]:
    values: set[str] = set()
    for claim in entity.get("claims", {}).get(property_id, []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, dict) and value.get("entity-type") == "item" and value.get("id"):
            values.add(str(value["id"]))
    return sorted(values)


def resolve_entities(titles: list[str]) -> list[dict]:
    entities: list[dict] = []
    for batch in chunks(titles, ENTITY_BATCH):
        payload = request_json(
            WIKIDATA_API,
            {
                "action": "wbgetentities",
                "sites": "enwiki",
                "titles": "|".join(batch),
                "props": "claims|labels|sitelinks",
                "languages": "en",
                "languagefallback": "1",
                "format": "json",
                "formatversion": "2",
            },
            post=True,
        )
        for entity in payload.get("entities", {}).values():
            if isinstance(entity, dict) and not entity.get("missing") and str(entity.get("id") or "").startswith("Q"):
                entities.append(entity)
        time.sleep(REQUEST_DELAY_SECONDS)
    return entities


def fetch_labels(qids: set[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    values = sorted(qids)
    for batch in chunks(values, LABEL_BATCH):
        payload = request_json(
            WIKIDATA_API,
            {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "labels",
                "languages": "en",
                "languagefallback": "1",
                "format": "json",
                "formatversion": "2",
            },
            post=True,
        )
        for qid, entity in payload.get("entities", {}).items():
            label = entity.get("labels", {}).get("en", {}).get("value") if isinstance(entity, dict) else None
            if label:
                labels[str(qid)] = str(label)
        time.sleep(REQUEST_DELAY_SECONDS)
    return labels


def entity_title(entity: dict) -> str:
    sitelink = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
    if sitelink:
        return str(sitelink)
    label = entity.get("labels", {}).get("en", {}).get("value")
    return str(label or entity.get("id") or "")


def normalize_entities(entities: list[dict], metadata: dict[str, list[Seed]]) -> list[dict]:
    language_ids = {qid for entity in entities for qid in item_ids(entity, "P364")}
    language_labels = fetch_labels(language_ids) if language_ids else {}
    movies: list[dict] = []

    for entity in entities:
        qid = str(entity.get("id") or "")
        title = entity_title(entity).strip()
        dates = claim_time_dates(entity)
        if not qid or not title or title == qid or not dates:
            continue

        seeds = metadata.get(title, [])
        if not seeds:
            # MediaWiki can normalize page titles. Match a normalized underscore/
            # whitespace form as a conservative fallback.
            normalized = title.replace("_", " ").casefold()
            seeds = [seed for key, seed_list in metadata.items() if key.replace("_", " ").casefold() == normalized for seed in seed_list]
        country_codes = sorted({seed.country_code for seed in seeds if seed.country_code})
        seeded_languages = sorted({seed.language for seed in seeds if seed.language})
        claim_languages = [language_labels[qid_] for qid_ in item_ids(entity, "P364") if qid_ in language_labels]
        languages = seeded_languages or sorted(set(claim_languages)) or ["Unknown"]
        country_code = "IN" if "IN" in country_codes else (country_codes[0] if country_codes else "XX")

        movies.append(
            {
                "wikidata_qid": qid,
                "title": title,
                "release_date": dates[0],
                "candidate_dates": dates,
                "languages": languages,
                "country_code": country_code,
                "country_codes": country_codes,
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
                "verification_status": "unconfirmed",
                "selection_reason": "mediawiki_category_discovery_earliest_day_precision_wikidata_date",
                "merge_strategy": "earliest",
            }
        )

    by_qid: dict[str, dict] = {}
    for movie in movies:
        existing = by_qid.get(movie["wikidata_qid"])
        if not existing:
            by_qid[movie["wikidata_qid"]] = movie
            continue
        existing["candidate_dates"] = sorted(set(existing["candidate_dates"]) | set(movie["candidate_dates"]))
        existing["release_date"] = existing["candidate_dates"][0]
        existing["languages"] = sorted(set(existing["languages"]) | set(movie["languages"]))
        existing["country_codes"] = sorted(set(existing["country_codes"]) | set(movie["country_codes"]))
        if "IN" in existing["country_codes"]:
            existing["country_code"] = "IN"

    return sorted(by_qid.values(), key=lambda item: (item["release_date"], item["title"].casefold(), item["wikidata_qid"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch broad film catalogue through Wikimedia Action APIs")
    parser.add_argument("--profile", choices=("bootstrap", "india", "global-recent", "rotate", "all-historical"), default="rotate")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--max-movies", type=int, default=MAX_MOVIES_PER_RUN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_MOVIES_PER_RUN, args.max_movies))
    seeds = build_seeds(args.profile)
    titles, metadata, reports = discover_titles(seeds, maximum)
    if not titles:
        print("No Wikipedia category film pages discovered; preserving existing catalogue.", file=sys.stderr)
        return 1

    try:
        entities = resolve_entities(titles)
        movies = normalize_entities(entities, metadata)[:maximum]
    except Exception as exc:
        print(f"Wikimedia entity resolution deferred: {exc}", file=sys.stderr)
        return 1

    if not movies:
        print("No day-precision Wikidata-backed films resolved from Wikipedia categories.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile": args.profile,
                "acquisition_path": "mediawiki_fallback",
                "merge_strategy": "earliest",
                "max_movies_per_run": maximum,
                "selection_policy": "Wikipedia year/language and year/country category discovery -> Wikidata entity resolution; day precision only; never overrides verified/supported dates",
                "category_report": reports,
                "discovered_page_titles": len(titles),
                "resolved_entities": len(entities),
                "movies": movies,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    successful_categories = sum(1 for report in reports if report.get("status") == "ok" and report.get("pages", 0) > 0)
    print(
        f"MediaWiki fallback wrote {len(movies)} unique movies from {len(titles)} discovered pages; "
        f"{successful_categories} populated categories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
