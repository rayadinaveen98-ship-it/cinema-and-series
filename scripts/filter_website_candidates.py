#!/usr/bin/env python3
"""Remove already-curated first-party dates from website-monitor candidates.

The website crawler is intentionally broad enough to rediscover dates that are
already present in data/official/releases.json. Dedupe must remain identity-safe:
a date is suppressed only when the same first-party source already has that date
verified for a movie title explicitly present in the page candidate. Source +
date alone is not sufficient because one studio may announce multiple films for
the same release day.
"""
from __future__ import annotations

import json
from pathlib import Path

from release_identity import candidate_matches_verified_release, verified_titles_by_source_date
from website_monitor import build_sql

CANDIDATES = Path("data/generated/website-release-candidates.json")
RELEASES = Path("data/official/releases.json")
REGISTRY = Path("data/official/source_registry.json")
OUT_SQL = Path("data/generated/website-candidates-upsert.sql")
IDENTITY_FIELDS = ("page_title", "review_title", "context_excerpts")


def filter_candidates(
    candidates: list[dict],
    known: dict[str, dict[str, set[str]]],
) -> tuple[list[dict], int]:
    filtered: list[dict] = []
    suppressed_dates = 0
    for candidate in candidates:
        original_dates = list(candidate.get("candidate_dates") or [])
        remaining_dates = [
            value
            for value in original_dates
            if not candidate_matches_verified_release(candidate, value, known, IDENTITY_FIELDS)
        ]
        suppressed_dates += len(original_dates) - len(remaining_dates)
        if not remaining_dates:
            continue
        item = dict(candidate)
        item["candidate_dates"] = remaining_dates
        item["candidate_release_date"] = remaining_dates[0] if len(remaining_dates) == 1 else None
        filtered.append(item)
    return filtered, suppressed_dates


def matching_sources(candidates: list[dict], registry_payload: dict) -> list[dict]:
    """Return only source rows needed by retained observations.

    An empty review queue must produce empty SQL so the workflow can truly skip
    D1 writes instead of touching every registered website source on each run.
    """
    source_keys = {candidate.get("source_key") for candidate in candidates if candidate.get("source_key")}
    if not source_keys:
        return []
    return [
        source for source in registry_payload.get("sources", [])
        if source.get("active") and source.get("website_url") and source.get("key") in source_keys
    ]


def main() -> int:
    candidates_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    releases_payload = json.loads(RELEASES.read_text(encoding="utf-8"))
    registry_payload = json.loads(REGISTRY.read_text(encoding="utf-8"))

    filtered, suppressed_dates = filter_candidates(
        candidates_payload.get("candidates", []),
        verified_titles_by_source_date(releases_payload),
    )
    candidates_payload["candidates"] = filtered
    candidates_payload["suppressed_known_verified_dates"] = suppressed_dates
    candidates_payload["policy"] = (
        "first-party websites only; explicit day-level release signals become pending review observations; "
        "a date is suppressed only when the same source/date candidate explicitly names the same verified movie; "
        "never auto-verify"
    )
    CANDIDATES.write_text(json.dumps(candidates_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sources = matching_sources(filtered, registry_payload)
    OUT_SQL.write_text(build_sql(filtered, sources), encoding="utf-8")
    print(
        f"website identity-safe dedupe kept {len(filtered)} observation(s) and suppressed "
        f"{suppressed_dates} already-verified same-movie date occurrence(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
