#!/usr/bin/env python3
"""Fetch an India-focused film release seed from Wikidata.

WDQS is used only as a scheduled acquisition tool, never as a live application
runtime dependency. The query intentionally orders newest dates first so future
releases cannot be crowded out by older rows when the source result is capped.

The public WDQS can throttle aggressively during incidents. We prefer the
current main-graph endpoint, respect ordinary 429 cooldowns, and fall back to
the legacy public hostname for ordinary endpoint/network failures. When WDQS
asks for a cooldown longer than this scheduled job can safely accommodate, we
defer acquisition immediately and preserve the existing D1 catalogue instead of
sleeping until CI is cancelled.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ENDPOINTS = (
    "https://query-main.wikidata.org/sparql",
    "https://query.wikidata.org/sparql",
)
OUT = Path("data/generated/wikidata-india.json")
USER_AGENT = "CinemaAndSeries/0.1 (public GitHub project; Wikidata acquisition)"
INDIA_QID = "Q668"
QUERY_LIMIT = 3000
RATE_LIMIT_FALLBACK_SECONDS = 65
MAX_INLINE_COOLDOWN_SECONDS = 90
MAX_ATTEMPTS = 4


class WikidataDeferred(RuntimeError):
    """The public service asked us to defer this scheduled acquisition."""


def tracked_years() -> list[int]:
    year = date.today().year
    return list(range(year - 1, year + 3))


def query_text() -> str:
    years = tracked_years()
    return f'''SELECT ?item ?itemLabel ?date ?language ?languageLabel ?place WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q11424;
        wdt:P495 wd:Q668;
        p:P577 ?releaseStatement.
  ?releaseStatement ps:P577 ?date;
                    psv:P577 ?releaseNode.
  ?releaseNode wikibase:timePrecision ?precision.
  FILTER(?precision >= 11)
  FILTER(YEAR(?date) >= {years[0]} && YEAR(?date) <= {years[-1]})
  OPTIONAL {{ ?releaseStatement pq:P291 ?place. }}
  OPTIONAL {{ ?item wdt:P364 ?language. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,te,ta,ml,kn,hi,bn,mr,gu,pa". }}
}}
ORDER BY DESC(?date) ?item
LIMIT {QUERY_LIMIT}'''


def fetch(endpoint: str = ENDPOINTS[0]) -> dict:
    params = urllib.parse.urlencode({"query": query_text(), "format": "json"})
    request = urllib.request.Request(
        f"{endpoint}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def retry_after_seconds(error: urllib.error.HTTPError) -> int:
    raw = error.headers.get("Retry-After") if error.headers else None
    if raw:
        try:
            return max(RATE_LIMIT_FALLBACK_SECONDS, int(raw))
        except ValueError:
            pass
    return RATE_LIMIT_FALLBACK_SECONDS


def fetch_with_resilience() -> dict:
    """Fetch while respecting public-service throttling without stalling CI."""
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        endpoint = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            return fetch(endpoint)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                delay = retry_after_seconds(exc)
                if delay > MAX_INLINE_COOLDOWN_SECONDS:
                    raise WikidataDeferred(
                        f"WDQS requested a {delay}s cooldown via {endpoint}; deferring to a later scheduled refresh"
                    ) from exc
                print(
                    f"WDQS rate-limited request via {endpoint}; respecting {delay}s cooldown",
                    file=sys.stderr,
                )
                if attempt + 1 < MAX_ATTEMPTS:
                    time.sleep(delay)
                continue
            if attempt + 1 < MAX_ATTEMPTS:
                time.sleep(min(8, 2 ** attempt))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 < MAX_ATTEMPTS:
                time.sleep(min(8, 2 ** attempt))
    assert last_error is not None
    raise last_error


def _qid(url: str | None) -> str | None:
    if not url:
        return None
    return url.rsplit("/", 1)[-1]


def normalize(payload: dict) -> list[dict]:
    by_item: dict[str, dict] = {}

    for row in payload.get("results", {}).get("bindings", []):
        qid = _qid(row.get("item", {}).get("value"))
        raw_date = row.get("date", {}).get("value", "")[:10]
        if not qid or len(raw_date) != 10:
            continue

        item = by_item.setdefault(
            qid,
            {
                "title": row.get("itemLabel", {}).get("value", qid),
                "languages": set(),
                "dates": {},
            },
        )

        label = row.get("languageLabel", {}).get("value")
        if label:
            item["languages"].add(label)

        place_qid = _qid(row.get("place", {}).get("value"))
        date_entry = item["dates"].setdefault(raw_date, {"places": set()})
        if place_qid:
            date_entry["places"].add(place_qid)

    movies: list[dict] = []
    for qid, item in by_item.items():
        dates = item["dates"]
        india_dates = sorted(
            release_date
            for release_date, metadata in dates.items()
            if INDIA_QID in metadata["places"]
        )
        all_dates = sorted(dates)
        if not all_dates:
            continue

        if india_dates:
            selected = india_dates[-1]
            selection_reason = "india_qualified_latest"
        else:
            selected = all_dates[-1]
            selection_reason = "latest_open_data_candidate"

        movies.append(
            {
                "wikidata_qid": qid,
                "title": item["title"],
                "release_date": selected,
                "candidate_dates": all_dates,
                "languages": sorted(item["languages"]),
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
                "verification_status": "unconfirmed",
                "selection_reason": selection_reason,
            }
        )

    return sorted(movies, key=lambda x: (x["release_date"], x["title"].casefold(), x["wikidata_qid"]))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        items = normalize(fetch_with_resilience())
        OUT.write_text(
            json.dumps(
                {
                    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "selection_policy": "scheduled Wikidata acquisition; prefer India-qualified P577; otherwise latest day-precision candidate; all remain unconfirmed until stronger evidence",
                    "tracked_years": tracked_years(),
                    "movies": items,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {len(items)} unique film release candidates to {OUT}")
        return 0
    except WikidataDeferred as exc:
        print(f"Wikidata acquisition deferred: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # public source resilience
        print(f"Wikidata acquisition failed after rate-aware retries: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
