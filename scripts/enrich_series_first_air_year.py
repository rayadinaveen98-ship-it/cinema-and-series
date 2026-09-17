#!/usr/bin/env python3
"""Enrich missing SeriesRun first-air years from explicit Wikidata P580 claims.

The resolver is deliberately conservative:
- only rows whose first_air_year is unresolved are eligible;
- only valid Wikidata QIDs are queried;
- only non-deprecated P580 (start time) claims are considered;
- dates must have at least year precision and fall inside the production schema range;
- one unambiguous year is required; a usable preferred-rank claim takes precedence;
- ambiguous, missing, imprecise, or invalid dates remain unresolved;
- generated SQL rechecks ID, QID, and NULL first_air_year before writing;
- every new year records field-level Wikidata P580 provenance.

No year is inferred from title text, Wikipedia categories, country, language, or other metadata.
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from pathlib import Path
from typing import Any, Iterable, Mapping

import fetch_mediawiki_backfill as base

WIKIDATA_FIRST_AIR_PROPERTY = "P580"
MAX_SERIES_PER_RUN = 500
ENTITY_BATCH = 25
REQUEST_DELAY_SECONDS = 0.75
MAX_BATCH_RETRIES = 6
MAX_BACKOFF_SECONDS = 45
TRANSIENT_MEDIAWIKI_ERRORS = {"maxlag", "ratelimited"}
QID_RE = re.compile(r"^Q\d+$", re.IGNORECASE)
WIKIDATA_TIME_RE = re.compile(r"^([+-])(\d{4,})-")
MIN_YEAR = 1900
MAX_YEAR = 2200
YEAR_PRECISION = 9


def valid_qid(value: object) -> bool:
    return bool(QID_RE.fullmatch(str(value or "").strip()))


def year_missing(value: object) -> bool:
    return value is None or str(value).strip() == ""


def load_d1_rows(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows: list[dict[str, Any]] = []
        for batch in payload:
            if isinstance(batch, dict) and isinstance(batch.get("results"), list):
                rows.extend(row for row in batch["results"] if isinstance(row, dict))
        return rows
    if isinstance(payload, dict):
        for key in ("results", "rows"):
            if isinstance(payload.get(key), list):
                return [row for row in payload[key] if isinstance(row, dict)]
    raise ValueError(f"{path}: unsupported D1 JSON shape")


def partition_candidates(
    rows: Iterable[Mapping[str, Any]], maximum: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    snapshot = [dict(row) for row in rows if year_missing(row.get("first_air_year"))]
    snapshot.sort(key=lambda row: (str(row.get("wikidata_qid") or ""), str(row.get("id") or "")))
    snapshot = snapshot[:maximum]
    candidates = [row for row in snapshot if valid_qid(row.get("wikidata_qid"))]
    missing_identity = [row for row in snapshot if not valid_qid(row.get("wikidata_qid"))]
    return candidates, missing_identity, len(snapshot)


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def retry_after_seconds(exc: urllib.error.HTTPError) -> int:
    raw = exc.headers.get("Retry-After") if exc.headers else None
    try:
        return max(1, int(raw)) if raw else 0
    except (TypeError, ValueError):
        return 0


def mediawiki_retry_delay(error: Mapping[str, Any], attempt: int) -> int:
    exponential = min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2))
    lag = error.get("lag")
    try:
        lag_delay = max(1, int(float(lag)) + 1) if lag is not None else 0
    except (TypeError, ValueError):
        lag_delay = 0
    return min(MAX_BACKOFF_SECONDS, max(exponential, lag_delay))


def request_wikidata(params: dict[str, str]) -> dict[str, Any]:
    """Request Wikidata without treating transient API errors as missing metadata."""
    request_params = {**params, "maxlag": "5"}
    last_error: Exception | None = None
    for attempt in range(MAX_BATCH_RETRIES):
        try:
            payload = base.request_json(base.WIKIDATA_API, request_params, post=False)
            api_error = payload.get("error") if isinstance(payload, Mapping) else None
            if isinstance(api_error, Mapping):
                code = str(api_error.get("code") or "unknown").strip().casefold()
                info = str(api_error.get("info") or "").strip()
                if code in TRANSIENT_MEDIAWIKI_ERRORS:
                    if attempt + 1 >= MAX_BATCH_RETRIES:
                        raise RuntimeError(
                            f"Wikidata transient API error persisted after {MAX_BATCH_RETRIES} attempts: {code}: {info}"
                        )
                    time.sleep(mediawiki_retry_delay(api_error, attempt))
                    continue
                raise RuntimeError(f"Wikidata API error {code}: {info}")
            if not isinstance(payload, dict):
                raise RuntimeError("Wikidata API returned a non-object JSON payload")
            return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code != 429:
                raise
            if attempt + 1 >= MAX_BATCH_RETRIES:
                raise
            exponential = min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2))
            delay = min(MAX_BACKOFF_SECONDS, max(retry_after_seconds(exc), exponential))
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt + 1 >= MAX_BATCH_RETRIES:
                raise
            time.sleep(min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2)))
    raise RuntimeError(f"unreachable Wikidata request failure: {last_error}")


def fetch_claim_entities(qids: list[str]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for batch in chunks(qids, ENTITY_BATCH):
        payload = request_wikidata(
            {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "claims",
                "format": "json",
                "formatversion": "2",
                "origin": "*",
            }
        )
        for qid, entity in (payload.get("entities") or {}).items():
            if isinstance(entity, dict):
                entities[str(qid).upper()] = entity
        time.sleep(REQUEST_DELAY_SECONDS)
    return entities


def extract_year_from_time_value(value: object) -> int | None:
    if not isinstance(value, Mapping):
        return None
    precision = value.get("precision")
    try:
        if int(precision) < YEAR_PRECISION:
            return None
    except (TypeError, ValueError):
        return None
    raw_time = str(value.get("time") or "")
    match = WIKIDATA_TIME_RE.match(raw_time)
    if not match or match.group(1) != "+":
        return None
    try:
        year = int(match.group(2))
    except ValueError:
        return None
    if not MIN_YEAR <= year <= MAX_YEAR:
        return None
    return year


def claim_first_air_year(entity: Mapping[str, Any]) -> tuple[str, int | None]:
    """Return (status, year), where status is resolved/ambiguous/missing/unusable."""
    claims = (entity.get("claims") or {}).get(WIKIDATA_FIRST_AIR_PROPERTY) or []
    preferred_seen = False
    preferred_unusable = False
    preferred_years: list[int] = []
    usable_years: list[int] = []
    nondeprecated_seen = False

    for claim in claims:
        if not isinstance(claim, Mapping) or claim.get("rank") == "deprecated":
            continue
        nondeprecated_seen = True
        mainsnak = claim.get("mainsnak") or {}
        if mainsnak.get("snaktype") != "value":
            if claim.get("rank") == "preferred":
                preferred_seen = True
                preferred_unusable = True
            continue
        datavalue = mainsnak.get("datavalue") or {}
        year = extract_year_from_time_value(datavalue.get("value"))
        if claim.get("rank") == "preferred":
            preferred_seen = True
            if year is None:
                preferred_unusable = True
            else:
                preferred_years.append(year)
        if year is not None:
            usable_years.append(year)

    if not nondeprecated_seen:
        return "missing", None

    if preferred_seen:
        if preferred_unusable:
            return "unusable", None
        unique_preferred = sorted(set(preferred_years))
        if len(unique_preferred) == 1:
            return "resolved", unique_preferred[0]
        if len(unique_preferred) > 1:
            return "ambiguous", None
        return "unusable", None

    unique_years = sorted(set(usable_years))
    if len(unique_years) == 1:
        return "resolved", unique_years[0]
    if len(unique_years) > 1:
        return "ambiguous", None
    return "unusable", None


def row_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or ""),
        "title": str(row.get("title") or ""),
        "wikidata_qid": str(row.get("wikidata_qid") or "").upper(),
    }


def build_enrichment(
    candidates: list[dict[str, Any]],
    missing_identity_rows: list[dict[str, Any]],
    snapshot_count: int,
    entities: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    updates: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    missing_claim: list[dict[str, Any]] = []
    unusable_time: list[dict[str, Any]] = []

    for row in candidates:
        item = row_identity(row)
        qid = item["wikidata_qid"]
        status, year = claim_first_air_year(entities.get(qid, {}))
        if status == "ambiguous":
            ambiguous.append(item)
        elif status == "missing":
            missing_claim.append(item)
        elif status == "unusable" or year is None:
            unusable_time.append(item)
        else:
            updates.append(
                {
                    **item,
                    "first_air_year": year,
                    "first_air_year_source": f"wikidata:{WIKIDATA_FIRST_AIR_PROPERTY}",
                    "first_air_year_source_url": f"https://www.wikidata.org/wiki/{qid}",
                }
            )

    missing_identity = [
        {
            "id": str(row.get("id") or ""),
            "title": str(row.get("title") or ""),
            "wikidata_qid": str(row.get("wikidata_qid") or ""),
        }
        for row in missing_identity_rows
    ]

    return {
        "schema_version": "series-first-air-year-enrichment-v1",
        "property": WIKIDATA_FIRST_AIR_PROPERTY,
        "snapshot_count": snapshot_count,
        "candidate_count": len(candidates),
        "missing_identity_count": len(missing_identity),
        "update_count": len(updates),
        "ambiguous_count": len(ambiguous),
        "missing_claim_count": len(missing_claim),
        "unusable_time_count": len(unusable_time),
        "updates": updates,
        "ambiguous": ambiguous,
        "missing_claim": missing_claim,
        "unusable_time": unusable_time,
        "missing_identity": missing_identity,
    }


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(report: Mapping[str, Any]) -> str:
    statements = [
        "-- Series First-Air-Year Enrichment V1: explicit Wikidata P580 only.",
        "-- Defensive predicates prevent overwriting a year resolved after snapshot capture.",
    ]
    for item in report.get("updates") or []:
        statements.append(
            "UPDATE series_titles SET "
            f"first_air_year={int(item['first_air_year'])}, "
            f"first_air_year_source={sql_quote(item['first_air_year_source'])}, "
            f"first_air_year_source_url={sql_quote(item['first_air_year_source_url'])}, "
            "updated_at=CURRENT_TIMESTAMP "
            f"WHERE id={sql_quote(item['id'])} "
            f"AND wikidata_qid={sql_quote(item['wikidata_qid'])} "
            "AND first_air_year IS NULL;"
        )
    return "\n".join(statements) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich missing SeriesRun first-air year from explicit Wikidata P580 claims"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--max-series", type=int, default=MAX_SERIES_PER_RUN)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("data/generated/series-first-air-year-enrichment-v1.json"),
    )
    parser.add_argument(
        "--sql-out",
        type=Path,
        default=Path("data/generated/series-first-air-year-enrichment-v1.sql"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_SERIES_PER_RUN, args.max_series))
    candidates, missing_identity, snapshot_count = partition_candidates(load_d1_rows(args.input), maximum)
    qids = [str(row["wikidata_qid"]).upper() for row in candidates]
    entities = fetch_claim_entities(qids) if qids else {}
    report = build_enrichment(candidates, missing_identity, snapshot_count, entities)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.sql_out.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.sql_out.write_text(build_sql(report), encoding="utf-8")

    print(
        "SERIES_FIRST_AIR_YEAR_ENRICHMENT_V1="
        + json.dumps(
            {
                "snapshot": report["snapshot_count"],
                "candidates": report["candidate_count"],
                "missing_identity": report["missing_identity_count"],
                "updates": report["update_count"],
                "ambiguous": report["ambiguous_count"],
                "missing_claim": report["missing_claim_count"],
                "unusable_time": report["unusable_time_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
