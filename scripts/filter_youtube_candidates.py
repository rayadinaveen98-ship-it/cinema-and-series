#!/usr/bin/env python3
"""Remove already-curated first-party dates from YouTube monitor candidates.

Official channels may repeat a release date across teasers, reminders, shorts,
and date-announcement videos. Once the same source/date is already curated in
``data/official/releases.json``, surfacing it again as pending review is noise.
This step keeps genuinely new dates, suppresses known verified occurrences,
and regenerates the D1 SQL only for retained observations.
"""
from __future__ import annotations

import json
from pathlib import Path

from youtube_monitor import build_sql, sources_for_candidates

CANDIDATES = Path("data/generated/youtube-release-candidates.json")
RELEASES = Path("data/official/releases.json")
REGISTRY = Path("data/official/source_registry.json")
OUT_SQL = Path("data/generated/youtube-candidates-upsert.sql")


def known_dates_by_source(releases_payload: dict) -> dict[str, set[str]]:
    known: dict[str, set[str]] = {}
    for release in releases_payload.get("releases", []):
        if release.get("verification_status") != "verified":
            continue
        source_key = release.get("source_key")
        release_date = release.get("release_date")
        if source_key and release_date:
            known.setdefault(source_key, set()).add(release_date)
    return known


def filter_candidates(candidates: list[dict], known: dict[str, set[str]]) -> tuple[list[dict], int]:
    filtered: list[dict] = []
    suppressed_dates = 0
    for candidate in candidates:
        existing = known.get(candidate.get("source_key", ""), set())
        original_dates = list(candidate.get("candidate_dates") or [])
        remaining_dates = [value for value in original_dates if value not in existing]
        suppressed_dates += len(original_dates) - len(remaining_dates)
        if not remaining_dates:
            continue
        item = dict(candidate)
        item["candidate_dates"] = remaining_dates
        item["candidate_release_date"] = remaining_dates[0] if len(remaining_dates) == 1 else None
        filtered.append(item)
    return filtered, suppressed_dates


def main() -> int:
    candidates_payload = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    releases_payload = json.loads(RELEASES.read_text(encoding="utf-8"))
    registry_payload = json.loads(REGISTRY.read_text(encoding="utf-8"))

    filtered, suppressed_dates = filter_candidates(
        candidates_payload.get("candidates", []),
        known_dates_by_source(releases_payload),
    )
    candidates_payload["candidates"] = filtered
    candidates_payload["suppressed_known_verified_dates"] = suppressed_dates
    candidates_payload["policy"] = (
        "official-channel observations only; future-facing release signals become pending review; "
        "dates already verified from the same source are suppressed; never auto-verify"
    )
    CANDIDATES.write_text(json.dumps(candidates_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    active_youtube_sources = [
        source for source in registry_payload.get("sources", [])
        if source.get("active") and (source.get("youtube_channel_id") or source.get("youtube_handle"))
    ]
    OUT_SQL.write_text(
        build_sql(filtered, sources_for_candidates(filtered, active_youtube_sources)),
        encoding="utf-8",
    )
    print(
        f"youtube candidate dedupe kept {len(filtered)} observation(s) and suppressed "
        f"{suppressed_dates} already-verified date occurrence(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
