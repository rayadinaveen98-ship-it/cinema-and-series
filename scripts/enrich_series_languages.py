#!/usr/bin/env python3
"""Enrich unknown SeriesRun languages from explicit Wikidata P364 claims.

The engine is intentionally conservative:
- only rows whose current language is missing/Unknown are candidates;
- only valid Wikidata QIDs are queried;
- deprecated claims are ignored;
- one unambiguous language QID is required (a unique preferred claim wins);
- ambiguous/missing claims remain unresolved;
- generated SQL contains a defensive WHERE clause and records field provenance;
- optional sharding uses the numeric Wikidata QID, so partitions stay stable even
  when earlier shards have already written resolved languages.

No language is inferred from country, title, script, Wikipedia category, or cast.
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

WIKIDATA_LANGUAGE_PROPERTY = "P364"
MAX_SERIES_PER_RUN = 8000
ENTITY_BATCH = 25
LABEL_BATCH = 25
REQUEST_DELAY_SECONDS = 0.75
MAX_BATCH_RETRIES = 6
MAX_BACKOFF_SECONDS = 45
TRANSIENT_MEDIAWIKI_ERRORS = {"maxlag", "ratelimited"}
UNKNOWN = {"", "unknown", "xx", "und", "n/a", "na", "none", "null"}
QID_RE = re.compile(r"^Q\d+$", re.IGNORECASE)


def norm(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def valid_qid(value: object) -> bool:
    return bool(QID_RE.fullmatch(str(value or "").strip()))


def qid_number(value: object) -> int:
    text = str(value or "").strip().upper()
    if not valid_qid(text):
        raise ValueError(f"invalid Wikidata QID: {value!r}")
    return int(text[1:])


def language_unknown(value: object) -> bool:
    return norm(value) in UNKNOWN


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

    candidates = []
    for row in rows:
        qid = row.get("wikidata_qid")
        if not language_unknown(row.get("language_name")) or not valid_qid(qid):
            continue
        if qid_number(qid) % shard_count != shard_index:
            continue
        candidates.append(dict(row))

    candidates.sort(key=lambda row: (qid_number(row.get("wikidata_qid")), str(row.get("id"))))
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
    """Return a bounded retry delay for an HTTP-200 MediaWiki transient error."""
    exponential = min(MAX_BACKOFF_SECONDS, 2 ** (attempt + 2))
    lag = error.get("lag")
    try:
        lag_delay = max(1, int(float(lag)) + 1) if lag is not None else 0
    except (TypeError, ValueError):
        lag_delay = 0
    return min(MAX_BACKOFF_SECONDS, max(exponential, lag_delay))


def request_wikidata(params: dict[str, str]) -> dict[str, Any]:
    """Request Wikidata with cooperative pacing and bounded transient backoff.

    MediaWiki can return throttling/server-load errors inside an HTTP-200 JSON
    payload. Those must never be interpreted as an empty entity response because
    doing so would silently misclassify metadata as genuinely missing.
    """
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
                            f"Wikidata transient API error persisted after {MAX_BATCH_RETRIES} attempts: "
                            f"{code}: {info}"
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
        payload = request_wikidata({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "claims",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        })
        for qid, entity in (payload.get("entities") or {}).items():
            if isinstance(entity, dict):
                entities[str(qid)] = entity
        time.sleep(REQUEST_DELAY_SECONDS)
    return entities


def claim_language_qids(entity: Mapping[str, Any]) -> tuple[str, str | None]:
    """Return (status, language_qid).

    Status is one of: resolved, ambiguous, missing.
    A unique preferred claim takes precedence over normal-rank claims. Otherwise
    there must be exactly one unique non-deprecated value.
    """
    claims = (entity.get("claims") or {}).get(WIKIDATA_LANGUAGE_PROPERTY) or []
    preferred: list[str] = []
    usable: list[str] = []
    for claim in claims:
        if not isinstance(claim, Mapping) or claim.get("rank") == "deprecated":
            continue
        mainsnak = claim.get("mainsnak") or {}
        if mainsnak.get("snaktype") != "value":
            continue
        datavalue = mainsnak.get("datavalue") or {}
        value = datavalue.get("value")
        qid = value.get("id") if isinstance(value, Mapping) else None
        if not valid_qid(qid):
            continue
        canonical = str(qid).upper()
        usable.append(canonical)
        if claim.get("rank") == "preferred":
            preferred.append(canonical)

    preferred_unique = sorted(set(preferred))
    if len(preferred_unique) == 1:
        return "resolved", preferred_unique[0]
    if len(preferred_unique) > 1:
        return "ambiguous", None

    usable_unique = sorted(set(usable))
    if len(usable_unique) == 1:
        return "resolved", usable_unique[0]
    if len(usable_unique) > 1:
        return "ambiguous", None
    return "missing", None


def fetch_language_labels(qids: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for batch in chunks(sorted(set(qids)), LABEL_BATCH):
        payload = request_wikidata({
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "labels",
            "languages": "en",
            "languagefallback": "1",
            "format": "json",
            "formatversion": "2",
            "origin": "*",
        })
        for qid, entity in (payload.get("entities") or {}).items():
            if not isinstance(entity, Mapping):
                continue
            label = ((entity.get("labels") or {}).get("en") or {}).get("value")
            if isinstance(label, str) and label.strip():
                labels[str(qid).upper()] = label.strip()
        time.sleep(REQUEST_DELAY_SECONDS)
    return labels


def build_enrichment(
    candidates: list[dict[str, Any]],
    entities: Mapping[str, Mapping[str, Any]],
    labels: Mapping[str, str],
) -> dict[str, Any]:
    updates: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    missing_claim: list[dict[str, Any]] = []
    missing_label: list[dict[str, Any]] = []

    for row in candidates:
        series_qid = str(row.get("wikidata_qid") or "").upper()
        status, language_qid = claim_language_qids(entities.get(series_qid, {}))
        item = {
            "id": str(row.get("id") or ""),
            "title": str(row.get("title") or ""),
            "wikidata_qid": series_qid,
        }
        if status == "ambiguous":
            ambiguous.append(item)
            continue
        if status == "missing" or not language_qid:
            missing_claim.append(item)
            continue
        language = labels.get(language_qid)
        if not language:
            missing_label.append({**item, "language_qid": language_qid})
            continue
        updates.append({
            **item,
            "language": language,
            "language_qid": language_qid,
            "language_source": f"wikidata:{WIKIDATA_LANGUAGE_PROPERTY}",
            "language_source_url": f"https://www.wikidata.org/wiki/{series_qid}",
        })

    return {
        "schema_version": "series-language-enrichment-v1",
        "property": WIKIDATA_LANGUAGE_PROPERTY,
        "candidate_count": len(candidates),
        "update_count": len(updates),
        "ambiguous_count": len(ambiguous),
        "missing_claim_count": len(missing_claim),
        "missing_label_count": len(missing_label),
        "updates": updates,
        "ambiguous": ambiguous,
        "missing_claim": missing_claim,
        "missing_label": missing_label,
    }


def sql_quote(value: object | None) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def build_sql(report: Mapping[str, Any]) -> str:
    statements = [
        "-- Series Language Enrichment V1: explicit Wikidata P364 only.",
        "-- Defensive predicates prevent overwriting any language resolved since snapshot capture.",
    ]
    for item in report.get("updates") or []:
        statements.append(
            "UPDATE series_titles SET "
            f"language_name={sql_quote(item['language'])}, "
            f"language_source={sql_quote(item['language_source'])}, "
            f"language_source_url={sql_quote(item['language_source_url'])}, "
            "updated_at=CURRENT_TIMESTAMP "
            f"WHERE id={sql_quote(item['id'])} "
            f"AND wikidata_qid={sql_quote(item['wikidata_qid'])} "
            "AND (language_name IS NULL OR TRIM(language_name)='' OR LOWER(language_name)='unknown');"
        )
    return "\n".join(statements) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich unknown SeriesRun language from explicit Wikidata P364 claims")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--max-series", type=int, default=MAX_SERIES_PER_RUN)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--out-json", type=Path, default=Path("data/generated/series-language-enrichment-v1.json"))
    parser.add_argument("--sql-out", type=Path, default=Path("data/generated/series-language-enrichment-v1.sql"))
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

    language_qids: list[str] = []
    for qid in qids:
        status, language_qid = claim_language_qids(entities.get(qid, {}))
        if status == "resolved" and language_qid:
            language_qids.append(language_qid)
    labels = fetch_language_labels(language_qids) if language_qids else {}

    report = build_enrichment(candidates, entities, labels)
    report["shard_index"] = args.shard_index
    report["shard_count"] = args.shard_count
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.sql_out.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.sql_out.write_text(build_sql(report), encoding="utf-8")
    print("SERIES_LANGUAGE_ENRICHMENT_V1=" + json.dumps({
        "shard": args.shard_index,
        "shard_count": args.shard_count,
        "candidates": report["candidate_count"],
        "updates": report["update_count"],
        "ambiguous": report["ambiguous_count"],
        "missing_claim": report["missing_claim_count"],
        "missing_label": report["missing_label_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
