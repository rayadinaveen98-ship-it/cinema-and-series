#!/usr/bin/env python3
"""Throttle-resilient Wikimedia catalogue backfill.

This runner keeps the broad Wikipedia category discovery from
`fetch_mediawiki_backfill.py`, but makes entity resolution deliberately
failure-tolerant:

1. Wikipedia resolves article titles -> Wikidata QIDs through pageprops.
2. Wikidata is queried only by direct QID, in smaller batches.
3. 429/transient failures use bounded multi-attempt backoff.
4. A failed batch is recorded and skipped; successful batches are retained.
5. Label lookup is best-effort and can degrade to seeded/Unknown languages.

Every resulting row remains unconfirmed discovery data. Stable QIDs are the
only identity key and the downstream SQL layer continues to protect verified
and supported release dates.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
from pathlib import Path

import fetch_mediawiki_backfill as base

OUT = Path("data/generated/mediawiki-backfill.json")
MAX_MOVIES_PER_RUN = 5000
TITLE_BATCH = 40
ENTITY_BATCH = 20
LABEL_BATCH = 25
REQUEST_DELAY_SECONDS = 0.75
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = (5, 12, 25, 40)


def chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def request_with_backoff(endpoint: str, params: dict[str, str], *, post: bool = False, sleep_fn=time.sleep) -> dict:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            return base.request_json(endpoint, params, post=post)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            retryable = not isinstance(exc, urllib.error.HTTPError) or exc.code in {429, 500, 502, 503, 504}
            if not retryable or attempt + 1 >= MAX_ATTEMPTS:
                break
            sleep_fn(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
    assert last_error is not None
    raise last_error


def resolve_qids_via_wikipedia(titles: list[str], *, sleep_fn=time.sleep) -> tuple[dict[str, str], list[dict]]:
    """Resolve English Wikipedia titles to stable Wikidata QIDs without WDQS."""
    qid_to_title: dict[str, str] = {}
    reports: list[dict] = []
    for batch_index, batch in enumerate(chunks(titles, TITLE_BATCH)):
        try:
            payload = request_with_backoff(
                base.ENWIKI_API,
                {
                    "action": "query",
                    "prop": "pageprops",
                    "ppprop": "wikibase_item",
                    "titles": "|".join(batch),
                    "redirects": "1",
                    "format": "json",
                    "formatversion": "2",
                    "origin": "*",
                },
                post=True,
                sleep_fn=sleep_fn,
            )
            found = 0
            for page in payload.get("query", {}).get("pages", []):
                qid = str(page.get("pageprops", {}).get("wikibase_item") or "").strip()
                title = str(page.get("title") or "").strip()
                if qid.startswith("Q") and title:
                    qid_to_title.setdefault(qid, title)
                    found += 1
            reports.append({"batch": batch_index, "status": "ok", "requested": len(batch), "resolved_qids": found})
        except Exception as exc:
            reports.append({"batch": batch_index, "status": "deferred", "requested": len(batch), "error": str(exc)[:180]})
        if batch_index + 1 < (len(titles) + TITLE_BATCH - 1) // TITLE_BATCH:
            sleep_fn(REQUEST_DELAY_SECONDS)
    return qid_to_title, reports


def fetch_entities_by_qid(qid_to_title: dict[str, str], *, sleep_fn=time.sleep) -> tuple[list[dict], list[dict]]:
    """Fetch claims by direct QID while retaining successful batches."""
    qids = list(qid_to_title)
    entities: list[dict] = []
    reports: list[dict] = []
    for batch_index, batch in enumerate(chunks(qids, ENTITY_BATCH)):
        try:
            payload = request_with_backoff(
                base.WIKIDATA_API,
                {
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "claims|labels|sitelinks",
                    "languages": "en",
                    "languagefallback": "1",
                    "format": "json",
                    "formatversion": "2",
                },
                post=True,
                sleep_fn=sleep_fn,
            )
            found = 0
            for qid, entity in payload.get("entities", {}).items():
                if not isinstance(entity, dict) or entity.get("missing") or not str(qid).startswith("Q"):
                    continue
                item = dict(entity)
                item.setdefault("id", str(qid))
                # Preserve the Wikipedia-discovered title as a safe local
                # fallback if the entity lacks an English label/sitelink.
                item["_discovered_title"] = qid_to_title.get(str(qid), "")
                entities.append(item)
                found += 1
            reports.append({"batch": batch_index, "status": "ok", "requested": len(batch), "entities": found})
        except Exception as exc:
            reports.append({"batch": batch_index, "status": "deferred", "requested": len(batch), "error": str(exc)[:180]})
        if batch_index + 1 < (len(qids) + ENTITY_BATCH - 1) // ENTITY_BATCH:
            sleep_fn(REQUEST_DELAY_SECONDS)
    return entities, reports


def fetch_labels_resilient(qids: set[str], *, sleep_fn=time.sleep) -> tuple[dict[str, str], list[dict]]:
    labels: dict[str, str] = {}
    reports: list[dict] = []
    values = sorted(qids)
    for batch_index, batch in enumerate(chunks(values, LABEL_BATCH)):
        try:
            payload = request_with_backoff(
                base.WIKIDATA_API,
                {
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "labels",
                    "languages": "en",
                    "languagefallback": "1",
                    "format": "json",
                    "formatversion": "2",
                },
                post=True,
                sleep_fn=sleep_fn,
            )
            for qid, entity in payload.get("entities", {}).items():
                label = entity.get("labels", {}).get("en", {}).get("value") if isinstance(entity, dict) else None
                if label:
                    labels[str(qid)] = str(label)
            reports.append({"batch": batch_index, "status": "ok", "requested": len(batch), "labels": len([qid for qid in batch if qid in labels])})
        except Exception as exc:
            reports.append({"batch": batch_index, "status": "deferred", "requested": len(batch), "error": str(exc)[:180]})
        if batch_index + 1 < (len(values) + LABEL_BATCH - 1) // LABEL_BATCH:
            sleep_fn(REQUEST_DELAY_SECONDS)
    return labels, reports


def entity_title(entity: dict) -> str:
    sitelink = entity.get("sitelinks", {}).get("enwiki", {}).get("title")
    if sitelink:
        return str(sitelink)
    label = entity.get("labels", {}).get("en", {}).get("value")
    if label:
        return str(label)
    return str(entity.get("_discovered_title") or entity.get("id") or "")


def matching_seeds(title: str, metadata: dict[str, list[base.Seed]]) -> list[base.Seed]:
    if title in metadata:
        return metadata[title]
    normalized = title.replace("_", " ").casefold()
    return [
        seed
        for key, seed_list in metadata.items()
        if key.replace("_", " ").casefold() == normalized
        for seed in seed_list
    ]


def normalize_entities_resilient(
    entities: list[dict],
    metadata: dict[str, list[base.Seed]],
    *,
    sleep_fn=time.sleep,
) -> tuple[list[dict], list[dict]]:
    language_ids = {qid for entity in entities for qid in base.item_ids(entity, "P364")}
    language_labels, label_reports = fetch_labels_resilient(language_ids, sleep_fn=sleep_fn) if language_ids else ({}, [])
    movies: list[dict] = []

    for entity in entities:
        qid = str(entity.get("id") or "")
        title = entity_title(entity).strip()
        dates = base.claim_time_dates(entity)
        if not qid or not title or title == qid or not dates:
            continue

        seeds = matching_seeds(title, metadata)
        country_codes = sorted({seed.country_code for seed in seeds if seed.country_code})
        seeded_languages = sorted({seed.language for seed in seeds if seed.language})
        claim_languages = [language_labels[item] for item in base.item_ids(entity, "P364") if item in language_labels]
        languages = seeded_languages or sorted(set(claim_languages)) or ["Unknown"]
        country_code = "IN" if "IN" in country_codes else (country_codes[0] if country_codes else "XX")

        movies.append(
            {
                "wikidata_qid": qid,
                "title": title,
                "release_date": dates[0],
                "candidate_dates": dates,
                "languages": languages,
                "country_code": country_code,
                "country_codes": country_codes,
                "source_url": f"https://www.wikidata.org/wiki/{qid}",
                "verification_status": "unconfirmed",
                "selection_reason": "mediawiki_pageprops_qid_discovery_earliest_day_precision_wikidata_date",
                "merge_strategy": "earliest",
            }
        )

    by_qid: dict[str, dict] = {}
    for movie in movies:
        existing = by_qid.get(movie["wikidata_qid"])
        if not existing:
            by_qid[movie["wikidata_qid"]] = movie
            continue
        existing["candidate_dates"] = sorted(set(existing["candidate_dates"]) | set(movie["candidate_dates"]))
        existing["release_date"] = existing["candidate_dates"][0]
        existing["languages"] = sorted(set(existing["languages"]) | set(movie["languages"]))
        existing["country_codes"] = sorted(set(existing["country_codes"]) | set(movie["country_codes"]))
        if "IN" in existing["country_codes"]:
            existing["country_code"] = "IN"

    return (
        sorted(by_qid.values(), key=lambda item: (item["release_date"], item["title"].casefold(), item["wikidata_qid"])),
        label_reports,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch broad film catalogue through throttle-resilient Wikimedia APIs")
    parser.add_argument("--profile", choices=("bootstrap", "india", "global-recent", "rotate", "all-historical"), default="rotate")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--max-movies", type=int, default=MAX_MOVIES_PER_RUN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = max(1, min(MAX_MOVIES_PER_RUN, args.max_movies))
    seeds = base.build_seeds(args.profile)
    titles, metadata, category_reports = base.discover_titles(seeds, maximum)
    if not titles:
        print("No Wikipedia category film pages discovered; preserving existing catalogue.", file=sys.stderr)
        return 1

    qid_to_title, qid_reports = resolve_qids_via_wikipedia(titles)
    if not qid_to_title:
        print("No Wikidata QIDs resolved from discovered Wikipedia pages.", file=sys.stderr)
        return 1

    entities, entity_reports = fetch_entities_by_qid(qid_to_title)
    if not entities:
        print("No Wikidata entity batches resolved; preserving existing catalogue.", file=sys.stderr)
        return 1

    movies, label_reports = normalize_entities_resilient(entities, metadata)
    movies = movies[:maximum]
    if not movies:
        print("No day-precision Wikidata-backed films resolved from successful batches.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile": args.profile,
                "acquisition_path": "mediawiki_resilient",
                "merge_strategy": "earliest",
                "max_movies_per_run": maximum,
                "selection_policy": "Wikipedia category discovery -> Wikipedia pageprops QID resolution -> small direct-QID Wikidata claim batches; day precision only; partial batches retained; never overrides verified/supported dates",
                "category_report": category_reports,
                "discovered_page_titles": len(titles),
                "resolved_qids": len(qid_to_title),
                "resolved_entities": len(entities),
                "qid_resolution_report": qid_reports,
                "entity_resolution_report": entity_reports,
                "label_resolution_report": label_reports,
                "movies": movies,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    successful_categories = sum(1 for report in category_reports if report.get("status") == "ok" and report.get("pages", 0) > 0)
    deferred_entity_batches = sum(1 for report in entity_reports if report.get("status") == "deferred")
    print(
        f"resilient MediaWiki fallback wrote {len(movies)} unique movies from {len(titles)} discovered pages, "
        f"{len(qid_to_title)} QIDs and {len(entities)} resolved entities; "
        f"{successful_categories} populated categories; {deferred_entity_batches} entity batch(es) deferred"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
