#!/usr/bin/env python3
"""Remove already-curated first-party dates from YouTube monitor candidates.

Official channels may repeat a release date across teasers, reminders, shorts,
and date-announcement videos. Dedupe must remain identity-safe: a date is
suppressed only when the same first-party source already has that date verified
for a movie title explicitly named in the candidate. Source + date alone is not
enough because one studio can release different movies on the same day.
"""
from __future__ import annotations

import json
from pathlib import Path

from release_identity import candidate_matches_verified_release, verified_titles_by_source_date
from youtube_monitor import build_sql, sources_for_candidates

CANDIDATES = Path("data/generated/youtube-release-candidates.json")
RELEASES = Path("data/official/releases.json")
REGISTRY = Path("data/official/source_registry.json")
OUT_SQL = Path("data/generated/youtube-candidates-upsert.sql")
IDENTITY_FIELDS = ("video_title",)


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
        "official-channel observations only; future-facing release signals become pending review; "
        "a date is suppressed only when the same source/date candidate explicitly names the same verified movie; "
        "never auto-verify"
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
        f"youtube identity-safe dedupe kept {len(filtered)} observation(s) and suppressed "
        f"{suppressed_dates} already-verified same-movie date occurrence(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
