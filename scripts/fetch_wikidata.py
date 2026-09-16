#!/usr/bin/env python3
"""Fetch a small India-focused film release seed from Wikidata.

WDQS is used only as a scheduled acquisition tool, never as a live application
runtime dependency. We keep one display release candidate per Wikidata item:
India-qualified P577 dates win when present; otherwise the latest day-precision
candidate in the bounded window is retained and remains unconfirmed.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ENDPOINT = "https://query.wikidata.org/sparql"
OUT = Path("data/generated/wikidata-india.json")
USER_AGENT = "CinemaAndSeries/0.1 (public GitHub project; Wikidata acquisition)"
INDIA_QID = "Q668"


def query_text() -> str:
    year = date.today().year
    return f'''SELECT ?item ?itemLabel ?date ?language ?languageLabel ?place WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q11424;
        wdt:P495 wd:Q668;
        p:P577 ?releaseStatement.
  ?releaseStatement ps:P577 ?date;
                    psv:P577 ?releaseNode.
  ?releaseNode wikibase:timePrecision ?precision.
  FILTER(?precision >= 11)
  FILTER(YEAR(?date) >= {year - 1} && YEAR(?date) <= {year + 2})
  OPTIONAL {{ ?releaseStatement pq:P291 ?place. }}
  OPTIONAL {{ ?item wdt:P364 ?language. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,te,ta,ml,kn,hi,bn,mr,gu,pa". }}
}}
ORDER BY ?date ?item
LIMIT 2000'''


def fetch() -> dict:
    params = urllib.parse.urlencode({"query": query_text(), "format": "json"})
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


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
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            items = normalize(fetch())
            OUT.write_text(
                json.dumps(
                    {
                        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "selection_policy": "prefer India-qualified P577; otherwise latest day-precision candidate; all remain unconfirmed until stronger evidence",
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
        except Exception as exc:  # network/source resilience
            last_error = exc
            time.sleep(2**attempt)
    print(f"Wikidata acquisition failed after retries: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
