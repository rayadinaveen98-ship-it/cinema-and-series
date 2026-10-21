#!/usr/bin/env python3
"""Polite Wikimedia Action API GET client for one source-only artwork scan.

Respects Wikimedia's 2026 rate-limit guidance: identifying User-Agent,
serial requests, max 1 request/second, 429/503 Retry-After and backoff.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from urllib.parse import urlsplit

AGENT = ("CinemaAndSeries-Artwork/2.0 "
         "(https://github.com/rayadinaveen98-ship-it/cinema-and-series; "
         "contact: GitHub repository Issues)")
HOSTS = {
    "www.wikidata.org", "en.wikipedia.org", "te.wikipedia.org",
    "hi.wikipedia.org", "ta.wikipedia.org", "ml.wikipedia.org",
    "kn.wikipedia.org", "bn.wikipedia.org", "commons.wikimedia.org",
}
_last_request: float = 0.0


def retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return min(max(float(value), 5.0), 90.0)
        except ValueError:
            try:
                future = parsedate_to_datetime(value)
                return min(max((future - datetime.now(timezone.utc)).total_seconds(), 5.0), 90.0)
            except (TypeError, ValueError, OverflowError):
                pass
    return min(10.0 * (attempt + 1), 60.0)


def fetch(base: str, params: dict, *, sleep=time.sleep, clock=time.monotonic,
          open_url=urllib.request.urlopen, attempts: int = 3) -> dict:
    global _last_request
    uri = urlsplit(base)
    if uri.scheme != "https" or uri.hostname not in HOSTS or not uri.path.endswith("/w/api.php"):
        raise ValueError("Only original Wikimedia Action API endpoints are permitted")
    if not 1 <= attempts <= 4:
        raise ValueError("Invalid retry limit")
    url = base + "?" + urllib.parse.urlencode(params)
    for i in range(attempts):
        # One global serial fetch rate across Wikidata, Wikipedia and Commons.
        # The interval also applies to retries; no parallel fanout.
        remaining = 1.0 - (clock() - _last_request)
        if remaining > 0:
            sleep(remaining)
        _last_request = clock()
        req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
        try:
            with open_url(req, timeout=22) as response:
                payload = json.loads(response.read(4_000_000).decode("utf-8"))
            if not isinstance(payload, dict) or payload.get("error"):
                raise ValueError("Wikimedia Action API returned malformed/error JSON")
            return payload
        except urllib.error.HTTPError as error:
            print(f"WIKIMEDIA_HTTP_STATUS={error.code}; host={uri.hostname}; attempt={i+1}", flush=True)
            if error.code not in (429, 503) or i == attempts - 1:
                raise
            delay = retry_delay(error.headers.get("Retry-After"), i)
            print(f"WIKIMEDIA_RETRY_AFTER={delay:.0f}s (honoring provider limit)", flush=True)
            sleep(delay)
        except (TimeoutError, urllib.error.URLError) as error:
            print(f"WIKIMEDIA_NETWORK_ERROR={type(error).__name__}; host={uri.hostname}; attempt={i+1}",
                  flush=True)
            if i == attempts - 1:
                raise
            sleep(5.0 * (i + 1))
    raise RuntimeError("Unreachable: retry loop did not return")
