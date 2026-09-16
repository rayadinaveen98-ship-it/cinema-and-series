#!/usr/bin/env python3
"""Build provenance-aware artwork updates for the Cinema & Series catalogue.

Priority:
1. First-party release evidence pages/videos already curated by the project.
2. Wikidata P18 images resolved through Wikimedia Commons for rows that still
   have no artwork.

The script never guesses image URLs from movie titles and never overwrites
first-party artwork with open-data artwork. It emits SQL for D1 plus a compact
JSON report for CI review.
"""
from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_RELEASES = ROOT / "data/official/releases.json"
WIKIDATA_PAYLOAD = ROOT / "data/generated/wikidata-india.json"
OUT_SQL = ROOT / "data/generated/artwork-upsert.sql"
OUT_REPORT = ROOT / "data/generated/artwork-report.json"
USER_AGENT = "CinemaAndSeries/0.2 (public GitHub project; artwork enrichment)"
TIMEOUT = 18
MAX_PAGE_BYTES = 1_200_000


class MetaImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        values = {key.lower(): value for key, value in attrs if value is not None}
        key = (values.get("property") or values.get("name") or "").lower()
        if key not in {"og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"}:
            return
        content = values.get("content")
        if content:
            self.images.append(html.unescape(content.strip()))


def sql_quote(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def https_url(value: str | None, base: str | None = None) -> str | None:
    if not value:
        return None
    candidate = urllib.parse.urljoin(base or "", value.strip())
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    return candidate


def request_bytes(url: str, *, method: str = "GET", limit: int | None = None) -> bytes:
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        if method == "HEAD":
            return b""
        return response.read(limit or -1)


def youtube_video_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host in {"youtube.com", "m.youtube.com"}:
        candidate = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
    else:
        return None
    return candidate if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", candidate or "") else None


def youtube_artwork(url: str) -> str | None:
    video_id = youtube_video_id(url)
    if not video_id:
        return None
    candidates = [
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    ]
    for candidate in candidates:
        try:
            request_bytes(candidate, method="HEAD")
            return candidate
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            continue
    return candidates[-1]


def official_page_artwork(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    # Root homepages are commonly generic brand images rather than movie art.
    if parsed.path in {"", "/"}:
        return None
    try:
        body = request_bytes(url, limit=MAX_PAGE_BYTES).decode("utf-8", errors="ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None
    parser = MetaImageParser()
    parser.feed(body)
    for image in parser.images:
        safe = https_url(image, url)
        if safe:
            return safe
    return None


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def json_get(url: str) -> dict:
    return json.loads(request_bytes(url).decode("utf-8"))


def wikidata_p18(qids: list[str]) -> dict[str, str]:
    output: dict[str, str] = {}
    for batch in chunks(qids, 50):
        params = urllib.parse.urlencode(
            {
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "claims",
                "format": "json",
                "origin": "*",
            }
        )
        try:
            payload = json_get(f"https://www.wikidata.org/w/api.php?{params}")
        except Exception:
            continue
        for qid, entity in payload.get("entities", {}).items():
            claims = entity.get("claims", {}).get("P18", [])
            for claim in claims:
                value = (
                    claim.get("mainsnak", {})
                    .get("datavalue", {})
                    .get("value")
                )
                if isinstance(value, str) and value.strip():
                    output[qid] = value.strip()
                    break
    return output


def commons_image_info(filenames: list[str]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for batch in chunks(filenames, 30):
        titles = "|".join(f"File:{name}" for name in batch)
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "titles": titles,
                "prop": "imageinfo",
                "iiprop": "url|size",
                "iiurlwidth": "1200",
                "format": "json",
                "origin": "*",
            }
        )
        try:
            payload = json_get(f"https://commons.wikimedia.org/w/api.php?{params}")
        except Exception:
            continue
        for page in payload.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            info = (page.get("imageinfo") or [{}])[0]
            if not title.startswith("File:") or not info:
                continue
            key = title[5:].replace("_", " ").casefold()
            image_url = https_url(info.get("thumburl") or info.get("url"))
            source_url = https_url(info.get("descriptionurl"))
            if image_url:
                output[key] = {
                    "url": image_url,
                    "source_url": source_url,
                    "width": int(info.get("width") or 0),
                    "height": int(info.get("height") or 0),
                }
    return output


def official_updates() -> list[dict]:
    if not OFFICIAL_RELEASES.exists():
        return []
    payload = json.loads(OFFICIAL_RELEASES.read_text(encoding="utf-8"))
    updates: list[dict] = []
    for release in payload.get("releases", []):
        source_url = https_url(release.get("source_url"))
        if not source_url:
            continue
        source_type = release.get("source_type") or "official"
        if source_type == "official_youtube":
            image_url = youtube_artwork(source_url)
            kind = "backdrop"
        else:
            image_url = official_page_artwork(source_url)
            kind = "backdrop"
        if not image_url:
            continue
        updates.append(
            {
                "title": release["title"],
                "release_date": release["release_date"],
                "poster_url": None,
                "backdrop_url": image_url,
                "artwork_source": source_type,
                "artwork_source_url": source_url,
                "artwork_kind": kind,
                "priority": 100,
            }
        )
    return updates


def wikidata_updates() -> list[dict]:
    if not WIKIDATA_PAYLOAD.exists():
        return []
    payload = json.loads(WIKIDATA_PAYLOAD.read_text(encoding="utf-8"))
    qids = [movie.get("wikidata_qid") for movie in payload.get("movies", [])]
    qids = [qid for qid in qids if isinstance(qid, str) and re.fullmatch(r"Q\d+", qid)]
    if not qids:
        return []
    images = wikidata_p18(qids)
    if not images:
        return []
    commons = commons_image_info(sorted(set(images.values())))
    updates: list[dict] = []
    for qid, filename in images.items():
        info = commons.get(filename.replace("_", " ").casefold())
        if not info:
            continue
        width, height = info["width"], info["height"]
        portrait = height > width * 1.12 if width and height else False
        updates.append(
            {
                "wikidata_qid": qid,
                "poster_url": info["url"] if portrait else None,
                "backdrop_url": None if portrait else info["url"],
                "artwork_source": "wikimedia_commons",
                "artwork_source_url": info.get("source_url") or f"https://www.wikidata.org/wiki/{qid}",
                "artwork_kind": "poster" if portrait else "backdrop",
                "priority": 20,
            }
        )
    return updates


def build_sql(wiki: list[dict], official: list[dict]) -> str:
    statements = [
        "-- Generated by scripts/artwork_refresh.py",
        "-- Open-data artwork only fills empty rows; first-party artwork then wins.",
    ]
    now = "CURRENT_TIMESTAMP"
    for item in wiki:
        statements.append(
            "UPDATE movies SET "
            f"poster_url = COALESCE(poster_url, {sql_quote(item['poster_url'])}), "
            f"backdrop_url = COALESCE(backdrop_url, {sql_quote(item['backdrop_url'])}), "
            f"artwork_source = CASE WHEN poster_url IS NULL AND backdrop_url IS NULL THEN {sql_quote(item['artwork_source'])} ELSE artwork_source END, "
            f"artwork_source_url = CASE WHEN poster_url IS NULL AND backdrop_url IS NULL THEN {sql_quote(item['artwork_source_url'])} ELSE artwork_source_url END, "
            f"artwork_updated_at = CASE WHEN poster_url IS NULL AND backdrop_url IS NULL THEN {now} ELSE artwork_updated_at END "
            f"WHERE wikidata_qid = {sql_quote(item['wikidata_qid'])};"
        )
    for item in official:
        statements.append(
            "UPDATE movies SET "
            f"poster_url = COALESCE({sql_quote(item['poster_url'])}, poster_url), "
            f"backdrop_url = COALESCE({sql_quote(item['backdrop_url'])}, backdrop_url), "
            f"artwork_source = {sql_quote(item['artwork_source'])}, "
            f"artwork_source_url = {sql_quote(item['artwork_source_url'])}, "
            f"artwork_updated_at = {now} "
            f"WHERE title = {sql_quote(item['title'])} AND release_date = {sql_quote(item['release_date'])};"
        )
    return "\n".join(statements) + "\n"


def main() -> int:
    OUT_SQL.parent.mkdir(parents=True, exist_ok=True)
    wiki = wikidata_updates()
    official = official_updates()
    OUT_SQL.write_text(build_sql(wiki, official), encoding="utf-8")
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy": "first-party evidence artwork overrides; Wikimedia Commons only fills missing artwork; no title guessing",
        "wikimedia_candidates": len(wiki),
        "official_candidates": len(official),
        "official_titles": [item["title"] for item in official],
    }
    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"artwork refresh: {len(wiki)} Wikimedia candidates, {len(official)} first-party candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
