#!/usr/bin/env python3
"""Convert curated first-party release evidence into idempotent D1 upserts.

Official evidence is allowed to promote a movie to verified and replace the
public display release date. Matching prefers Wikidata QID when available,
otherwise a case-insensitive title match is reused before creating a stable
`official-*` movie row.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RELEASES = Path("data/official/releases.json")
SOURCES = Path("data/official/source_registry.json")
OUT = Path("data/generated/official-upsert.sql")


def esc(value: str) -> str:
    return value.replace("'", "''")


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return normalized or "movie"


def q(value: str | None) -> str:
    return "NULL" if value is None else f"'{esc(value)}'"


def build_statements(releases_payload: dict, sources_payload: dict) -> list[str]:
    statements: list[str] = []

    for source in sources_payload.get("sources", []):
        statements.append(
            "INSERT INTO source_channels "
            "(source_key, source_name, source_type, website_url, youtube_channel_id, youtube_handle, active, updated_at) "
            f"VALUES ('{esc(source['key'])}','{esc(source['name'])}','{esc(source['source_type'])}',"
            f"{q(source.get('website_url'))},{q(source.get('youtube_channel_id'))},{q(source.get('youtube_handle'))},"
            f"{1 if source.get('active', True) else 0},CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "source_name=excluded.source_name, source_type=excluded.source_type, website_url=excluded.website_url, "
            "youtube_channel_id=excluded.youtube_channel_id, youtube_handle=excluded.youtube_handle, "
            "active=excluded.active, updated_at=CURRENT_TIMESTAMP;"
        )

    for movie in releases_payload.get("releases", []):
        title = esc(movie["title"])
        release_date = esc(movie["release_date"])
        language = esc(movie.get("language") or "Unknown")
        country_code = esc(movie.get("country_code") or "IN")
        source_key = esc(movie["source_key"])
        source_type = esc(movie["source_type"])
        source_title = esc(movie.get("source_title") or movie["title"])
        source_url = esc(movie["source_url"])
        qid = movie.get("wikidata_qid")
        preferred_id = f"wd-{qid}" if qid else f"official-{slug(movie['title'])}"

        if qid:
            qid_escaped = esc(qid)
            statements.append(
                "INSERT INTO movies (id, wikidata_qid, title, language_name, country_code, release_date, verification_status, release_date_source, updated_at) "
                f"VALUES ('{esc(preferred_id)}','{qid_escaped}','{title}','{language}','{country_code}','{release_date}','verified','{source_key}',CURRENT_TIMESTAMP) "
                "ON CONFLICT(id) DO UPDATE SET "
                "title=excluded.title, language_name=CASE WHEN movies.language_name='Unknown' THEN excluded.language_name ELSE movies.language_name END, "
                "country_code=excluded.country_code, release_date=excluded.release_date, verification_status='verified', "
                "release_date_source=excluded.release_date_source, updated_at=CURRENT_TIMESTAMP;"
            )
        else:
            statements.append(
                "UPDATE movies SET "
                f"release_date='{release_date}', verification_status='verified', release_date_source='{source_key}', "
                f"language_name=CASE WHEN language_name='Unknown' THEN '{language}' ELSE language_name END, updated_at=CURRENT_TIMESTAMP "
                f"WHERE id=(SELECT id FROM movies WHERE title COLLATE NOCASE='{title}' LIMIT 1);"
            )
            statements.append(
                "INSERT INTO movies (id, title, language_name, country_code, release_date, verification_status, release_date_source, updated_at) "
                f"SELECT '{esc(preferred_id)}','{title}','{language}','{country_code}','{release_date}','verified','{source_key}',CURRENT_TIMESTAMP "
                f"WHERE NOT EXISTS (SELECT 1 FROM movies WHERE title COLLATE NOCASE='{title}');"
            )

        match_clause = (
            f"wikidata_qid='{esc(qid)}'" if qid else f"title COLLATE NOCASE='{title}'"
        )
        statements.append(
            "INSERT OR IGNORE INTO release_evidence "
            "(movie_id, claimed_release_date, source_type, source_url, source_title, is_official) "
            f"SELECT id,'{release_date}','{source_type}','{source_url}','{source_title}',1 "
            f"FROM movies WHERE {match_clause} ORDER BY verification_status='verified' DESC LIMIT 1;"
        )

    return statements


def main() -> int:
    releases_payload = json.loads(RELEASES.read_text(encoding="utf-8"))
    sources_payload = json.loads(SOURCES.read_text(encoding="utf-8"))
    statements = build_statements(releases_payload, sources_payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(statements) + ("\n" if statements else ""), encoding="utf-8")
    print(
        f"wrote {len(sources_payload.get('sources', []))} source upserts and "
        f"{len(releases_payload.get('releases', []))} verified release upserts to {OUT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
