#!/usr/bin/env python3
"""Prepare a reviewed, read-only SQL preview from an Indian movie discovery audit.

Never executes SQL. A candidate requires Wikidata P31=film, P495=India,
P577 release year matching the discovery year, and a stable QID. The SQL
also guards existing exact movies and year-precision titles at import time.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_mediawiki_backfill as wiki
from audit_indian_movie_growth import rate_limited

FILM_QID = "Q11424"
INDIA_QID = "Q668"
BATCH_SIZE = 15
REQUEST_PAUSE = 1.4
QID = re.compile(r"^Q[1-9][0-9]*$")
YEAR = re.compile(r"^[+-](\d{4})-\d{2}-\d{2}T")


def ids_for_claim(entity: dict, property_id: str) -> set[str]:
    found = set()
    for claim in entity.get("claims", {}).get(property_id, []):
        mainsnak = claim.get("mainsnak", {})
        value = (mainsnak.get("datavalue") or {}).get("value")
        if mainsnak.get("snaktype") == "value" and isinstance(value, dict):
            qid = str(value.get("id") or "").upper()
            if QID.fullmatch(qid):
                found.add(qid)
    return found


def years_for_release(entity: dict) -> set[int]:
    years = set()
    for claim in entity.get("claims", {}).get("P577", []):
        mainsnak = claim.get("mainsnak", {})
        value = (mainsnak.get("datavalue") or {}).get("value")
        if not isinstance(value, dict) or int(value.get("precision") or 0) < 9:
            continue
        match = YEAR.match(str(value.get("time") or ""))
        if match:
            years.add(int(match.group(1)))
    return years


def validate(item: dict, entity: dict | None) -> str:
    if not isinstance(entity, dict) or "missing" in entity:
        return "entity_unavailable"
    if FILM_QID not in ids_for_claim(entity, "P31"):
        return "not_confirmed_film"
    if INDIA_QID not in ids_for_claim(entity, "P495"):
        return "not_confirmed_indian_origin"
    if item["year"] not in years_for_release(entity):
        return "release_year_not_corroborated"
    return "eligible"


def sql_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def sql_for_movie(item: dict) -> str:
    """Idempotent, insert-only and duplicate-guarded. Never rewrites prior titles."""
    qid = str(item["wikidata_qid"]).upper()
    if not QID.fullmatch(qid):
        raise ValueError("verified SQL requires a valid Wikidata QID")
    page_id = int(item["page_id"])
    year = int(item["year"])
    if not (1913 <= year <= 2026) or page_id <= 0:
        raise ValueError("invalid candidate year/page")
    title = str(item["title"]).strip()
    if not title or title.upper() == qid:
        raise ValueError("unresolved movie title")
    languages = item.get("observed_languages") or []
    language = languages[0] if len(languages) == 1 else "Unknown"
    categories = item.get("source_categories") or []
    category = categories[0] if categories else f"Category:{year} Indian films"
    source_url = f"https://en.wikipedia.org/?curid={page_id}"
    return (
        "INSERT OR IGNORE INTO catalogue_titles "
        "(id,wikidata_qid,wikipedia_page_id,title,release_year,date_precision,"
        "language_name,country_code,source_category,source_url,verification_status,updated_at) "
        "SELECT "
        f"{sql_quote('wd-' + qid)},{sql_quote(qid)},{page_id},{sql_quote(title)},{year},"
        f"'year',{sql_quote(language)},'IN',{sql_quote(category)},{sql_quote(source_url)},"
        "'unconfirmed',CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS (SELECT 1 FROM movies m WHERE "
        f"m.wikidata_qid={sql_quote(qid)} OR (LOWER(TRIM(m.title))=LOWER(TRIM({sql_quote(title)})) "
        f"AND CAST(substr(m.release_date,1,4) AS INTEGER)={year})) "
        "AND NOT EXISTS (SELECT 1 FROM series_titles s WHERE "
        f"s.wikidata_qid={sql_quote(qid)}) "
        "AND NOT EXISTS (SELECT 1 FROM catalogue_titles c WHERE "
        f"c.wikidata_qid={sql_quote(qid)} OR c.wikipedia_page_id={page_id} OR "
        f"(LOWER(TRIM(c.title))=LOWER(TRIM({sql_quote(title)})) AND c.release_year={year}));"
    )


def find_candidates(payload: dict, max_checks: int) -> list[dict]:
    seen = set()
    selected = []
    for item in payload.get("candidates", []):
        if item.get("classification") not in {
            "new_indian_category_candidates", "new_language_only_candidates"
        }:
            continue
        qid = str(item.get("wikidata_qid") or "").upper()
        if not QID.fullmatch(qid) or qid in seen:
            continue
        if not isinstance(item.get("year"), int):
            continue
        if not item.get("title") or str(item["title"]).strip().upper() == qid:
            continue
        seen.add(qid)
        selected.append(item)
    selected.sort(key=lambda row: (not row.get("india_category"), -row["year"],
                                   str(row["title"]).casefold()))
    return selected[:max_checks]


def verify(candidate_items: list[dict], request_fn=None) -> dict:
    """Explicit dependency injection keeps unit tests network-free."""
    request_fn = request_fn or wiki.request_json
    accepted = []
    rejected = []
    stopped_for_rate_limit = False
    checked = 0
    for start in range(0, len(candidate_items), BATCH_SIZE):
        batch = candidate_items[start:start + BATCH_SIZE]
        ids = [str(item["wikidata_qid"]).upper() for item in batch]
        try:
            response = request_fn(
                wiki.WIKIDATA_API,
                {"action": "wbgetentities", "ids": "|".join(ids),
                 "props": "claims", "format": "json", "formatversion": "2"},
            )
        except Exception as exc:
            reason = "rate_limited" if rate_limited(exc) else "request_failure"
            rejected.extend({"qid": qid, "reason": reason} for qid in ids)
            if rate_limited(exc):
                stopped_for_rate_limit = True
                print("Wikidata rate-limit detected; stopping corroboration requests.")
                break
            time.sleep(REQUEST_PAUSE)
            continue
        entities = response.get("entities", {})
        for item in batch:
            qid = str(item["wikidata_qid"]).upper()
            reason = validate(item, entities.get(qid))
            checked += 1
            if reason == "eligible":
                accepted.append(item)
            else:
                rejected.append({"qid": qid, "reason": reason})
        time.sleep(REQUEST_PAUSE)
    return {
        "accepted": accepted, "rejected": rejected,
        "checked": checked,
        "rate_limited": stopped_for_rate_limit,
        "total_attempted": len(candidate_items),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit-json", type=Path, required=True)
    p.add_argument("--max-checks", type=int, default=60)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-sql", type=Path, required=True)
    args = p.parse_args()
    if not 1 <= args.max_checks <= 300:
        p.error("--max-checks must be 1..300")
    report = json.loads(args.audit_json.read_text(encoding="utf-8"))
    candidates = find_candidates(report, args.max_checks)
    results = verify(candidates) if candidates else {"accepted": [], "rejected": [], "checked": 0, "rate_limited": False}
    outcomes = Counter(row["reason"] for row in results["rejected"])
    summary = {
        "examined_qid_candidates": results["checked"],
        "verified_indian_film_candidates": len(results["accepted"]),
        "reject_or_defer_reasons": dict(outcomes),
        "rate_limited": results["rate_limited"],
        "source_audit_incomplete": bool(report.get("source", {}).get("source_incomplete")),
        "note": "SQL preview only; verified Wikidata claims are not equivalent to official confirmation.",
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps({"summary": summary, "verified": results["accepted"],
                    "rejected": results["rejected"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.out_sql.parent.mkdir(parents=True, exist_ok=True)
    sql = ["-- READ-ONLY PREVIEW. Do not apply before independent review."]
    sql.extend(sql_for_movie(item) for item in results["accepted"])
    args.out_sql.write_text("\n".join(sql) + "\n", encoding="utf-8")
    print("INDIA_VERIFIED_PREVIEW=" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
