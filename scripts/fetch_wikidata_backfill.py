#!/usr/bin/env python3
"""Sharded Wikidata backfill for a large global film catalogue.

This is intentionally separate from the fast India/upcoming refresh. It is a
slow accumulation lane for historical/general catalogue breadth. Queries are
partitioned by country groups and year windows so the public Wikidata Query
Service is not asked for one enormous result set.

Backfill rows remain unconfirmed discovery data. The SQL layer preserves any
existing verified/supported date and, for historical rows, keeps the earliest
day-precision Wikidata date observed across independently fetched shards.

To stay friendly to both WDQS and Cloudflare D1 Free, each run imports at most
5,000 unique movies. Bootstrap output is balanced across successful shards;
scheduled rotation pages through shards over time rather than repeatedly
returning only the first page.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

ENDPOINTS = (
    "https://query-main.wikidata.org/sparql",
    "https://query.wikidata.org/sparql",
)
OUT = Path("data/generated/wikidata-backfill.json")
USER_AGENT = "CinemaAndSeries/0.2 (public GitHub project; sharded Wikidata catalogue backfill)"
QUERY_LIMIT = 5000
MAX_ATTEMPTS_PER_SHARD = 3
MAX_INLINE_COOLDOWN_SECONDS = 45
INTER_SHARD_DELAY_SECONDS = 2
MAX_MOVIES_PER_RUN = 5000
ROTATION_SHARDS_PER_RUN = 2
ROTATION_PAGE_CYCLE = 8
ROTATION_ANCHOR = date(2026, 9, 16)


@dataclass(frozen=True)
class Country:
    qid: str
    code: str
    label: str


@dataclass(frozen=True)
class Shard:
    key: str
    start_year: int
    end_year: int
    countries: tuple[Country, ...]
    page: int = 0


INDIA = Country("Q668", "IN", "India")
ASIA = (
    Country("Q884", "KR", "South Korea"),
    Country("Q17", "JP", "Japan"),
    Country("Q148", "CN", "China"),
    Country("Q8646", "HK", "Hong Kong"),
    Country("Q865", "TW", "Taiwan"),
    Country("Q252", "ID", "Indonesia"),
    Country("Q869", "TH", "Thailand"),
    Country("Q928", "PH", "Philippines"),
    Country("Q843", "PK", "Pakistan"),
    Country("Q902", "BD", "Bangladesh"),
    Country("Q854", "LK", "Sri Lanka"),
    Country("Q837", "NP", "Nepal"),
)
WEST = (
    Country("Q30", "US", "United States"),
    Country("Q145", "GB", "United Kingdom"),
    Country("Q16", "CA", "Canada"),
    Country("Q408", "AU", "Australia"),
    Country("Q664", "NZ", "New Zealand"),
    Country("Q142", "FR", "France"),
    Country("Q183", "DE", "Germany"),
    Country("Q38", "IT", "Italy"),
    Country("Q29", "ES", "Spain"),
)
OTHER = (
    Country("Q155", "BR", "Brazil"),
    Country("Q96", "MX", "Mexico"),
    Country("Q414", "AR", "Argentina"),
    Country("Q43", "TR", "Turkey"),
    Country("Q794", "IR", "Iran"),
    Country("Q1033", "NG", "Nigeria"),
    Country("Q79", "EG", "Egypt"),
)

INDIA_SHARDS = (
    Shard("india-1910-1949", 1910, 1949, (INDIA,)),
    Shard("india-1950-1969", 1950, 1969, (INDIA,)),
    Shard("india-1970-1989", 1970, 1989, (INDIA,)),
    Shard("india-1990-2004", 1990, 2004, (INDIA,)),
    Shard("india-2005-2014", 2005, 2014, (INDIA,)),
    Shard("india-2015-2024", 2015, 2024, (INDIA,)),
)
GLOBAL_RECENT_SHARDS = (
    Shard("asia-2015-2024", 2015, 2024, ASIA),
    Shard("west-2015-2024", 2015, 2024, WEST),
    Shard("other-2015-2024", 2015, 2024, OTHER),
)
HISTORICAL_SHARDS = (
    Shard("asia-1950-1979", 1950, 1979, ASIA),
    Shard("west-1950-1979", 1950, 1979, WEST),
    Shard("other-1950-1979", 1950, 1979, OTHER),
    Shard("asia-1980-1999", 1980, 1999, ASIA),
    Shard("west-1980-1999", 1980, 1999, WEST),
    Shard("other-1980-1999", 1980, 1999, OTHER),
    Shard("asia-2000-2014", 2000, 2014, ASIA),
    Shard("west-2000-2014", 2000, 2014, WEST),
    Shard("other-2000-2014", 2000, 2014, OTHER),
)
ROTATION_SHARDS = GLOBAL_RECENT_SHARDS + HISTORICAL_SHARDS


def selected_shards(profile: str, today: date | None = None) -> tuple[Shard, ...]:
    if profile == "india":
        return INDIA_SHARDS
    if profile == "global-recent":
        return GLOBAL_RECENT_SHARDS
    if profile == "bootstrap":
        return INDIA_SHARDS + GLOBAL_RECENT_SHARDS
    if profile == "all-historical":
        return HISTORICAL_SHARDS
    if profile == "rotate":
        current = today or date.today()
        elapsed = max(0, (current - ROTATION_ANCHOR).days)
        absolute_slot = elapsed * ROTATION_SHARDS_PER_RUN
        selected: list[Shard] = []
        for offset in range(ROTATION_SHARDS_PER_RUN):
            slot = absolute_slot + offset
            shard_index = slot % len(ROTATION_SHARDS)
            page = (slot // len(ROTATION_SHARDS)) % ROTATION_PAGE_CYCLE
            selected.append(replace(ROTATION_SHARDS[shard_index], page=page))
        return tuple(selected)
    raise ValueError(f"unknown profile: {profile}")


def query_text(shard: Shard) -> str:
    country_values = " ".join(f"wd:{country.qid}" for country in shard.countries)
    offset = shard.page * QUERY_LIMIT
    return f'''SELECT ?item ?itemLabel ?date ?language ?languageLabel ?country ?countryLabel WHERE {{
  VALUES ?country {{ {country_values} }}
  ?item wdt:P31/wdt:P279* wd:Q11424;
        wdt:P495 ?country;
        p:P577 ?releaseStatement.
  ?releaseStatement ps:P577 ?date;
                    psv:P577 ?releaseNode.
  ?releaseNode wikibase:timePrecision ?precision.
  FILTER(?precision >= 11)
  FILTER(YEAR(?date) >= {shard.start_year} && YEAR(?date) <= {shard.end_year})
  OPTIONAL {{ ?item wdt:P364 ?language. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,te,ta,ml,kn,hi,bn,mr,gu,pa,ko,ja,zh,fr,de,it,es,pt,tr,fa,id,th". }}
}}
ORDER BY ?item ?date
LIMIT {QUERY_LIMIT}
OFFSET {offset}'''


def request_payload(shard: Shard, endpoint: str) -> dict:
    params = urllib.parse.urlencode({"query": query_text(shard), "format": "json"})
    request = urllib.request.Request(
        f"{endpoint}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(request, timeout=75) as response:
        return json.load(response)


def retry_after_seconds(error: urllib.error.HTTPError) -> int:
    raw = error.headers.get("Retry-After") if error.headers else None
    if raw:
        try:
            return max(5, int(raw))
        except ValueError:
            pass
    return 20


def fetch_shard(shard: Shard) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS_PER_SHARD):
        endpoint = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            return request_payload(shard, endpoint)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                delay = retry_after_seconds(exc)
                if delay > MAX_INLINE_COOLDOWN_SECONDS:
                    break
                if attempt + 1 < MAX_ATTEMPTS_PER_SHARD:
                    time.sleep(delay)
                continue
            if attempt + 1 < MAX_ATTEMPTS_PER_SHARD:
                time.sleep(min(8, 2 ** attempt))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 < MAX_ATTEMPTS_PER_SHARD:
                time.sleep(min(8, 2 ** attempt))
    assert last_error is not None
    raise last_error


def entity_qid(url: str | None) -> str | None:
    if not url:
        return None
    return url.rsplit("/", 1)[-1]


def normalize(shard_payloads: list[tuple[Shard, dict]]) -> list[dict]:
    country_codes = {
        country.qid: country.code
        for shard, _ in shard_payloads
        for country in shard.countries
    }
    by_item: dict[str, dict] = {}

    for _, payload in shard_payloads:
        for row in payload.get("results", {}).get("bindings", []):
            qid = entity_qid(row.get("item", {}).get("value"))
            raw_date = row.get("date", {}).get("value", "")[:10]
            if not qid or len(raw_date) != 10:
                continue

            item = by_item.setdefault(
                qid,
                {
                    "title": row.get("itemLabel", {}).get("value", qid),
                    "languages": set(),
                    "dates": set(),
                    "country_codes": set(),
                    "countries": set(),
                },
            )
            label = row.get("languageLabel", {}).get("value")
            if label:
                item["languages"].add(label)
            item["dates"].add(raw_date)

            country_qid = entity_qid(row.get("country", {}).get("value"))
            if country_qid and country_qid in country_codes:
                item["country_codes"].add(country_codes[country_qid])
            country_label = row.get("countryLabel", {}).get("value")
            if country_label:
                item["countries"].add(country_label)

    movies: list[dict] = []
    for qid, item in by_item.items():
        dates = sorted(item["dates"])
        if not dates:
            continue
        codes = sorted(item["country_codes"])
        movies.append(
            {
                "wikidata_qid": qid,
                "title": item["title"],
                "release_date": dates[0],
                "candidate_dates": dates,
                "languages": sorted(item["languages"]),
                "country_code": "IN" if "IN" in codes else (codes[0] if codes else "XX"),
                "country_codes": codes,
                "countries": sorted(item["countries"]),
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
                "verification_status": "unconfirmed",
                "selection_reason": "earliest_day_precision_open_data_candidate",
                "merge_strategy": "earliest",
            }
        )

    return sorted(movies, key=lambda item: (item["release_date"], item["title"].casefold(), item["wikidata_qid"]))


def balanced_selection(successful: list[tuple[Shard, dict]], maximum: int) -> list[dict]:
    """Round-robin successful shards so one huge market cannot consume the run."""
    per_shard = [normalize([(shard, payload)]) for shard, payload in successful]
    positions = [0] * len(per_shard)
    selected: list[dict] = []
    seen: set[str] = set()

    while len(selected) < maximum:
        progressed = False
        for index, movies in enumerate(per_shard):
            while positions[index] < len(movies):
                movie = movies[positions[index]]
                positions[index] += 1
                qid = movie["wikidata_qid"]
                if qid in seen:
                    continue
                seen.add(qid)
                selected.append(movie)
                progressed = True
                break
            if len(selected) >= maximum:
                break
        if not progressed:
            break
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch sharded Wikidata catalogue backfill")
    parser.add_argument(
        "--profile",
        choices=("bootstrap", "india", "global-recent", "rotate", "all-historical"),
        default="rotate",
    )
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--max-movies", type=int, default=MAX_MOVIES_PER_RUN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_MOVIES_PER_RUN, args.max_movies))
    shards = selected_shards(args.profile)
    successful: list[tuple[Shard, dict]] = []
    reports: list[dict] = []

    for index, shard in enumerate(shards):
        try:
            payload = fetch_shard(shard)
            bindings = payload.get("results", {}).get("bindings", [])
            successful.append((shard, payload))
            reports.append(
                {
                    "key": shard.key,
                    "page": shard.page,
                    "status": "ok",
                    "start_year": shard.start_year,
                    "end_year": shard.end_year,
                    "countries": [country.code for country in shard.countries],
                    "raw_bindings": len(bindings),
                    "possibly_truncated": len(bindings) >= QUERY_LIMIT,
                }
            )
            print(f"{shard.key} page {shard.page}: fetched {len(bindings)} bindings")
        except Exception as exc:
            reports.append(
                {
                    "key": shard.key,
                    "page": shard.page,
                    "status": "deferred",
                    "start_year": shard.start_year,
                    "end_year": shard.end_year,
                    "countries": [country.code for country in shard.countries],
                    "error": str(exc)[:240],
                }
            )
            print(f"{shard.key} page {shard.page}: deferred ({exc})", file=sys.stderr)
        if index + 1 < len(shards):
            time.sleep(INTER_SHARD_DELAY_SECONDS)

    if not successful:
        print("No Wikidata backfill shards succeeded; preserving existing D1 catalogue.", file=sys.stderr)
        return 1

    movies = balanced_selection(successful, maximum)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile": args.profile,
                "merge_strategy": "earliest",
                "max_movies_per_run": maximum,
                "selection_policy": "sharded historical/global Wikidata discovery; day precision only; balanced across successful shards; earliest candidate retained; never overrides verified/supported dates",
                "shards": reports,
                "movies": movies,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {len(movies)} unique backfill movies from {len(successful)}/{len(shards)} successful shards "
        f"(run cap {maximum})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
