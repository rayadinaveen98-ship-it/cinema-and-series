#!/usr/bin/env python3
"""Read-only movie-art discovery from exact Wikidata -> Wikipedia article identity.

Wikipedia article thumbnails (including non-free images) are *review leads*, not
permission to reproduce/post copyrighted film posters in a third-party app.
Consumes the 100-title D1 identity snapshot from the earlier completed pilot.
No D1 queries, no title searches/guesses, no production writes, no TMDB.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

WIKIDATA = "https://www.wikidata.org/w/api.php"
WIKI_SITES = ("enwiki", "tewiki", "hiwiki", "tawiki", "mlwiki", "knwiki", "bnwiki")
HOSTS = {site: "https://" + site[:-4] + ".wikipedia.org" for site in WIKI_SITES}
AGENT = "CinemaAndSeriesArtDiscovery/1.1 (read-only pilot; contact: GitHub rayadinaveen98-ship-it/cinema-and-series)"
QID = re.compile(r"Q[1-9][0-9]*\Z")


def request_json(url: str, params: dict) -> dict:
    destination = url + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(destination, headers={"User-Agent": AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=22) as result:
        payload = json.loads(result.read(4_000_000).decode("utf-8"))
    if not isinstance(payload, dict) or "error" in payload:
        raise ValueError("Wiki source replied with an API error")
    return payload


def batches(rows: list, limit: int = 20):
    for start in range(0, len(rows), limit):
        yield rows[start:start + limit]


def article_sitelinks(qids: list[str], fetch=request_json) -> tuple[dict[str, tuple[str, str]], int]:
    """Choose the best available *exact item* article, never similar-title search."""
    chosen = {}
    errors = 0
    for batch in batches(qids):
        try:
            payload = fetch(WIKIDATA, {
                "action": "wbgetentities", "ids": "|".join(batch), "props": "sitelinks",
                "sitefilter": "|".join(WIKI_SITES), "format": "json", "maxlag": "5",
            })
            entities = payload.get("entities") or {}
            if not isinstance(entities, dict):
                raise ValueError("Malformed entity response")
            for qid in batch:
                entity = entities.get(qid) or {}
                if entity.get("id") != qid:
                    continue
                links = entity.get("sitelinks") or {}
                for site in WIKI_SITES:
                    title = (links.get(site) or {}).get("title")
                    if isinstance(title, str) and title.strip():
                        chosen[qid] = (site, title.strip())
                        break
        except (ValueError, OSError, TimeoutError) as exc:
            errors += 1
    return chosen, errors


def film_page_images(sitelinks: dict[str, tuple[str, str]], fetch=request_json) -> tuple[dict[str, dict], int]:
    """Use thumbnail shown on a film's actual article; verify its Wikibase QID."""
    by_site = {}
    for qid, (site, title) in sitelinks.items():
        by_site.setdefault(site, []).append((qid, title))
    matches = {}
    errors = 0
    for site, items in by_site.items():
        base = HOSTS[site]
        for group in batches(items, 12):
            try:
                response = fetch(base + "/w/api.php", {
                    "action": "query", "titles": "|".join(t for _, t in group),
                    "redirects": "1", "prop": "pageimages|pageprops",
                    "piprop": "thumbnail|name", "pithumbsize": "640",
                    "pilicense": "any", "ppprop": "wikibase_item",
                    "format": "json", "maxlag": "5",
                })
                pages = (response.get("query") or {}).get("pages") or {}
                if not isinstance(pages, dict):
                    raise ValueError("Malformed pages response")
                requested = {qid for qid, _ in group}
                for page in pages.values():
                    if not isinstance(page, dict) or "missing" in page:
                        continue
                    qid = (page.get("pageprops") or {}).get("wikibase_item")
                    if qid not in requested:
                        continue
                    thumbnail = page.get("thumbnail") or {}
                    image_url = thumbnail.get("source")
                    if not isinstance(image_url, str) or not image_url.startswith("https://upload.wikimedia.org/"):
                        continue
                    title = page.get("title")
                    if not isinstance(title, str):
                        continue
                    # Canonical article identified by wikibase_item, not text similarity.
                    page_url = base + "/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe="()")
                    matches[qid] = {
                        "image_url": image_url,
                        "file_page_url": page_url,
                        "width": thumbnail.get("width"), "height": thumbnail.get("height"),
                        "license": "Not verified; article may contain non-free film poster",
                        "license_url": None, "artist": None,
                        "source": "wikipedia_article_pageimage",
                        "source_site": site,
                        "pageimage_filename": page.get("pageimage"),
                        "match_basis": "EXACT_PAGEPROP_WIKIBASE_ITEM",
                        "rights_status": "REVIEW_REQUIRED_NON_FREE_POSSIBLE",
                    }
            except (ValueError, OSError, TimeoutError):
                errors += 1
    return matches, errors


def merge_images(original: dict, images: dict[str, dict], link_errors: int, page_errors: int) -> dict:
    if (original.get("schema") != "existing-title-artwork-pilot-v1"
            or original.get("d1_writes") != 0 or original.get("publication_performed") is not False):
        raise ValueError("Only the completed read-only existing-title pilot can be reused")
    rows = original.get("candidates") or []
    if not isinstance(rows, list) or len(rows) > 100 or len(rows) != original.get("selected_count"):
        raise ValueError("Untrusted candidate count")
    result = dict(original)
    result["candidates"] = []
    promoted = 0
    portrait = 0
    for row in rows:
        item = dict(row)
        if item.get("approved_for_publication") is not False or item.get("production_written") is not False:
            raise ValueError("Refusing previously published/approved candidate")
        image = images.get(item.get("wikidata_qid"))
        if image and not (item.get("image") or {}).get("image_url"):
            item["image"] = image
            item["status"] = "WIKIPEDIA_ARTICLE_IMAGE_REVIEW"
            item["match_basis"] = image["match_basis"]
            item["file_name"] = image.get("pageimage_filename")
            promoted += 1
            try:
                if int(image["height"]) > int(image["width"]) * 1.25:
                    portrait += 1
            except (ValueError, TypeError):
                pass
        item["approved_for_publication"] = False
        item["production_written"] = False
        result["candidates"].append(item)
    result["schema"] = "existing-title-artwork-pilot-v1"
    result["d1_writes"] = 0
    result["publication_performed"] = False
    result["source_note"] = ("Wikipedia exact-identity pageimages; some posters are NON-FREE. "
                             "Found images are not production-approved or licensed automatically.")
    result["discovery_stats"] = {
        "selected": len(rows), "wikipedia_new_article_images": promoted,
        "portrait_article_images": portrait,
        "total_visual_candidates": sum(bool((x.get("image") or {}).get("image_url")) for x in result["candidates"]),
        "sitelink_batch_errors": link_errors, "pageimage_batch_errors": page_errors,
        "production_writes": 0,
    }
    result["status_counts"] = dict(Counter(str(x.get("status")) for x in result["candidates"]))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    original = json.loads(args.input.read_text(encoding="utf-8"))
    rows = original.get("candidates") or []
    qids = list(dict.fromkeys(str(x.get("wikidata_qid", "")) for x in rows
                              if QID.fullmatch(str(x.get("wikidata_qid", "")))))
    links, link_errors = article_sitelinks(qids)
    images, page_errors = film_page_images(links)
    result = merge_images(original, images, link_errors, page_errors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("FILM_POSTER_DISCOVERY=" + json.dumps(result["discovery_stats"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
