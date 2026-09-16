#!/usr/bin/env python3
"""Poll registered official YouTube channels for release-date announcement candidates.

The monitor intentionally does not auto-verify dates. It uses the official
YouTube Data API to read each registered channel's uploads playlist, extracts
explicit date phrases only when release-oriented context is present, and emits
reviewable candidates for D1. Sources may be registered by stable channel ID or
by an official @handle; handle-only entries are resolved through channels.list.

To keep the live review queue useful, only recent uploads are considered,
candidate dates must be today-or-future at scan time, candidate dates cannot
precede the upload date, and response/review promotional videos are excluded.
Short evidence excerpts are preserved in the generated review artifact so a
human can see why a date matched without storing full video descriptions.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGISTRY = Path("data/official/source_registry.json")
OUT_JSON = Path("data/generated/youtube-release-candidates.json")
OUT_SQL = Path("data/generated/youtube-candidates-upsert.sql")
API_ROOT = "https://www.googleapis.com/youtube/v3"
MAX_UPLOAD_AGE_DAYS = 45
MAX_RELEASE_LAG_DAYS = 0
MAX_RELEASE_LEAD_DAYS = 1095
CONTEXT_RADIUS = 110

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
RELEASE_CONTEXT = re.compile(
    r"\b(release|releasing|releases|worldwide|cinema|cinemas|theatre|theatres|theater|theaters|in theatres|in cinemas|from)\b",
    re.IGNORECASE,
)
LOW_VALUE_PROMO = re.compile(
    r"\b(public|audience|fan|fans)?\s*(response|responses|reaction|reactions|review|reviews)\b|"
    r"\bsuccess\s*(meet|party|celebration|celebrations)\b",
    re.IGNORECASE,
)
DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*,?\s*(20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b"),
]
PARTIAL_DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b", re.IGNORECASE),
    re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\b", re.IGNORECASE),
]
YEAR_TOKEN = re.compile(r"\b20\d{2}\b")
YEAR_INFERENCE_PATTERNS = [
    re.compile(r"\b(?:upcoming|coming|releasing|release(?:s|d)?|arriving)\s+(?:in\s+)?(20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(20\d{2})\s+(?:release|releases|theatrical\s+release|film|movie)\b", re.IGNORECASE),
]


def api_get(resource: str, params: dict[str, str]) -> dict:
    params = {**params, "key": os.environ["YOUTUBE_API_KEY"]}
    url = f"{API_ROOT}/{resource}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "CinemaAndSeries/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def parse_date(match: re.Match[str]) -> str | None:
    groups = match.groups()
    try:
        if groups[0].isalpha():
            month = MONTHS[groups[0].casefold()]
            day = int(groups[1])
            year = int(groups[2])
        elif groups[1].isalpha():
            day = int(groups[0])
            month = MONTHS[groups[1].casefold()]
            year = int(groups[2])
        else:
            day, month, year = map(int, groups)
        return datetime(year, month, day).date().isoformat()
    except (KeyError, ValueError):
        return None


def parse_partial_date(match: re.Match[str], year: int) -> str | None:
    groups = match.groups()
    try:
        if groups[0].isalpha():
            month = MONTHS[groups[0].casefold()]
            day = int(groups[1])
        else:
            day = int(groups[0])
            month = MONTHS[groups[1].casefold()]
        return datetime(year, month, day).date().isoformat()
    except (KeyError, ValueError):
        return None


def _clean_excerpt(value: str) -> str:
    return " ".join(value.split()).strip()


def infer_release_year(text: str) -> tuple[int, str] | None:
    """Infer one release year only from explicit future/release wording.

    A bare year, upload timestamp, copyright notice, or channel boilerplate is
    never enough. The complete title+description must contain exactly one 20xx
    year, and that same year must participate in wording such as "Upcoming
    2026", "release 2026", or "2026 release". This deliberately rejects
    ambiguous metadata that mentions multiple years.
    """
    all_years = {int(match.group(0)) for match in YEAR_TOKEN.finditer(text)}
    if len(all_years) != 1:
        return None
    only_year = next(iter(all_years))

    for pattern in YEAR_INFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            matched_year = int(match.group(1))
            if matched_year != only_year:
                continue
            start = max(0, match.start() - CONTEXT_RADIUS)
            end = min(len(text), match.end() + CONTEXT_RADIUS)
            return only_year, _clean_excerpt(text[start:end])
    return None


def extract_release_date_contexts(text: str) -> list[dict[str, str]]:
    """Return explicit or safely completed release dates with evidence excerpts.

    Full day-level dates are preferred. A month/day phrase without a year is
    accepted only when ``infer_release_year`` can prove one unambiguous release
    year from the same official upload metadata. Multiple syntactic mentions of
    the same date collapse to one item.
    """
    contexts: dict[str, str] = {}
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            start = max(0, match.start() - CONTEXT_RADIUS)
            end = min(len(text), match.end() + CONTEXT_RADIUS)
            window = text[start:end]
            if not RELEASE_CONTEXT.search(window):
                continue
            parsed = parse_date(match)
            if not parsed:
                continue
            excerpt = _clean_excerpt(window)
            previous = contexts.get(parsed)
            if previous is None or len(excerpt) < len(previous):
                contexts[parsed] = excerpt

    inferred = infer_release_year(text)
    if inferred:
        inferred_year, year_excerpt = inferred
        for pattern in PARTIAL_DATE_PATTERNS:
            for match in pattern.finditer(text):
                start = max(0, match.start() - CONTEXT_RADIUS)
                end = min(len(text), match.end() + CONTEXT_RADIUS)
                window = text[start:end]
                if not RELEASE_CONTEXT.search(window):
                    continue
                parsed = parse_partial_date(match, inferred_year)
                if not parsed:
                    continue
                excerpt = _clean_excerpt(window)
                if str(inferred_year) not in excerpt:
                    excerpt = _clean_excerpt(f"{excerpt} | year context: {year_excerpt}")[:420]
                previous = contexts.get(parsed)
                if previous is None or len(excerpt) < len(previous):
                    contexts[parsed] = excerpt

    return [{"date": value, "excerpt": contexts[value]} for value in sorted(contexts)]


def extract_release_dates(text: str) -> list[str]:
    return [item["date"] for item in extract_release_date_contexts(text)]


def is_low_value_promo(title: str) -> bool:
    return bool(LOW_VALUE_PROMO.search(title))


def parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def filter_plausible_release_dates(
    dates: list[str],
    published_at: str | None,
    now: datetime | None = None,
) -> list[str]:
    published = parse_published_at(published_at)
    if not published:
        return []

    reference_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if published < reference_now - timedelta(days=MAX_UPLOAD_AGE_DAYS):
        return []

    lower = max(
        published.date() - timedelta(days=MAX_RELEASE_LAG_DAYS),
        reference_now.date(),
    )
    upper = published.date() + timedelta(days=MAX_RELEASE_LEAD_DAYS)
    plausible: list[str] = []
    for value in dates:
        try:
            candidate = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            continue
        if lower <= candidate <= upper:
            plausible.append(value)
    return plausible


def esc(value: str) -> str:
    return value.replace("'", "''")


def sql_value(value: str | None) -> str:
    return "NULL" if value is None else f"'{esc(value)}'"


def _uploads_from_channel(channel: dict) -> str | None:
    return channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")


def resolve_upload_playlists(sources: list[dict]) -> dict[str, dict[str, str]]:
    """Return source_key -> {channel_id, uploads_playlist_id}.

    Known channel IDs are resolved in batches. Handle-only sources use
    channels.list(forHandle=...), which is the official API path and avoids
    guessing opaque channel IDs.
    """
    resolved: dict[str, dict[str, str]] = {}
    by_channel_id = {
        source["youtube_channel_id"]: source
        for source in sources
        if source.get("youtube_channel_id")
    }
    ids = list(by_channel_id)

    for offset in range(0, len(ids), 50):
        chunk = ids[offset:offset + 50]
        payload = api_get("channels", {"part": "contentDetails", "id": ",".join(chunk), "maxResults": "50"})
        for channel in payload.get("items", []):
            channel_id = channel.get("id")
            uploads = _uploads_from_channel(channel)
            source = by_channel_id.get(channel_id)
            if source and channel_id and uploads:
                resolved[source["key"]] = {"channel_id": channel_id, "uploads_playlist_id": uploads}

    for source in sources:
        if source["key"] in resolved or source.get("youtube_channel_id") or not source.get("youtube_handle"):
            continue
        handle = source["youtube_handle"].lstrip("@")
        payload = api_get("channels", {"part": "contentDetails", "forHandle": handle, "maxResults": "1"})
        items = payload.get("items", [])
        if not items:
            print(f"warning: YouTube handle could not be resolved for {source['name']}: @{handle}", file=sys.stderr)
            continue
        channel = items[0]
        channel_id = channel.get("id")
        uploads = _uploads_from_channel(channel)
        if channel_id and uploads:
            resolved[source["key"]] = {"channel_id": channel_id, "uploads_playlist_id": uploads}

    return resolved


def fetch_latest_uploads(
    source: dict,
    channel_id: str,
    playlist_id: str,
    now: datetime | None = None,
) -> list[dict]:
    payload = api_get(
        "playlistItems",
        {"part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": "50"},
    )
    candidates: list[dict] = []
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("contentDetails", {}).get("videoId") or snippet.get("resourceId", {}).get("videoId")
        if not video_id:
            continue
        title = snippet.get("title", "").strip()
        if is_low_value_promo(title):
            continue
        description = snippet.get("description", "").strip()
        published_at = snippet.get("publishedAt")
        combined_text = f"{title}\n{description}"
        date_contexts = extract_release_date_contexts(combined_text)
        dates = filter_plausible_release_dates(
            [item["date"] for item in date_contexts],
            published_at,
            now=now,
        )
        if not dates:
            continue
        retained_dates = set(dates)
        date_contexts = [item for item in date_contexts if item["date"] in retained_dates]
        candidates.append({
            "source_key": source["key"],
            "source_name": source["name"],
            "channel_id": channel_id,
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "video_title": title,
            "published_at": published_at,
            "candidate_dates": dates,
            "candidate_release_date": dates[0] if len(dates) == 1 else None,
            "date_contexts": date_contexts,
            "status": "pending_review",
        })
    return candidates


def sources_for_candidates(candidates: list[dict], sources: list[dict]) -> list[dict]:
    source_keys = {candidate.get("source_key") for candidate in candidates if candidate.get("source_key")}
    if not source_keys:
        return []
    return [source for source in sources if source.get("key") in source_keys]


def build_sql(candidates: list[dict], sources: list[dict] | None = None) -> str:
    """Build an idempotent, FK-safe sync batch for retained observations."""
    statements: list[str] = []

    for source in sources or []:
        statements.append(
            "INSERT INTO source_channels "
            "(source_key, source_name, source_type, website_url, youtube_channel_id, youtube_handle, active, updated_at) "
            f"VALUES ('{esc(source['key'])}','{esc(source['name'])}','{esc(source.get('source_type') or 'official_channel')}',"
            f"{sql_value(source.get('website_url'))},{sql_value(source.get('youtube_channel_id'))},{sql_value(source.get('youtube_handle'))},"
            f"{1 if source.get('active', True) else 0},CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "source_name=excluded.source_name, source_type=excluded.source_type, website_url=excluded.website_url, "
            "youtube_channel_id=excluded.youtube_channel_id, youtube_handle=excluded.youtube_handle, "
            "active=excluded.active, updated_at=CURRENT_TIMESTAMP;"
        )

    for candidate in candidates:
        candidate_dates = json.dumps(candidate["candidate_dates"], ensure_ascii=False)
        date_value = "NULL" if not candidate.get("candidate_release_date") else f"'{esc(candidate['candidate_release_date'])}'"
        published = candidate.get("published_at")
        published_value = "NULL" if not published else f"'{esc(published)}'"
        statements.append(
            "INSERT INTO source_observations "
            "(source_key, external_id, external_url, title, published_at, candidate_release_date, candidate_dates_json, review_status, observed_at) "
            f"VALUES ('{esc(candidate['source_key'])}','{esc(candidate['video_id'])}','{esc(candidate['video_url'])}',"
            f"'{esc(candidate['video_title'])}',{published_value},{date_value},'{esc(candidate_dates)}','pending_review',CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key, external_id) DO UPDATE SET "
            "external_url=excluded.external_url, title=excluded.title, published_at=excluded.published_at, "
            "candidate_release_date=excluded.candidate_release_date, candidate_dates_json=excluded.candidate_dates_json, "
            "observed_at=CURRENT_TIMESTAMP;"
        )
    return "\n".join(statements) + ("\n" if statements else "")


def main() -> int:
    if not os.environ.get("YOUTUBE_API_KEY"):
        print("YOUTUBE_API_KEY is not configured; official YouTube monitoring skipped.")
        return 0

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = [
        source for source in registry.get("sources", [])
        if source.get("active") and (source.get("youtube_channel_id") or source.get("youtube_handle"))
    ]
    resolved = resolve_upload_playlists(sources)
    candidates: list[dict] = []
    channels_checked = 0
    scan_time = datetime.now(timezone.utc)
    for source in sources:
        channel = resolved.get(source["key"])
        if not channel:
            print(f"warning: uploads playlist not found for {source['name']}", file=sys.stderr)
            continue
        channels_checked += 1
        candidates.extend(
            fetch_latest_uploads(
                source,
                channel["channel_id"],
                channel["uploads_playlist_id"],
                now=scan_time,
            )
        )

    candidates.sort(key=lambda item: (item.get("published_at") or "", item["source_key"], item["video_id"]), reverse=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "generated_at": scan_time.isoformat(),
                "policy": "official-channel observations only; recent non-response/review uploads with explicit or safely completed day-level release dates that are still today-or-future become pending review candidates; yearless dates require one unambiguous release-year phrase in the same upload metadata; short local date context is preserved for human review; never auto-verify",
                "channels_registered": len(sources),
                "channels_checked": channels_checked,
                "candidates": candidates,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    OUT_SQL.write_text(build_sql(candidates, sources_for_candidates(candidates, sources)), encoding="utf-8")
    print(f"checked {channels_checked}/{len(sources)} official channels and found {len(candidates)} future-facing release-date candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
