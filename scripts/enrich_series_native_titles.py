#!/usr/bin/env python3
"""Analyze missing SeriesRun native titles from explicit Wikidata original-title evidence.

Conservative source hierarchy:
- Tier A: explicit non-deprecated P1705 (native label) claims.
- Tier B: P1476 (title) only when that exact statement has
  P3831 (object has role) = Q1294573 (original title).
- unqualified/localized P1476 values are ignored.
- a resolved P1705 is authoritative unless a resolved explicitly-original P1476
  disagrees, in which case the row is a conflict and is not written.
- ambiguous or unusable P1705 never silently falls back to P1476.
- if P1705 is absent, one unambiguous explicitly-original P1476 may resolve.
- every resolved value records its language code and exact provenance contract.
- generated SQL rechecks ID, QID, and empty native_title before writing.

No title is inferred from Wikidata labels, Wikipedia page names, country, script,
language metadata, or unqualified/localized title statements.
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

P1705_NATIVE_LABEL = "P1705"
P1476_TITLE = "P1476"
P3831_OBJECT_HAS_ROLE = "P3831"
ORIGINAL_TITLE_QID = "Q1294573"
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
    """Request Wikidata without turning transient API errors into missing metadata."""
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


def monolingual_text_value(snak_or_claim: Mapping[str, Any]) -> tuple[str, str] | None:
    mainsnak = snak_or_claim.get("mainsnak") if "mainsnak" in snak_or_claim else snak_or_claim
    if not isinstance(mainsnak, Mapping) or mainsnak.get("snaktype") != "value":
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


def item_qid_from_snak(snak: Mapping[str, Any]) -> str | None:
    if snak.get("snaktype") != "value":
        return None
    datavalue = snak.get("datavalue") or {}
    value = datavalue.get("value")
    if not isinstance(value, Mapping):
        return None
    qid = str(value.get("id") or "").strip().upper()
    if valid_qid(qid):
        return qid
    numeric_id = value.get("numeric-id")
    try:
        return f"Q{int(numeric_id)}" if numeric_id is not None else None
    except (TypeError, ValueError):
        return None


def claim_has_original_title_role(claim: Mapping[str, Any]) -> bool:
    qualifiers = claim.get("qualifiers") or {}
    role_snaks = qualifiers.get(P3831_OBJECT_HAS_ROLE) or []
    return any(
        isinstance(snak, Mapping) and item_qid_from_snak(snak) == ORIGINAL_TITLE_QID
        for snak in role_snaks
    )


def resolve_claim_values(
    claims: Iterable[object],
    *,
    require_original_title_role: bool = False,
) -> tuple[str, tuple[str, str] | None]:
    nondeprecated_seen = False
    preferred_seen = False
    preferred_unusable = False
    preferred_values: list[tuple[str, str]] = []
    usable_values: list[tuple[str, str]] = []

    for raw_claim in claims:
        if not isinstance(raw_claim, Mapping) or raw_claim.get("rank") == "deprecated":
            continue
        if require_original_title_role and not claim_has_original_title_role(raw_claim):
            continue
        nondeprecated_seen = True
        value = monolingual_text_value(raw_claim)
        if raw_claim.get("rank") == "preferred":
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


def resolve_native_title(entity: Mapping[str, Any]) -> tuple[str, tuple[str, str] | None, str | None]:
    """Return (status, value, source_contract).

    Status is resolved, ambiguous, conflict, missing, or unusable.
    """
    claims = entity.get("claims") or {}
    p1705_status, p1705_value = resolve_claim_values(claims.get(P1705_NATIVE_LABEL) or [])
    p1476_status, p1476_value = resolve_claim_values(
        claims.get(P1476_TITLE) or [], require_original_title_role=True
    )

    if p1705_status == "resolved" and p1705_value is not None:
        if p1476_status == "resolved" and p1476_value is not None and p1476_value != p1705_value:
            return "conflict", None, None
        return "resolved", p1705_value, "wikidata:P1705"

    if p1705_status in {"ambiguous", "unusable"}:
        return p1705_status, None, None

    if p1476_status == "resolved" and p1476_value is not None:
        return "resolved", p1476_value, "wikidata:P1476+P3831=Q1294573"
    if p1476_status in {"ambiguous", "unusable"}:
        return p1476_status, None, None
    return "missing", None, None


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
    conflicts: list[dict[str, Any]] = []
    missing_claim: list[dict[str, Any]] = []
    unusable_value: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}

    for row in candidates:
        item = row_identity(row)
        qid = item["wikidata_qid"]
        status, value, source_contract = resolve_native_title(entities.get(qid, {}))
        if status == "ambiguous":
            ambiguous.append(item)
        elif status == "conflict":
            conflicts.append(item)
        elif status == "missing":
            missing_claim.append(item)
        elif status == "unusable" or value is None or source_contract is None:
            unusable_value.append(item)
        else:
            text, language_code = value
            source_counts[source_contract] = source_counts.get(source_contract, 0) + 1
            updates.append(
                {
                    **item,
                    "native_title": text,
                    "native_title_language_code": language_code,
                    "native_title_source": source_contract,
                    "native_title_source_url": f"https://www.wikidata.org/wiki/{qid}",
                }
            )

    return {
        "schema_version": "series-native-title-enrichment-v1",
        "source_contract": "P1705 OR P1476 qualified P3831=Q1294573",
        "candidate_count": len(candidates),
        "update_count": len(updates),
        "ambiguous_count": len(ambiguous),
        "conflict_count": len(conflicts),
        "missing_claim_count": len(missing_claim),
        "unusable_value_count": len(unusable_value),
        "source_counts": source_counts,
        "updates": updates,
        "ambiguous": ambiguous,
        "conflicts": conflicts,
        "missing_claim": missing_claim,
        "unusable_value": unusable_value,
    }


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(report: Mapping[str, Any]) -> str:
    statements = [
        "-- Series Native Title Enrichment V1: explicit original-title evidence only.",
        "-- Accepted sources: P1705, or P1476 explicitly qualified P3831=Q1294573.",
        "-- Defensive predicates prevent overwriting a title resolved after snapshot capture.",
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
        description="Analyze missing SeriesRun native titles from explicit Wikidata original-title evidence"
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
                "conflicts": report["conflict_count"],
                "missing_claim": report["missing_claim_count"],
                "unusable_value": report["unusable_value_count"],
                "source_counts": report["source_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
