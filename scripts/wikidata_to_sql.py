#!/usr/bin/env python3
"""Convert reviewed Wikidata candidate JSON into idempotent D1 upserts."""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path("data/generated/wikidata-india.json")
OUT = Path("data/generated/wikidata-upsert.sql")


def esc(value: str) -> str:
    return value.replace("'", "''")


def main() -> int:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    statements = ["BEGIN TRANSACTION;"]
    for movie in payload.get("movies", []):
        qid = esc(movie["wikidata_qid"])
        title = esc(movie["title"])
        release_date = esc(movie["release_date"])
        languages = movie.get("languages") or ["Unknown"]
        language_name = esc(languages[0])
        movie_id = f"wd-{qid}-{release_date}"
        statements.append(
            "INSERT INTO movies (id, wikidata_qid, title, language_name, release_date, verification_status, release_date_source, updated_at) "
            f"VALUES ('{esc(movie_id)}','{qid}','{title}','{language_name}','{release_date}','unconfirmed','wikidata',CURRENT_TIMESTAMP) "
            "ON CONFLICT(id) DO UPDATE SET title=excluded.title, language_name=excluded.language_name, release_date=excluded.release_date, updated_at=CURRENT_TIMESTAMP;"
        )
    statements.append("COMMIT;")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(statements) + "\n", encoding="utf-8")
    print(f"wrote {len(statements)-2} upserts to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
