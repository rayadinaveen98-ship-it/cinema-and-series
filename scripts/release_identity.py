#!/usr/bin/env python3
"""Conservative movie-title identity helpers for release-signal dedupe.

Dedupe is intentionally stricter than discovery. A release signal is considered
already curated only when the official source, release date, and a movie title
all agree. Matching by source + date alone is unsafe because one studio may
announce more than one title for the same release day.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_identity_text(value: str | None) -> str:
    """Return a Unicode-aware, punctuation-insensitive identity string."""
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    normalized = re.sub(r"[\W_]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def title_in_text(title: str | None, text: str | None) -> bool:
    """Require the normalized movie title as a whole-token phrase in text."""
    needle = normalize_identity_text(title)
    haystack = normalize_identity_text(text)
    if not needle or not haystack:
        return False
    return f" {needle} " in f" {haystack} "


def verified_titles_by_source_date(releases_payload: dict) -> dict[str, dict[str, set[str]]]:
    """Index verified movie titles by first-party source and release date."""
    known: dict[str, dict[str, set[str]]] = {}
    for release in releases_payload.get("releases", []):
        if release.get("verification_status") != "verified":
            continue
        source_key = release.get("source_key")
        release_date = release.get("release_date")
        title = release.get("title")
        if source_key and release_date and title:
            known.setdefault(source_key, {}).setdefault(release_date, set()).add(title)
    return known


def candidate_identity_text(candidate: dict, fields: tuple[str, ...]) -> str:
    parts: list[str] = []
    for field in fields:
        value = candidate.get(field)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value if item)
    return " ".join(parts)


def candidate_matches_verified_release(
    candidate: dict,
    release_date: str,
    known: dict[str, dict[str, set[str]]],
    identity_fields: tuple[str, ...],
) -> bool:
    """Return True only for a same-source/date candidate naming the same movie."""
    source_key = candidate.get("source_key", "")
    titles = known.get(source_key, {}).get(release_date, set())
    if not titles:
        return False
    text = candidate_identity_text(candidate, identity_fields)
    return any(title_in_text(title, text) for title in titles)
