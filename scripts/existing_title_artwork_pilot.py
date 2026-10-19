#!/usr/bin/env python3
"""Build a 100-existing-title, source-only artwork pilot from a D1 snapshot.

Read-only. No title imports, no production writes, no automated image publication.
Uses Wikidata QID -> P18 -> Wikimedia Commons, retaining file-specific license
metadata for review. Does not infer a poster from a similar title or release year.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

QID = re.compile(r"Q[1-9]\d*\Z")
API = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
AGENT = "CinemaAndSeriesExistingArtworkPilot/1.0 (source-only; GitHub: rayadinaveen98-ship-it/cinema-and-series)"
MAX_TITLES = 100
QUOTAS = {"movies": 30, "catalogue_titles": 60, "series_titles": 10}
SOURCE_TYPE = {"movies": "movie", "catalogue_titles": "movie", "series_titles": "series"}


def read_wrangle_rows(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("result"), list):
        payload = payload["result"]
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("Expected Wrangler JSON result batches")
    rows = []
    for batch in payload:
        if not isinstance(batch, dict) or not isinstance(batch.get("results"), list):
            raise ValueError("Malformed D1 batch")
        if not all(isinstance(row, dict) for row in batch["results"]):
            raise ValueError("Malformed D1 row")
        rows.extend(batch["results"])
    return rows


def select_existing_titles(samples: dict[str, list[dict]], limit: int = MAX_TITLES) -> list[dict]:
    if not 1 <= limit <= MAX_TITLES:
        raise ValueError("Pilot must contain between 1 and 100 titles")
    eligible = {name: [] for name in QUOTAS}
    qid_used = set()
    for name in QUOTAS:
        for raw in samples.get(name, []):
            qid = raw.get("wikidata_qid")
            title = str(raw.get("title") or "").strip()
            row_id = str(raw.get("id") or "").strip()
            if (not isinstance(qid, str) or not QID.fullmatch(qid)
                    or not title or not row_id or raw.get("has_poster") in (1, True)):
                continue
            year = raw.get("year")
            if year is not None and (not isinstance(year, int) or year < 1888 or year > 2200):
                continue
            eligible[name].append({
                "source_table": name, "media_type": SOURCE_TYPE[name],
                "source_id": row_id, "wikidata_qid": qid,
                "title": title, "year": year,
                "language": str(raw.get("language_name") or "Unknown"),
                "country": str(raw.get("country_code") or "XX"),
            })
    # Movies table wins duplicate identities over the year-only catalogue;
    # originals in the D1 rows are otherwise never modified or merged.
    selected = []
    for name in QUOTAS:
        taken = 0
        for row in eligible[name]:
            if row["wikidata_qid"] in qid_used or taken >= min(limit, QUOTAS[name]):
                continue
            selected.append(row)
            qid_used.add(row["wikidata_qid"])
            taken += 1
    for name in QUOTAS:
        for row in eligible[name]:
            if len(selected) >= limit:
                break
            if row["wikidata_qid"] not in qid_used:
                selected.append(row)
                qid_used.add(row["wikidata_qid"])
    return selected[:limit]


def api_get(base: str, params: dict) -> dict:
    url = base + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        data = json.loads(response.read(4_000_000).decode("utf-8"))
    if not isinstance(data, dict) or "error" in data:
        raise ValueError("Source response invalid or throttled")
    return data


def batches(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def p18_by_qid(qids: list[str], fetch=api_get) -> dict[str, str]:
    result = {}
    for subset in batches(qids, 20):
        response = fetch(API, {"action": "wbgetentities", "ids": "|".join(subset),
                               "props": "claims", "format": "json", "maxlag": "5"})
        entities = response.get("entities", {})
        if not isinstance(entities, dict):
            raise ValueError("Malformed Wikidata entities")
        for qid in subset:
            entity = entities.get(qid)
            if not isinstance(entity, dict) or entity.get("missing") is not None or entity.get("id", qid) != qid:
                continue
            claims = (entity.get("claims") or {}).get("P18") or []
            images = []
            for claim in claims:
                if claim.get("rank") == "deprecated":
                    continue
                value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(value, str) and value.strip():
                    images.append(value.strip())
            # A single exact-QID image claim is reviewable; several are ambiguous.
            if len(set(images)) == 1:
                result[qid] = images[0]
    return result


def commons_by_filename(names: list[str], fetch=api_get) -> dict[str, dict]:
    result = {}
    for subset in batches(sorted(set(names)), 20):
        response = fetch(COMMONS, {
            "action": "query", "titles": "|".join("File:" + n for n in subset),
            "prop": "imageinfo", "iiprop": "url|size|extmetadata",
            "iiurlwidth": "650", "format": "json", "maxlag": "5",
        })
        pages = (response.get("query") or {}).get("pages") or {}
        if not isinstance(pages, dict):
            raise ValueError("Malformed Commons pages")
        for page in pages.values():
            title = page.get("title", "")
            info = (page.get("imageinfo") or [None])[0]
            if not title.startswith("File:") or not isinstance(info, dict):
                continue
            meta = info.get("extmetadata") or {}
            def metadata(key):
                value = (meta.get(key) or {}).get("value") or ""
                return html.unescape(re.sub(r"<[^>]*>", "", str(value))).strip()
            def https(value):
                p = urllib.parse.urlparse(str(value or ""))
                return str(value) if p.scheme == "https" and p.hostname else None
            result[title[5:].replace("_", " ").casefold()] = {
                "image_url": https(info.get("thumburl") or info.get("url")),
                "file_page_url": https(info.get("descriptionurl")),
                "width": info.get("width"), "height": info.get("height"),
                "license": metadata("LicenseShortName"),
                "license_url": https(metadata("LicenseUrl")),
                "artist": metadata("Artist")[:250],
                "attribution_required": metadata("AttributionRequired"),
                "restrictions": metadata("Restrictions"),
            }
    return result


def build_pilot(samples: dict[str, list[dict]], *, limit: int = MAX_TITLES,
                fetch=api_get, discover: bool = True) -> dict:
    selected = select_existing_titles(samples, limit)
    file_claims = p18_by_qid([row["wikidata_qid"] for row in selected], fetch) if discover and selected else {}
    commons = commons_by_filename(list(file_claims.values()), fetch) if file_claims else {}
    candidates = []
    statuses = Counter()
    for title in selected:
        qid = title["wikidata_qid"]
        filename = file_claims.get(qid)
        image = commons.get(filename.replace("_", " ").casefold()) if filename else None
        if not filename:
            status = "NO_SINGLE_P18_CLAIM"
        elif not image or not image.get("image_url") or not image.get("file_page_url"):
            status = "IMAGE_UNAVAILABLE"
        elif not image.get("license") or not image.get("license_url"):
            status = "RIGHTS_REVIEW_NEEDED"
        else:
            status = "REVIEW_IMAGE_AND_RIGHTS"
        statuses[status] += 1
        candidates.append({
            **title, "status": status, "file_name": filename,
            "image": image, "match_basis": "EXACT_WIKIDATA_QID_P18" if filename else None,
            "approved_for_publication": False,
            "production_written": False,
        })
    return {
        "schema": "existing-title-artwork-pilot-v1",
        "read_only": True, "d1_writes": 0, "production_updates": 0,
        "publication_performed": False, "all_titles_from_existing_d1_snapshot": True,
        "selected_count": len(selected), "selected_by_table": dict(Counter(c["source_table"] for c in candidates)),
        "status_counts": dict(sorted(statuses.items())),
        "unmatched_or_held": sum(v for k, v in statuses.items() if k != "REVIEW_IMAGE_AND_RIGHTS"),
        "sources": ["Wikidata P18", "Wikimedia Commons file metadata"],
        "warning": "File identity is not a copyright license. All candidates require rights and visual review before publication.",
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for table in QUOTAS:
        parser.add_argument("--" + table.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offline", action="store_true", help="Selection-only dry run")
    args = parser.parse_args()
    samples = {table: read_wrangle_rows(getattr(args, table)) for table in QUOTAS}
    pilot = build_pilot(samples, limit=args.limit, discover=not args.offline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(pilot, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print("EXISTING_ARTWORK_PILOT=" + json.dumps({
        key: pilot[key] for key in ("selected_count", "selected_by_table", "status_counts",
                                    "d1_writes", "publication_performed")
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
