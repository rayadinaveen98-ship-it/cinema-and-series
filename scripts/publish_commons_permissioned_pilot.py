#!/usr/bin/env python3
"""One evidence-backed real-poster publication to an existing D1 film.

The Indian Priest poster has Wikimedia VRT-confirmed rightsholder permission:
https://commons.wikimedia.org/wiki/File:The_Indian_Priest_Film_Poster.jpg
VRT ticket 2024032810002841; image is CC BY-SA 4.0.
No poster in the earlier 70-title preview was automatically rights-approved.
This first publication is deliberately pinned to this single verified source.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

FILE = "The Indian Priest Film Poster.jpg"
SOURCE = "https://commons.wikimedia.org/wiki/File:The_Indian_Priest_Film_Poster.jpg"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
VRT_TICKET = "2024032810002841"
ASSET_ID = "commons-vrt-2024032810002841-the-indian-priest-poster"
TITLE = "The Indian Priest"
YEAR = 2016


def parse_d1(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Unexpected Wrangler D1 response")
    out = []
    for result in payload:
        if not result.get("success", False) or not isinstance(result.get("results"), list):
            raise ValueError("D1 query failed or returned error")
        out.extend(result["results"])
    return out


def match_existing(exact: list[dict], catalogue: list[dict]) -> dict | None:
    """Allow one exact film identity only, never add titles or guess by similarity."""
    candidates = []
    for source, records in (("movies", exact), ("catalogue_titles", catalogue)):
        for r in records:
            if (str(r.get("title", "")).strip().casefold() != TITLE.casefold()
                    or str(r.get("release_year")) != str(YEAR)
                    or not str(r.get("id") or "")
                    or not re.fullmatch(r"Q[1-9]\d*", str(r.get("wikidata_qid") or ""))):
                continue
            country = str(r.get("country_code") or "").upper()
            if country not in ("IN", "SE", "XX"):
                continue
            candidates.append({**r, "source_table": source})
    qids = {r["wikidata_qid"] for r in candidates}
    if len(qids) != 1:
        return None
    if len(candidates) not in (1, 2):
        return None
    if len(candidates) == 2 and {r["source_table"] for r in candidates} != {"movies", "catalogue_titles"}:
        return None
    return next((r for r in candidates if r["source_table"] == "movies"), candidates[0])


def fetch_commons_image(fetch=None) -> dict:
    """Inspect actual file's Commons CC BY-SA metadata before any D1 write."""
    if fetch is None:
        fetch = _http_get_json
    info = fetch("https://commons.wikimedia.org/w/api.php", {
        "action": "query", "titles": "File:" + FILE, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": "680",
        "format": "json", "maxlag": "5",
    })
    pages = (info.get("query") or {}).get("pages") or {}
    if len(pages) != 1:
        raise ValueError("Source file metadata is ambiguous")
    page = next(iter(pages.values()))
    if page.get("title") != "File:" + FILE:
        raise ValueError("Commons file title changed")
    details = (page.get("imageinfo") or [None])[0] or {}
    extra = details.get("extmetadata") or {}
    license_name = str((extra.get("LicenseShortName") or {}).get("value") or "")
    license_link = str((extra.get("LicenseUrl") or {}).get("value") or "")
    if license_name != "CC BY-SA 4.0" or license_link.rstrip("/") != LICENSE_URL.rstrip("/"):
        raise ValueError("Source license is not verified CC BY-SA 4.0")
    url = details.get("thumburl") or details.get("url") or ""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ("upload.wikimedia.org", "thumb.wikimedia.org"):
        raise ValueError("Image URL is not a trusted Wikimedia image CDN: " + str(parsed.hostname))
    width = int(details.get("thumbwidth") or details.get("width") or 0)
    height = int(details.get("thumbheight") or details.get("height") or 0)
    if not 200 <= width <= 5000 or not 200 <= height <= 5000 or height <= width:
        raise ValueError("Source must be a usable portrait theatrical poster")
    return {"url": url, "width": width, "height": height,
            "license": license_name, "license_url": LICENSE_URL, "source_page": SOURCE,
            "vrt_ticket": VRT_TICKET}


def _http_get_json(url: str, params: dict) -> dict:
    endpoint = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(endpoint, headers={
        "User-Agent": "CinemaAndSeries/1.0 (verified free-poster pilot; github.com/rayadinaveen98-ship-it/cinema-and-series)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read(1_500_000))


def sq(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_sql(row: dict, meta: dict) -> str:
    """Always tied to a single exact existing ID and QID; insert-only."""
    table = row["source_table"]
    if table not in ("movies", "catalogue_titles"):
        raise ValueError("Only films may be published with this poster")
    source_id, qid = str(row["id"]), str(row["wikidata_qid"])
    if not re.fullmatch(r"Q[1-9]\d*", qid):
        raise ValueError("Unsafe Wikidata identity")
    attr = ("The Indian Priest film poster © Holdcaulfield1951; "
            "CC BY-SA 4.0; original unmodified; VRT ticket " + VRT_TICKET)
    link_id = "link-" + ASSET_ID + "-" + source_id
    film_constraint = ("id=" + sq(source_id) + " AND wikidata_qid=" + sq(qid) +
                       " AND title=" + sq(TITLE) + " COLLATE NOCASE")
    if table == "movies":
        film_constraint += " AND substr(release_date,1,4)=" + sq(str(YEAR))
    else:
        film_constraint += " AND release_year=" + str(YEAR)
    return (
        "-- Explicit VRT rightsholder permission; CC BY-SA 4.0, attribution mandatory.\n"
        "INSERT OR IGNORE INTO artwork_assets "
        "(id,asset_type,source_key,source_asset_id,source_page_url,delivery_url,"
        "language_code,territory_code,publication_state,rights_basis,hosting_mode,"
        "attribution_required,attribution_text,creator_text,rights_reference,"
        "rights_verified_at,rights_verified_by,width,height,aspect_ratio,quality_score)"
        " SELECT " +
        ",".join((sq(ASSET_ID),"'poster'","'wikimedia_commons_vrt'",
                  sq(FILE),sq(SOURCE),sq(meta["url"]),"''","''",
                  "'OPEN_LICENSE_VERIFIED'","'OPEN_LICENSE'","'PROVIDER_CDN'",
                  "1",sq(attr),sq("Holdcaulfield1951"),sq(LICENSE_URL),
                  "strftime('%Y-%m-%dT%H:%M:%SZ','now')",sq("Wikimedia VRT " + VRT_TICKET),
                  str(meta["width"]),str(meta["height"]),
                  str(round(meta["width"]/meta["height"],5)),"1.0")) +
        " WHERE EXISTS (SELECT 1 FROM " + table + " WHERE " + film_constraint + ");\n"
        "INSERT OR IGNORE INTO title_artwork_links "
        "(id,media_type,source_table,source_id,asset_id,presentation_role,language_code,territory_code)"
        " SELECT " +
        ",".join((sq(link_id),"'movie'",sq(table),sq(source_id),
                  sq(ASSET_ID),"'poster'","''","''")) +
        " WHERE EXISTS (SELECT 1 FROM " + table + " WHERE " + film_constraint + ")"
        " AND EXISTS (SELECT 1 FROM artwork_assets WHERE id=" + sq(ASSET_ID) + ");\n"
    )


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--exact",type=Path,required=True)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    matched = match_existing(parse_d1(args.exact), parse_d1(args.catalogue))
    report = {
        "film": TITLE, "year": YEAR, "source_page": SOURCE,
        "source_license": "CC BY-SA 4.0 with VRT-verified permission",
        "vrt_ticket": VRT_TICKET, "source_table": matched["source_table"] if matched else None,
        "source_id": matched["id"] if matched else None,
        "source_qid": matched["wikidata_qid"] if matched else None,
        "published": False, "reason": "no_unique_existing_2016_film_identity" if not matched else "pending_image_metadata",
    }
    if matched:
        try:
            meta = fetch_commons_image()
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(build_sql(matched,meta),encoding="utf-8")
            report["reason"] = "ready_to_publish"
            report["delivery_url"] = meta["url"]
            report["dimensions"] = [meta["width"],meta["height"]]
        except (OSError,TimeoutError,ValueError) as exc:
            report["reason"] = "source_metadata_unverified"
            report["verification_error"] = str(exc)[:240]
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PERMISSIONED_POSTER_PREP="+json.dumps(report,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
