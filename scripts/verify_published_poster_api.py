#!/usr/bin/env python3
"""Acceptance gate: each newly published VRT poster must appear in live movie API.

No D1 queries or writes. Uses the signed-off publication report produced by
the same workflow, and an always-unique cache key to avoid stale catalogue data.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ORIGIN = "https://cinema-and-series.rayadinaveen98.workers.dev"
QID = re.compile(r"Q[1-9][0-9]*\Z")


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "CinemaAndSeries-PermissionedPoster-Acceptance/1.0",
    })
    with urllib.request.urlopen(req, timeout=22) as response:
        if response.status != 200:
            raise ValueError("public API returned non-200")
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("public API returned malformed JSON")
    return data


def verify_film(item: dict, payload: dict) -> dict:
    if payload.get("source") != "d1":
        raise ValueError("public film response is not backed by production D1")
    candidates = payload.get("movies")
    if not isinstance(candidates, list):
        raise ValueError("public film response lacks movies array")
    ids = item["source_ids"]
    if not isinstance(ids, list) or not ids:
        raise ValueError("no existing film record verified")
    qids = {v["qid"] for v in ids}
    if len(qids) != 1 or not all(QID.fullmatch(str(q)) for q in qids):
        raise ValueError("film identity ambiguity in D1 proof")
    qid = next(iter(qids))
    matching = [movie for movie in candidates if movie.get("wikidataQid") == qid
                and str(movie.get("title") or "").casefold().strip()
                == str(item["title"]).casefold().strip()]
    if not matching:
        raise ValueError("exact verified film identity missing from public API")
    expected_source = item["source_url"]
    expected_poster = item["delivery_url"]
    expected_license = str(item["license"]).rstrip("/")
    errors = []
    for movie in matching:
        # The film can legitimately be represented by an exact-date or a
        # year-only table record. Every published linked representation must work.
        linked_id = {x["id"] for x in ids}
        if movie.get("id") not in linked_id:
            continue
        poster_url = str(movie.get("posterUrl") or "")
        credited = str(movie.get("artworkAttribution") or "")
        license_url = str(movie.get("artworkLicenseUrl") or "")
        if (poster_url != expected_poster or movie.get("artworkSource") != "wikimedia_commons_vrt"
            or movie.get("artworkSourceUrl") != expected_source
            or license_url.rstrip("/") != expected_license
            or "CC BY-SA 4.0" not in credited or item["ticket"] not in credited):
            errors.append(str(movie.get("id")) + ": poster or provenance mismatch")
    visible_ids = {x.get("id") for x in matching}
    expected_ids = {x["id"] for x in ids}
    if not expected_ids.issubset(visible_ids):
        raise ValueError("API missing a verified database representation")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "title": item["title"], "year": item["year"],
        "wikidata_qid": qid, "linked_ids": sorted(expected_ids),
        "poster_displayed_in_api": True,
        "license": item["license"],
    }


def public_url(origin: str, item: dict, cache_nonce: str, attempt: int) -> str:
    query = urllib.parse.urlencode({
        "scope": "all", "q": item["title"], "year": item["year"],
        "limit": 100, "meta": 0,
        "artworkBatch02": f"{cache_nonce}-{attempt}-{item['ticket']}",
    })
    return origin.rstrip("/") + "/api/movies?" + query


def verify_all(report: dict, fetch=fetch_json, *,
               origin: str = ORIGIN, cache_nonce: str = "local",
               attempts: int = 3, delay_seconds: float = 2) -> dict:
    ready = report.get("ready")
    verified = report.get("verified_titles")
    if not isinstance(ready, list) or not isinstance(verified, list):
        raise ValueError("missing independent production D1 readback")
    if sorted(verified) != sorted(x["title"] for x in ready):
        raise ValueError("production D1 proof does not match selected films")
    if report.get("published") != len(ready):
        raise ValueError("unverified poster publication count")
    if not 1 <= attempts <= 5:
        raise ValueError("invalid bounded verification retry count")
    visible, held = [], []
    for item in ready:
        final_error = ""
        for attempt in range(attempts):
            url = public_url(origin, item, cache_nonce, attempt)
            try:
                actual = verify_film(item, fetch(url))
                visible.append(actual)
                final_error = ""
                break
            except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:
                final_error = str(exc)[:170]
                if attempt < attempts - 1 and delay_seconds:
                    time.sleep(delay_seconds)
        if final_error:
            held.append({"title": item["title"], "error": final_error})
    return {
        "schema": "permissioned-artwork-live-api-acceptance-v1",
        "published_in_d1": len(ready), "visible_in_public_api": len(visible),
        "verified": visible, "failed": held, "database_writes": 0,
        "test_origin": origin,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--nonce", default=os.getenv("GITHUB_RUN_ID") or "local")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    outcome = verify_all(report, cache_nonce=args.nonce)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LICENSED_POSTERS_VISIBLE_API=" + json.dumps(outcome, sort_keys=True), flush=True)
    if outcome["failed"] or outcome["visible_in_public_api"] != outcome["published_in_d1"]:
        raise SystemExit("Some newly published posters are not visible and attributed in public API")


if __name__ == "__main__":
    main()
