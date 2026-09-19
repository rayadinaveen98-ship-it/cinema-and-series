#!/usr/bin/env python3
"""Deterministic, provenance-backed media identity corrections.

This registry is intentionally small and explicit. It is not a heuristic and it
never infers media type from title text, country, language, or Wikipedia
category. Each correction must be backed by reviewed entity-type evidence.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data/quality/media_identity_corrections.json"
QID_RE = re.compile(r"^Q\d+$")
MEDIA_TYPES = {"movie", "series"}
DISPOSITIONS = {"exclude", "canonicalize"}


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "media-identity-corrections-v1":
        raise ValueError("unsupported media identity correction registry schema")
    raw = payload.get("corrections")
    if not isinstance(raw, dict):
        raise ValueError("media identity correction registry must contain an object named corrections")

    corrections: dict[str, dict[str, Any]] = {}
    for raw_qid, value in raw.items():
        qid = str(raw_qid).strip().upper()
        if not QID_RE.fullmatch(qid):
            raise ValueError(f"invalid media identity correction QID: {raw_qid!r}")
        if not isinstance(value, Mapping):
            raise ValueError(f"correction for {qid} must be an object")
        disposition = str(value.get("disposition") or "").strip()
        if disposition not in DISPOSITIONS:
            raise ValueError(f"correction for {qid} has unsupported disposition {disposition!r}")
        canonical = value.get("canonical_media_type")
        if disposition == "exclude":
            if canonical is not None:
                raise ValueError(f"excluded correction {qid} cannot have a canonical media type")
        else:
            canonical = str(canonical or "").strip()
            if canonical not in MEDIA_TYPES:
                raise ValueError(f"canonicalized correction {qid} must choose movie or series")
        evidence = value.get("evidence")
        if not isinstance(evidence, Mapping) or not evidence.get("entity_url") or not evidence.get("verified_run_id"):
            raise ValueError(f"correction for {qid} lacks durable evidence provenance")
        corrections[qid] = dict(value)
    return corrections


def is_media_type_allowed(
    qid: object,
    media_type: str,
    *,
    corrections: Mapping[str, Mapping[str, Any]] | None = None,
) -> bool:
    """Return whether a QID may enter the requested canonical media projection."""
    if media_type not in MEDIA_TYPES:
        raise ValueError(f"unsupported media type: {media_type}")
    normalized = str(qid or "").strip().upper()
    if not normalized:
        return True
    registry = corrections if corrections is not None else load_registry()
    correction = registry.get(normalized)
    if not correction:
        return True
    disposition = correction.get("disposition")
    if disposition == "exclude":
        return False
    return str(correction.get("canonical_media_type") or "").strip() == media_type


def filter_rows(
    rows: Iterable[Mapping[str, Any]],
    media_type: str,
    *,
    corrections: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    registry = corrections if corrections is not None else load_registry()
    kept: list[dict[str, Any]] = []
    suppressed: list[str] = []
    for row in rows:
        qid = str(row.get("wikidata_qid") or "").strip().upper()
        if qid and not is_media_type_allowed(qid, media_type, corrections=registry):
            suppressed.append(qid)
            continue
        kept.append(dict(row))
    return kept, sorted(set(suppressed), key=lambda value: int(value[1:]) if QID_RE.fullmatch(value) else value)
