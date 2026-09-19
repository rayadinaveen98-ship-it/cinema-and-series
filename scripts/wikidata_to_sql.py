#!/usr/bin/env python3
"""Convert Wikidata candidate JSON into idempotent D1 upserts.

The movie identity remains stable (`wd-QID`) when a release-date candidate
changes. Previous release evidence is retained rather than overwritten.
Unresolved rows whose label is still only their Wikidata QID are deliberately
excluded until a human-readable title becomes available.

The default source/output paths preserve the fast India refresh contract. The
same generator can consume sharded historical/global backfill payloads. A
payload or movie may request `merge_strategy=earliest`, which preserves the
earliest open-data date seen across independently fetched historical shards.
Verified or supported release dates are never replaced by unconfirmed Wikidata
data, and identical reruns become no-op updates to conserve D1 Free writes.

Reviewed media-identity corrections are enforced at the final SQL boundary as
defense in depth. A QID explicitly excluded from Movie, or canonicalized to
Series, can never be reintroduced by a later catalogue refresh.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import media_identity_corrections as identity
except ModuleNotFoundError:
    from scripts import media_identity_corrections as identity

DEFAULT_SRC = Path("data/generated/wikidata-india.json")
DEFAULT_OUT = Path("data/generated/wikidata-upsert.sql")


def esc(value: str) -> str:
    return value.replace("'", "''")


def build_statements(payload: dict) -> list[str]:
    statements: list[str] = []
    payload_country = str(payload.get("default_country_code") or "IN").upper()
    payload_merge_strategy = str(payload.get("merge_strategy") or "replace")

    for movie in payload.get("movies", []):
        raw_qid = str(movie["wikidata_qid"]).strip().upper()
        raw_title = str(movie["title"]).strip()
        if not raw_title or raw_title == raw_qid:
            continue
        if not identity.is_media_type_allowed(raw_qid, "movie"):
            continue

        qid = esc(raw_qid)
        title = esc(raw_title)
        release_date = esc(movie["release_date"])
        languages = movie.get("languages") or ["Unknown"]
        language_name = esc(str(languages[0]))
        country_code = esc(str(movie.get("country_code") or payload_country).upper())
        source_url = esc(movie.get("source_url") or f"https://www.wikidata.org/wiki/{qid}")
        movie_id = f"wd-{qid}"
        merge_strategy = str(movie.get("merge_strategy") or payload_merge_strategy)

        stronger_date = "movies.verification_status IN ('verified','supported')"
        if merge_strategy == "earliest":
            release_date_update = (
                "release_date=CASE "
                f"WHEN {stronger_date} THEN movies.release_date "
                "WHEN movies.release_date <= excluded.release_date THEN movies.release_date "
                "ELSE excluded.release_date END"
            )
            date_changed = f"(NOT ({stronger_date}) AND excluded.release_date < movies.release_date)"
        else:
            release_date_update = (
                f"release_date=CASE WHEN {stronger_date} "
                "THEN movies.release_date ELSE excluded.release_date END"
            )
            date_changed = f"(NOT ({stronger_date}) AND excluded.release_date <> movies.release_date)"

        statements.append(
            "INSERT INTO movies (id, wikidata_qid, title, language_name, country_code, release_date, verification_status, release_date_source, updated_at) "
            f"VALUES ('{esc(movie_id)}','{qid}','{title}','{language_name}','{country_code}','{release_date}','unconfirmed','wikidata',CURRENT_TIMESTAMP) "
            "ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title, language_name=excluded.language_name, country_code=excluded.country_code, "
            "release_date_source=CASE WHEN movies.verification_status IN ('verified','supported') THEN movies.release_date_source ELSE excluded.release_date_source END, "
            f"{release_date_update}, updated_at=CURRENT_TIMESTAMP "
            "WHERE movies.title <> excluded.title "
            "OR movies.language_name <> excluded.language_name "
            "OR movies.country_code <> excluded.country_code "
            f"OR {date_changed};"
        )

        statements.append(
            "INSERT OR IGNORE INTO release_evidence "
            "(movie_id, claimed_release_date, source_type, source_url, source_title, is_official) "
            f"VALUES ('{esc(movie_id)}','{release_date}','wikidata','{source_url}','Wikidata {qid}',0);"
        )

    return statements


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build D1 SQL from a Wikidata catalogue payload")
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.src.read_text(encoding="utf-8"))
    statements = build_statements(payload)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(statements) + ("\n" if statements else ""), encoding="utf-8")
    print(f"wrote {len(statements)//2} movie upserts plus evidence to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
