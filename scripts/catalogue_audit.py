#!/usr/bin/env python3
"""Audit scheduled catalogue inputs before they are allowed into D1.

Hard errors fail the refresh. Soft warnings are reported for review but do not
block useful open-data acquisition. This keeps the public catalogue resilient
without pretending Wikidata is perfectly curated.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

WIKIDATA = Path("data/generated/wikidata-india.json")
REGISTRY = Path("data/official/source_registry.json")
OFFICIAL_RELEASES = Path("data/official/releases.json")
QID_RE = re.compile(r"^Q\d+$")


def valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def norm_title(value: str) -> str:
    return " ".join(value.casefold().split())


def audit() -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = registry.get("sources", [])
    source_keys = [source.get("key") for source in sources]
    duplicate_source_keys = sorted(key for key, count in Counter(source_keys).items() if key and count > 1)
    if duplicate_source_keys:
        errors.append(f"duplicate source keys: {', '.join(duplicate_source_keys)}")

    for index, source in enumerate(sources):
        label = source.get("key") or f"source[{index}]"
        if not source.get("key") or not source.get("name") or not source.get("source_type"):
            errors.append(f"{label}: source identity fields are incomplete")
        if source.get("active") and not any(
            source.get(field) for field in ("website_url", "youtube_channel_id", "youtube_handle")
        ):
            errors.append(f"{label}: active source has no monitorable first-party endpoint")

    known_sources = set(key for key in source_keys if key)
    official = json.loads(OFFICIAL_RELEASES.read_text(encoding="utf-8"))
    releases = official.get("releases", [])
    official_identity_seen: set[tuple[str, str, str]] = set()
    for index, release in enumerate(releases):
        title = str(release.get("title") or "").strip()
        source_key = release.get("source_key")
        release_date = release.get("release_date")
        label = title or f"official_release[{index}]"
        if not title:
            errors.append(f"{label}: blank official title")
        if not valid_date(release_date):
            errors.append(f"{label}: invalid official release date {release_date!r}")
        if source_key not in known_sources:
            errors.append(f"{label}: unknown source_key {source_key!r}")
        if release.get("verification_status") != "verified":
            errors.append(f"{label}: curated first-party release must be verified")
        if not release.get("source_url"):
            errors.append(f"{label}: source_url missing")
        identity = (norm_title(title), str(release_date), str(source_key))
        if identity in official_identity_seen:
            errors.append(f"{label}: duplicate curated release row")
        official_identity_seen.add(identity)

    wikidata_movies: list[dict] = []
    if WIKIDATA.exists():
        wikidata = json.loads(WIKIDATA.read_text(encoding="utf-8"))
        wikidata_movies = wikidata.get("movies", [])
        qids: set[str] = set()
        title_date: Counter[tuple[str, str]] = Counter()
        unresolved = 0
        for index, movie in enumerate(wikidata_movies):
            qid = str(movie.get("wikidata_qid") or "")
            title = str(movie.get("title") or "").strip()
            release_date = movie.get("release_date")
            label = qid or f"wikidata_movie[{index}]"
            if not QID_RE.fullmatch(qid):
                errors.append(f"{label}: invalid Wikidata QID")
            if qid in qids:
                errors.append(f"{label}: duplicate Wikidata QID")
            qids.add(qid)
            if not title:
                errors.append(f"{label}: blank title")
            if not valid_date(release_date):
                errors.append(f"{label}: invalid release date {release_date!r}")
            if title == qid:
                unresolved += 1
            if title and valid_date(release_date):
                title_date[(norm_title(title), str(release_date))] += 1

        duplicate_title_dates = [key for key, count in title_date.items() if count > 1]
        if duplicate_title_dates:
            warnings.append(f"{len(duplicate_title_dates)} duplicate normalized title/date groups require editorial review")
        if unresolved:
            warnings.append(f"{unresolved} unresolved QID-only titles will be excluded from public import")

    metrics = {
        "official_sources": len(sources),
        "official_releases": len(releases),
        "wikidata_candidates": len(wikidata_movies),
        "errors": len(errors),
        "warnings": len(warnings),
    }
    return errors, warnings, metrics


def main() -> int:
    errors, warnings, metrics = audit()
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    print("catalogue audit:", json.dumps(metrics, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
