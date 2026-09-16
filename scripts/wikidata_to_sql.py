#!/usr/bin/env python3
"""Convert reviewed Wikidata candidate JSON into idempotent D1 upserts.

The movie identity remains stable (`wd-QID`) when a release-date candidate
changes. Previous release evidence is retained rather than overwritten.

Wrangler's remote `d1 execute --file` path must not contain explicit SQL
transaction statements, so this generator emits only idempotent statements.
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("data/generated/wikidata-india.json")
OUT = Path("data/generated/wikidata-upsert.sql")


def esc(value: str) -> str:
    return value.replace("'", "''")


def build_statements(payload: dict) -> list[str]:
    statements: list[str] = []

    for movie in payload.get("movies", []):
        qid = esc(movie["wikidata_qid"])
        title = esc(movie["title"])
        release_date = esc(movie["release_date"])
        languages = movie.get("languages") or ["Unknown"]
        language_name = esc(languages[0])
        source_url = esc(movie.get("source_url") or f"https://www.wikidata.org/wiki/{qid}")
        movie_id = f"wd-{qid}"

        statements.append(
            "INSERT INTO movies (id, wikidata_qid, title, language_name, release_date, verification_status, release_date_source, updated_at) "
            f"VALUES ('{esc(movie_id)}','{qid}','{title}','{language_name}','{release_date}','unconfirmed','wikidata',CURRENT_TIMESTAMP) "
            "ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title, language_name=excluded.language_name, "
            "release_date_source=CASE WHEN movies.verification_status='verified' THEN movies.release_date_source ELSE excluded.release_date_source END, "
            "release_date=CASE WHEN movies.verification_status='verified' THEN movies.release_date ELSE excluded.release_date END, "
            "updated_at=CURRENT_TIMESTAMP;"
        )

        statements.append(
            "INSERT OR IGNORE INTO release_evidence "
            "(movie_id, claimed_release_date, source_type, source_url, source_title, is_official) "
            f"VALUES ('{esc(movie_id)}','{release_date}','wikidata','{source_url}','Wikidata {qid}',0);"
        )

    return statements


def main() -> int:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    statements = build_statements(payload)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(statements) + ("\n" if statements else ""), encoding="utf-8")
    print(f"wrote {len(statements)//2} movie upserts plus evidence to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
