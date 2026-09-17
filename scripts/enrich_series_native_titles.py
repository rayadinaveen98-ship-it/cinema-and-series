#!/usr/bin/env python3
"""Enrich missing SeriesRun native titles from explicit Wikidata P1705 claims.

The resolver is deliberately conservative:
- only rows whose native_title is unresolved are eligible;
- only valid Wikidata QIDs are queried;
- only non-deprecated P1705 (native label) claims are considered;
- P1705 values must be usable monolingual text with a non-empty language code;
- one unambiguous text/language pair is required; a unique preferred-rank value wins;
- ambiguous, missing, or unusable values remain unresolved;
- generated SQL rechecks ID, QID, and empty native_title before writing;
- every new native title records the Wikidata language code and P1705 provenance;
- QID-modulo sharding stays stable even after earlier shards write values.

No title is inferred from the English label, Wikipedia page title, country, script,
original-language metadata, or any translated/localized title property.
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

WIKIDATA_NATIVE_LABEL_PROPERTY = "P1705"
MAX_SERIES_PER_RUN = 1200
ENTITY_BATCH = 25
REQUEST_DELAY_SECONDS = 0.75
MAX_BATCH_RETRIES = 6
MAX_BACKOFF_SECONDS = 45
TRANSIENT_MEDIAWIKI_ERRORS = {"maxlag", "ratelimited"}
QID_RE = re.compile(r"^Q\d+$", re.IGNORECASE)


def norm(value: object) -> str:
    return " ".join(str(value or "").split())


def valid_qid(value: object) -> bool:
    return bool(QID_RE.fullmatch(str(value or "").strip()))


def qid_number(value: object) -> int:
    text = str(value or "").strip().upper()
    if not valid_qid(text):
        raise ValueError(f"invalid Wikidata QID: {value!r}")
    return int(text[1:])


def native_title_missing(value: object) -> bool:
    return not norm(value)


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


def select_candidates(
    rows: Iterable[Mapping[str, Any]],
    maximum: int,
    *,
    shard_index: int = 0,
    shard_count: int = 1,
) -> list[dict[str, Any]]:
    if shard_count < 1:
        raise ValueError("shard_count must be at least 1")
    if shard_index < 0 or shard_index >= shard_count:
        raise ValueError(f"shard_index must be between 0 and {shard_count - 1}")

    candidates: list[dict[str, Any]] = []
    for row in rows:
        qid = row.get("wikidata_qid")
        if not native_title_missing(row.get("native_title")) or not valid_qid(qid):
            continue
        if qid_number(qid) % shard_count != shard_index:
            continue
        candidates.append(dict(row))

    candidates.sort(key=lambda row: (qid_number(row.get("wikidata_qid")), str(row.get("id") or "")))
    return candidates[:maximum]


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


def native_label_value(claim: Mapping[str, Any]) -> tuple[str, str] | None:
    mainsnak = claim.get("mainsnak") or {}
    if mainsnak.get("snaktype") != "value":
        return None
    datavalue = mainsnak.get("datavalue") or {}
    value = datavalue.get("value")
    if not isinstance(value, Mapping):
        return None
    text = norm(value.get("text"))
    language = str(value.get("language") or "").strip().casefold()
    if not text or not language:
        return None
    return text, language


def claim_native_title(entity: Mapping[str, Any]) -> tuple[str, tuple[str, str] | None]:
    """Return (status, (text, language_code)).

    Status is resolved, ambiguous, missing, or unusable. A usable preferred-rank
    P1705 value takes precedence. If preferred claims exist but are unusable, the
    resolver refuses to fall back silently to normal-rank claims.
    """
    claims = (entity.get("claims") or {}).get(WIKIDATA_NATIVE_LABEL_PROPERTY) or []
    nondeprecated_seen = False
    preferred_seen = False
    preferred_unusable = False
    preferred_values: list[tuple[str, str]] = []
    usable_values: list[tuple[str, str]] = []

    for claim in claims:
        if not isinstance(claim, Mapping) or claim.get("rank") == "deprecated":
            continue
        nondeprecated_seen = True
        value = native_label_value(claim)
        if claim.get("rank") == "preferred":
            preferred_seen = True
            if value is None:
                preferred_unusable = True
            else:
                preferred_values.append(value)
        if value is not None:
            usable_values.append(value)

    if not nondeprecated_seen:
        return "missing", None

    if preferred_seen:
        if preferred_unusable:
            return "unusable", None
        unique_preferred = list(dict.fromkeys(preferred_values))
        if len(unique_preferred) == 1:
            return "resolved", unique_preferred[0]
        if len(unique_preferred) > 1:
            return "ambiguous", None
        return "unusable", None

    unique_values = list(dict.fromkeys(usable_values))
    if len(unique_values) == 1:
        return "resolved", unique_values[0]
    if len(unique_values) > 1:
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
    entities: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    updates: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    missing_claim: list[dict[str, Any]] = []
    unusable_value: list[dict[str, Any]] = []

    for row in candidates:
        item = row_identity(row)
        qid = item["wikidata_qid"]
        status, value = claim_native_title(entities.get(qid, {}))
        if status == "ambiguous":
            ambiguous.append(item)
        elif status == "missing":
            missing_claim.append(item)
        elif status == "unusable" or value is None:
            unusable_value.append(item)
        else:
            text, language_code = value
            updates.append(
                {
                    **item,
                    "native_title": text,
                    "native_title_language_code": language_code,
                    "native_title_source": f"wikidata:{WIKIDATA_NATIVE_LABEL_PROPERTY}",
                    "native_title_source_url": f"https://www.wikidata.org/wiki/{qid}",
                }
            )

    return {
        "schema_version": "series-native-title-enrichment-v1",
        "property": WIKIDATA_NATIVE_LABEL_PROPERTY,
        "candidate_count": len(candidates),
        "update_count": len(updates),
        "ambiguous_count": len(ambiguous),
        "missing_claim_count": len(missing_claim),
        "unusable_value_count": len(unusable_value),
        "updates": updates,
        "ambiguous": ambiguous,
        "missing_claim": missing_claim,
        "unusable_value": unusable_value,
    }


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(report: Mapping[str, Any]) -> str:
    statements = [
        "-- Series Native Title Enrichment V1: explicit Wikidata P1705 only.",
        "-- Defensive predicates prevent overwriting a native title resolved after snapshot capture.",
    ]
    for item in report.get("updates") or []:
        statements.append(
            "UPDATE series_titles SET "
            f"native_title={sql_quote(item['native_title'])}, "
            f"native_title_language_code={sql_quote(item['native_title_language_code'])}, "
            f"native_title_source={sql_quote(item['native_title_source'])}, "
            f"native_title_source_url={sql_quote(item['native_title_source_url'])}, "
            "updated_at=CURRENT_TIMESTAMP "
            f"WHERE id={sql_quote(item['id'])} "
            f"AND wikidata_qid={sql_quote(item['wikidata_qid'])} "
            "AND (native_title IS NULL OR TRIM(native_title)='');"
        )
    return "\n".join(statements) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich missing SeriesRun native titles from explicit Wikidata P1705 claims"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--max-series", type=int, default=MAX_SERIES_PER_RUN)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=Path("data/generated/series-native-title-enrichment-v1.json"),
    )
    parser.add_argument(
        "--sql-out",
        type=Path,
        default=Path("data/generated/series-native-title-enrichment-v1.sql"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_SERIES_PER_RUN, args.max_series))
    candidates = select_candidates(
        load_d1_rows(args.input),
        maximum,
        shard_index=args.shard_index,
        shard_count=args.shard_count,
    )
    qids = [str(row["wikidata_qid"]).upper() for row in candidates]
    entities = fetch_claim_entities(qids) if qids else {}
    report = build_enrichment(candidates, entities)
    report["shard_index"] = args.shard_index
    report["shard_count"] = args.shard_count

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.sql_out.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.sql_out.write_text(build_sql(report), encoding="utf-8")

    print(
        "SERIES_NATIVE_TITLE_ENRICHMENT_V1="
        + json.dumps(
            {
                "shard": args.shard_index,
                "shard_count": args.shard_count,
                "candidates": report["candidate_count"],
                "updates": report["update_count"],
                "ambiguous": report["ambiguous_count"],
                "missing_claim": report["missing_claim_count"],
                "unusable_value": report["unusable_value_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
