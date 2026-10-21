#!/usr/bin/env python3
"""Guarded publication of a small set of rightsholder-permissioned Indian film posters.

Each manifest entry is backed by a distinct Wikimedia VRT confirmation and CC
BY-SA 4.0. Publication requires exact existing title, year and Wikidata identity,
fresh Commons license metadata and the expected VRT ticket in its file page.
No new catalogue records, no fuzzy title matching, no non-free Wikipedia files.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish_commons_permissioned_pilot import _http_get_json, parse_d1, sq

LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# Pinned independently documented copyright-holder permission records.
# Do not add Commons uploads without checked VRT evidence.
POSTERS = (
    dict(title="Yaanai", year=2022, country="IN", file="Yaanai Poster.jpg",
         author="Drumsticks Productions", ticket="2022031910001078"),
    dict(title="Lahiri Lahiri Lahirilo", year=2002, country="IN",
         file="YVS Laahiri Laahiri Laahiri Lo 01.tif",
         author="YVS Chowdary", ticket="2019011910002621"),
    dict(title="Nasha Jurm Aur Gangsters", year=2023, country="IN",
         file="Nasha Jurm Aur Gangsters Official Poster.jpg",
         author="Patras Glam Ent", ticket="2023041510002599"),
    dict(title="Vrithakrithiyulla Chathuram", year=2020, country="IN",
         file="VrithakrithiyilullaChathuramPoster.jpg",
         author="Krishand R K", ticket="2020051710001992"),
)

def verify_manifest():
    seen = set()
    for entry in POSTERS:
        assert entry["title"] and 1900 <= entry["year"] <= 2026
        assert re.fullmatch(r"20\d{14}", entry["ticket"])
        assert entry["ticket"] not in seen
        seen.add(entry["ticket"])

def matches(rows: list[dict], entry: dict) -> list[dict]:
    candidates = []
    for row in rows:
        if (str(row.get("title") or "").casefold().strip()
                != entry["title"].casefold()
                or row.get("release_year") != entry["year"]
                or (row.get("country_code") or "").upper() not in ("IN", "XX")
                or not re.fullmatch(r"Q[1-9][0-9]*", str(row.get("wikidata_qid") or ""))):
            continue
        if row.get("source_table") not in ("movies", "catalogue_titles"):
            continue
        candidates.append(row)
    qids = {x["wikidata_qid"] for x in candidates}
    if len(qids) != 1 or not 1 <= len(candidates) <= 2:
        return []
    if len(candidates) == 2 and {x["source_table"] for x in candidates} != {"movies", "catalogue_titles"}:
        return []
    # A title can have a day-precision and a year-precision representation;
    # publish both only when they are the *same Wikidata film QID*.
    return candidates

def verified_metadata(entry: dict, fetch=_http_get_json) -> dict:
    name = "File:" + entry["file"]
    data = fetch(COMMONS_API, {
        "action": "query", "titles": name, "prop": "imageinfo|revisions",
        "iiprop": "url|extmetadata|size", "iiurlwidth": "680",
        "rvprop": "content", "rvslots": "main", "format": "json", "maxlag": "5",
    })
    pages = (data.get("query") or {}).get("pages") or {}
    if len(pages) != 1:
        raise ValueError("ambiguous_file")
    page = next(iter(pages.values()))
    if page.get("title") != name:
        raise ValueError("file_changed")
    details = (page.get("imageinfo") or [{}])[0]
    license_data = details.get("extmetadata") or {}
    license_name = str((license_data.get("LicenseShortName") or {}).get("value") or "")
    license_url = str((license_data.get("LicenseUrl") or {}).get("value") or "")
    if license_name != "CC BY-SA 4.0" or license_url.rstrip("/") != LICENSE.rstrip("/"):
        raise ValueError("license_mismatch")
    import urllib.parse
    url = str(details.get("thumburl") or details.get("url") or "")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("thumb.wikimedia.org", "upload.wikimedia.org"):
        raise ValueError("untrusted_image_host")
    width = int(details.get("thumbwidth") or details.get("width") or 0)
    height = int(details.get("thumbheight") or details.get("height") or 0)
    if width < 250 or height < 330 or height < width * 1.2:
        raise ValueError("not_a_portrait_poster")
    # VRT permission notices are often transcluded from permission templates
    # or structured Commons file metadata; the raw file revision alone cannot
    # reliably expose them. Verify the independently rendered Commons page.
    rendered = fetch(COMMONS_API, {
        "action":"parse", "page":name, "prop":"text",
        "format":"json", "maxlag":"5",
    })
    parsed_page = rendered.get("parse") or {}
    if parsed_page.get("title") != name:
        raise ValueError("rendered_file_identity_mismatch")
    html = str((parsed_page.get("text") or {}).get("*") or "")
    if (entry["ticket"] not in html
            or "VRT" not in html
            or "permission" not in html.lower()):
        raise ValueError("copyright_holder_vrt_proof_missing")
    return {"url":url, "width":width, "height":height, "license":license_url,
            "source":"https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(entry["file"].replace(" ", "_")),
            "ticket":entry["ticket"]}

def sql(entry: dict, matches: list[dict], img: dict) -> str:
    if not matches:
        raise ValueError("No unambiguous exact existing movie")
    aid = "commons-vrt-" + entry["ticket"] + "-poster"
    credit = f'{entry["title"]} theatrical poster © {entry["author"]}; CC BY-SA 4.0; image used unmodified; Wikimedia VRT #{entry["ticket"]}'
    values = [
        sq(aid), "'poster'", "'wikimedia_commons_vrt'", sq(entry["file"]), sq(img["source"]),
        sq(img["url"]), "''", "''", "'OPEN_LICENSE_VERIFIED'", "'OPEN_LICENSE'", "'PROVIDER_CDN'",
        "1",sq(credit),sq(entry["author"]),sq(LICENSE),
        "strftime('%Y-%m-%dT%H:%M:%SZ','now')",sq("Wikimedia VRT "+entry["ticket"]),
        str(img["width"]),str(img["height"]),str(round(img["width"]/img["height"],5)),"1.0"
    ]
    statements = [
        "-- Audited license and individual copyright-holder VRT ticket.\n"
        "INSERT OR IGNORE INTO artwork_assets "
        "(id,asset_type,source_key,source_asset_id,source_page_url,delivery_url,"
        "language_code,territory_code,publication_state,rights_basis,hosting_mode,"
        "attribution_required,attribution_text,creator_text,rights_reference,"
        "rights_verified_at,rights_verified_by,width,height,aspect_ratio,quality_score) "
        "SELECT " + ",".join(values) + " WHERE EXISTS (SELECT 1 FROM " +
        matches[0]["source_table"] + " WHERE id=" + sq(matches[0]["id"]) +
        " AND wikidata_qid=" + sq(matches[0]["wikidata_qid"]) + ");"
    ]
    for row in matches:
        table, source_id = row["source_table"], row["id"]
        year_match = ("substr(release_date,1,4)=" + sq(str(entry["year"])))
        if table == "catalogue_titles":
            year_match = "release_year=" + str(entry["year"])
        conditions = (f"id={sq(source_id)} AND wikidata_qid={sq(row['wikidata_qid'])}"
                      f" AND title={sq(entry['title'])} COLLATE NOCASE AND {year_match}")
        link_id = "link-" + aid + "-" + source_id
        statements.append(
            "INSERT OR IGNORE INTO title_artwork_links "
            "(id,media_type,source_table,source_id,asset_id,presentation_role,language_code,territory_code) "
            "SELECT " + ",".join((sq(link_id),"'movie'",sq(table),sq(source_id),sq(aid),"'poster'","''","''")) +
            f" WHERE EXISTS (SELECT 1 FROM {table} WHERE {conditions}) "
            f"AND EXISTS (SELECT 1 FROM artwork_assets WHERE id={sq(aid)});"
        )
    return "\n".join(statements)+"\n"

def prepare(exact: list[dict], catalogue: list[dict], output_dir: Path, fetch=_http_get_json) -> dict:
    verify_manifest()
    rows = [{**x, "source_table":"movies"} for x in exact] + [
        {**x, "source_table":"catalogue_titles"} for x in catalogue]
    output_dir.mkdir(parents=True,exist_ok=True)
    report = {"schema":"verified-artwork-batch-v2","selected":len(POSTERS),"ready":[],"held":[],
              "planned_sql_writes":0,"published":0}
    for entry in POSTERS:
        found = matches(rows,entry)
        if not found:
            report["held"].append({"title":entry["title"],"reason":"not_one_exact_year_qid_existing_film"})
            continue
        try:
            img=verified_metadata(entry,fetch)
        except (ValueError, OSError, TimeoutError, KeyError) as exc:
            report["held"].append({"title":entry["title"],"reason":"source_rights_or_image_check_failed",
                                   "detail":str(exc)[:140]})
            continue
        sql_path=output_dir/("vrts-"+entry["ticket"]+".sql")
        sql_path.write_text(sql(entry,found,img),encoding="utf-8")
        report["ready"].append({"title":entry["title"],"year":entry["year"],
            "source_file":entry["file"],"source_url":img["source"],"delivery_url":img["url"],
            "ticket":entry["ticket"],"asset_id":"commons-vrt-"+entry["ticket"]+"-poster",
            "license":LICENSE,
            "source_ids":[{"table":row["source_table"],"id":row["id"],"qid":row["wikidata_qid"]} for row in found],
            "sql_filename":sql_path.name})
    report["planned_sql_writes"]=len(report["ready"])
    return report

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--exact",required=True,type=Path)
    parser.add_argument("--catalogue",required=True,type=Path)
    parser.add_argument("--out-dir",required=True,type=Path)
    args=parser.parse_args()
    report=prepare(parse_d1(args.exact),parse_d1(args.catalogue),args.out_dir)
    (args.out_dir/"preview.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("VRT_BATCH_PREVIEW="+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
