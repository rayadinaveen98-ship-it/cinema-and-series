#!/usr/bin/env python3
"""Conservative movie-title identity helpers for release-signal dedupe.

Dedupe is intentionally stricter than discovery. Same-source release signals are
considered already curated only when source, release date, and movie title all
agree. Cross-source corroboration is also suppressible when a different
registered first-party source names the exact same *distinctive* movie title on
the exact same date. Date-only matching is never sufficient.
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


def title_is_distinctive(title: str | None) -> bool:
    """Return True only for titles safe enough for cross-source corroboration.

    Multi-word titles are considered distinctive once they carry meaningful
    normalized text. Single-word titles must be at least eight characters so
    short/generic names such as KING cannot silently cross-dedupe independent
    projects from different studios.
    """
    normalized = normalize_identity_text(title)
    if not normalized:
        return False
    tokens = normalized.split()
    if len(tokens) >= 2:
        return len(normalized.replace(" ", "")) >= 6
    return len(tokens[0]) >= 8


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
    """Return True for an identity-safe same-movie/date verified occurrence.

    Same-source matching accepts any exact normalized movie title. Cross-source
    matching is deliberately narrower: the exact date must match and the movie
    title must be distinctive enough to avoid generic-title collisions.
    """
    source_key = candidate.get("source_key", "")
    if not source_key:
        return False

    text = candidate_identity_text(candidate, identity_fields)
    same_source_titles = known.get(source_key, {}).get(release_date, set())
    if any(title_in_text(title, text) for title in same_source_titles):
        return True

    for verified_source_key, dates in known.items():
        if verified_source_key == source_key:
            continue
        for title in dates.get(release_date, set()):
            if title_is_distinctive(title) and title_in_text(title, text):
                return True
    return False
