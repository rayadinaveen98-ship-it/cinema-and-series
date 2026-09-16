#!/usr/bin/env python3
"""Outage-friendly paced entrypoint for the sharded WDQS catalogue fetcher.

During the September 2026 WDQS incident the service explicitly reports an
aggressive roughly one-request-per-minute limit. The normal fetcher keeps a
short inter-shard delay for healthy periods; this entrypoint reuses the exact
same query, normalization, identity and evidence policy while spacing shards
far enough apart for outage-mode catalogue accumulation.
"""
from __future__ import annotations

import os

import fetch_wikidata_backfill as base

DEFAULT_OUTAGE_DELAY_SECONDS = 65


def configure() -> int:
    raw = os.environ.get("WDQS_INTER_SHARD_DELAY_SECONDS", str(DEFAULT_OUTAGE_DELAY_SECONDS))
    try:
        delay = max(60, min(180, int(raw)))
    except ValueError:
        delay = DEFAULT_OUTAGE_DELAY_SECONDS
    base.INTER_SHARD_DELAY_SECONDS = delay
    # Pacing is the retry strategy here; avoid repeatedly hitting the same shard
    # inside a one-minute service window before moving to the next paced slot.
    base.MAX_ATTEMPTS_PER_SHARD = 1
    return delay


def main() -> int:
    delay = configure()
    print(f"WDQS outage pacing enabled: {delay}s between shards")
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
