#!/usr/bin/env python3
"""Build FK-safe D1 upserts for first-party release review observations.

The monitor artifacts retain only short local evidence excerpts, never full page
or video descriptions. This module serializes those excerpts into D1 so a
review client can explain why a candidate date was detected.
"""
from __future__ import annotations

import json


def esc(value: str) -> str:
    return value.replace("'", "''")


def sql_value(value: str | None) -> str:
    return "NULL" if value is None else f"'{esc(value)}'"


def _candidate_fields(candidate: dict, kind: str) -> tuple[str, str, str, str | None, list]:
    if kind == "youtube":
        return (
            candidate["video_id"],
            candidate["video_url"],
            candidate["video_title"],
            candidate.get("published_at"),
            list(candidate.get("date_contexts") or []),
        )
    if kind == "website":
        return (
            candidate["external_id"],
            candidate["page_url"],
            candidate["review_title"],
            None,
            list(candidate.get("context_excerpts") or []),
        )
    raise ValueError(f"unsupported observation kind: {kind}")


def build_observation_sql(candidates: list[dict], sources: list[dict] | None, kind: str) -> str:
    """Return an idempotent source + observation upsert batch.

    Evidence is stored as compact JSON because a candidate may contain several
    explicit date mentions. The review status is never auto-promoted here.
    """
    statements: list[str] = []
    default_source_type = "official_channel" if kind == "youtube" else "official_website"

    for source in sources or []:
        statements.append(
            "INSERT INTO source_channels "
            "(source_key, source_name, source_type, website_url, youtube_channel_id, youtube_handle, active, updated_at) "
            f"VALUES ('{esc(source['key'])}','{esc(source['name'])}','{esc(source.get('source_type') or default_source_type)}',"
            f"{sql_value(source.get('website_url'))},{sql_value(source.get('youtube_channel_id'))},{sql_value(source.get('youtube_handle'))},"
            f"{1 if source.get('active', True) else 0},CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "source_name=excluded.source_name, source_type=excluded.source_type, website_url=excluded.website_url, "
            "youtube_channel_id=excluded.youtube_channel_id, youtube_handle=excluded.youtube_handle, "
            "active=excluded.active, updated_at=CURRENT_TIMESTAMP;"
        )

    for candidate in candidates:
        external_id, external_url, title, published_at, evidence_contexts = _candidate_fields(candidate, kind)
        candidate_dates = json.dumps(candidate.get("candidate_dates") or [], ensure_ascii=False)
        evidence_json = json.dumps(evidence_contexts, ensure_ascii=False)
        date_value = sql_value(candidate.get("candidate_release_date"))
        published_value = sql_value(published_at)
        statements.append(
            "INSERT INTO source_observations "
            "(source_key, external_id, external_url, title, published_at, candidate_release_date, candidate_dates_json, evidence_contexts_json, review_status, observed_at) "
            f"VALUES ('{esc(candidate['source_key'])}','{esc(external_id)}','{esc(external_url)}',"
            f"'{esc(title)}',{published_value},{date_value},'{esc(candidate_dates)}','{esc(evidence_json)}','pending_review',CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key, external_id) DO UPDATE SET "
            "external_url=excluded.external_url, title=excluded.title, published_at=excluded.published_at, "
            "candidate_release_date=excluded.candidate_release_date, candidate_dates_json=excluded.candidate_dates_json, "
            "evidence_contexts_json=excluded.evidence_contexts_json, observed_at=CURRENT_TIMESTAMP;"
        )

    return "\n".join(statements) + ("\n" if statements else "")
