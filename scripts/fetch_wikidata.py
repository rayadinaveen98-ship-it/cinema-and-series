#!/usr/bin/env python3
"""Fetch a small India-focused film release seed from Wikidata.

This deliberately uses WDQS only as a scheduled acquisition tool, never as a live app dependency.
Only day-precision P577 statements are emitted. Output is deterministic JSON for review/import.
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


def query_text() -> str:
    year = date.today().year
    return f'''SELECT ?item ?itemLabel ?date ?language ?languageLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:Q11424;
        wdt:P495 wd:Q668;
        p:P577 ?releaseStatement.
  ?releaseStatement psv:P577 ?releaseNode.
  ?releaseNode wikibase:timeValue ?date;
               wikibase:timePrecision ?precision.
  FILTER(?precision >= 11)
  FILTER(YEAR(?date) >= {year - 1} && YEAR(?date) <= {year + 2})
  OPTIONAL {{ ?item wdt:P364 ?language. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,te,ta,ml,kn,hi,bn,mr,gu,pa". }}
}}
ORDER BY ?date ?item
LIMIT 1500'''


def fetch() -> dict:
    params = urllib.parse.urlencode({"query": query_text(), "format": "json"})
    request = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def normalize(payload: dict) -> list[dict]:
    merged: dict[tuple[str, str], dict] = {}
    for row in payload.get("results", {}).get("bindings", []):
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        raw_date = row["date"]["value"][:10]
        key = (qid, raw_date)
        entry = merged.setdefault(key, {
            "wikidata_qid": qid,
            "title": row.get("itemLabel", {}).get("value", qid),
            "release_date": raw_date,
            "languages": [],
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
            "verification_status": "unconfirmed",
        })
        label = row.get("languageLabel", {}).get("value")
        if label and label not in entry["languages"]:
            entry["languages"].append(label)
    return sorted(merged.values(), key=lambda x: (x["release_date"], x["title"].casefold(), x["wikidata_qid"]))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            items = normalize(fetch())
            OUT.write_text(json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "movies": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"wrote {len(items)} release candidates to {OUT}")
            return 0
        except Exception as exc:  # network/source resilience
            last_error = exc
            time.sleep(2 ** attempt)
    print(f"Wikidata acquisition failed after retries: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
