"""Bounded, read-only P2.3 artwork discovery engine.

This module only turns already-fetched source records into reviewable candidates.
It never downloads media, mutates production tables, or publishes artwork.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from scripts.p2_artwork_adapters import ArtworkCandidate, normalize_candidate


@dataclass(frozen=True)
class TitleIdentity:
    title_id: str
    title: str
    year: int | None
    language: str | None
    territory: str = "IN"


@dataclass(frozen=True)
class DiscoveryCandidate:
    title_id: str
    normalized_title: str
    candidate: ArtworkCandidate
    match_score: int
    match_basis: str


def normalize_title(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def match_title(identity: TitleIdentity, source_title: str, source_year: int | None = None) -> tuple[int, str]:
    """Deterministic conservative match: exact normalized title, optional year bonus."""
    left, right = normalize_title(identity.title), normalize_title(source_title)
    if not left or left != right:
        return 0, "NO_MATCH"
    score = 100
    basis = "EXACT_NORMALIZED_TITLE"
    if identity.year is not None and source_year is not None:
        if identity.year == source_year:
            score += 10
            basis += "+YEAR"
        else:
            score -= 25
    return score, basis


def discover_candidates(
    identity: TitleIdentity,
    source_records: Iterable[dict],
    *,
    source_key: str,
    minimum_score: int = 100,
) -> list[DiscoveryCandidate]:
    """Produce bounded review candidates from supplied records only."""
    results: list[DiscoveryCandidate] = []
    for raw in source_records:
        score, basis = match_title(identity, str(raw.get("source_title", "")), raw.get("source_year"))
        if score < minimum_score:
            continue
        candidate = normalize_candidate(raw, source_key=source_key)
        results.append(
            DiscoveryCandidate(
                title_id=identity.title_id,
                normalized_title=normalize_title(identity.title),
                candidate=candidate,
                match_score=score,
                match_basis=basis,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -item.match_score,
            item.candidate.source_asset_id,
            item.candidate.role,
        ),
    )
