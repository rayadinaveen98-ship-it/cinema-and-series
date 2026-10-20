#!/usr/bin/env python3
"""Render a safe, local artwork contact sheet and CSV for visual review.

Input: existing-title-artwork-pilot-v1 JSON. No network, image copying, production
updates, asset licensing, or automatic publication. The static HTML may request
Wikimedia thumbnails when opened by a reviewer; no page scripts are generated.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "existing-title-artwork-pilot-v1"
IMAGE_HOSTS = {"upload.wikimedia.org", "commons.wikimedia.org"}
FILE_HOSTS = {"commons.wikimedia.org", "en.wikipedia.org", "te.wikipedia.org", "hi.wikipedia.org", "ta.wikipedia.org", "ml.wikipedia.org", "kn.wikipedia.org", "bn.wikipedia.org"}
CSV_FIELDS = [
    "source_table", "source_id", "wikidata_qid", "title", "year", "language",
    "country", "status", "image_shape", "file_name", "file_page_url",
    "license", "license_url", "artist", "review_decision", "review_notes",
]


def safe_url(raw: object, allowed_hosts: set[str]) -> str:
    """Allow only exact, HTTPS-hosted image / Commons file destinations."""
    if not isinstance(raw, str):
        return ""
    try:
        parsed = urlsplit(raw)
        if (parsed.scheme != "https" or parsed.hostname not in allowed_hosts
                or parsed.username or parsed.password or parsed.port
                or not parsed.path.startswith("/") or any(ord(c) < 32 for c in raw)):
            return ""
    except ValueError:
        return ""
    return raw


def safe_rights_url(raw: object) -> str:
    """Rights links can be third-party HTTPS, but not script or data URLs."""
    if not isinstance(raw, str):
        return ""
    try:
        parsed = urlsplit(raw)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return ""
    except ValueError:
        return ""
    return raw


def image_shape(image: dict) -> str:
    """Orientation hint only: a portrait P18 photo is not automatically a poster."""
    try:
        w, h = float(image.get("width")), float(image.get("height"))
        if not math.isfinite(w) or not math.isfinite(h) or w <= 0 or h <= 0:
            return "unknown"
    except (TypeError, ValueError, OverflowError):
        return "unknown"
    if h >= 1.25 * w:
        return "portrait"
    if w >= 1.25 * h:
        return "landscape"
    return "square-ish"


def validate_pilot(pilot: dict) -> list[dict]:
    if (not isinstance(pilot, dict) or pilot.get("schema") != SCHEMA
            or pilot.get("read_only") is not True
            or pilot.get("publication_performed") is not False
            or pilot.get("d1_writes") != 0):
        raise ValueError("Artwork pilot must be the read-only, unpublished schema")
    candidates = pilot.get("candidates")
    if not isinstance(candidates, list) or len(candidates) > 100:
        raise ValueError("Expected at most 100 existing title candidates")
    if pilot.get("selected_count") != len(candidates):
        raise ValueError("Missing or unexpected review candidates")
    identities = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Malformed candidate")
        if candidate.get("approved_for_publication") is not False or candidate.get("production_written") is not False:
            raise ValueError("Refusing any candidate marked as published or approved")
        source_table = candidate.get("source_table")
        if source_table not in ("movies", "catalogue_titles", "series_titles"):
            raise ValueError("Unknown title table")
        identity = (source_table, candidate.get("source_id"))
        if not identity[1] or identity in identities:
            raise ValueError("Missing or duplicate database identity")
        identities.add(identity)
    return candidates


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def card(candidate: dict, index: int) -> str:
    image = candidate.get("image") if isinstance(candidate.get("image"), dict) else {}
    shape = image_shape(image)
    status = str(candidate.get("status") or "UNKNOWN")
    thumb = safe_url(image.get("image_url"), IMAGE_HOSTS)
    file_url = safe_url(image.get("file_page_url"), FILE_HOSTS)
    license_url = safe_rights_url(image.get("license_url"))
    picture = (
        '<img src="' + esc(thumb) + '" loading="lazy" referrerpolicy="no-referrer" alt="Candidate image for ' +
        esc(candidate.get("title")) + '">'
        if thumb else '<div class="no-image">No usable thumbnail</div>'
    )
    attribution = esc(image.get("artist") or "Not provided")
    link = (
        '<a href="' + esc(file_url) + '" target="_blank" rel="noopener noreferrer">Open source article/file</a>'
        if file_url else "<span>No source link</span>"
    )
    license_text = esc(image.get("license") or "Not documented")
    license_label = (
        '<a href="' + esc(license_url) + '" target="_blank" rel="noopener noreferrer">' +
        license_text + "</a>" if license_url else license_text
    )
    return "\n".join([
        '<article class="tile">',
        '<div class="image-frame">' + picture + "</div>",
        '<div class="content">',
        '<div class="eyebrow">#' + str(index) + " · " + esc(candidate.get("source_table")) + " · " + esc(shape) + "</div>",
        '<h2>' + esc(candidate.get("title")) + "</h2>",
        '<p class="metadata">' + esc(candidate.get("year") or "Year unknown") + " · " +
        esc(candidate.get("language") or "Unknown") + " · " + esc(candidate.get("country") or "") + "</p>",
        '<p class="status">' + esc(status.replace("_", " ")) + "</p>",
        '<dl><dt>Film identity</dt><dd>' + esc(candidate.get("wikidata_qid")) + "</dd>",
        '<dt>Filename</dt><dd>' + esc(candidate.get("file_name") or "Unavailable") + "</dd>",
        '<dt>License (unreviewed)</dt><dd>' + license_label + "</dd>",
        '<dt>Artist</dt><dd>' + attribution + "</dd>",
        '<dt>Image source</dt><dd>' + link + "</dd></dl>",
        '<p class="hold">Review required · not approved for publication</p>',
        "</div></article>",
    ])


def render_html(pilot: dict) -> str:
    candidates = validate_pilot(pilot)
    shapes = Counter(image_shape(row.get("image") if isinstance(row.get("image"), dict) else {}) for row in candidates)
    by_status = Counter(str(row.get("status") or "UNKNOWN") for row in candidates)
    tiles = "\n".join(card(row, i) for i, row in enumerate(candidates, 1))
    counts = ", ".join(esc(k.replace("_", " ")) + ": " + str(v) for k, v in sorted(by_status.items()))
    summary = ", ".join(esc(k) + ": " + str(v) for k, v in sorted(shapes.items()))
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src https://upload.wikimedia.org https://commons.wikimedia.org; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Cinema &amp; Series — Artwork Review</title>
<style>
:root { color-scheme: dark; font-family: system-ui, -apple-system, sans-serif; background:#0e1116; color:#edf0f4; }
* { box-sizing:border-box; } body { margin:0; padding:28px; }
header { max-width:1200px; margin:0 auto 28px; }
h1 { font-size:clamp(25px,4vw,36px); letter-spacing:-.035em; }
.subtitle { color:#aeb9c9; line-height:1.65; max-width:850px; }
.metrics { display:flex; flex-wrap:wrap; gap:10px; margin-top:16px; }
.metric { border:1px solid #303946; border-radius:9px; padding:9px 12px; color:#dce1e7; }
.gallery { max-width:1520px; margin:auto; display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px; }
.tile { border:1px solid #303946; border-radius:12px; overflow:hidden; background:#171b23; min-width:0; }
.image-frame { background:#0a0d12; height:350px; display:flex; justify-content:center; align-items:center; }
.image-frame img { object-fit:contain; width:100%; height:100%; }
.no-image { padding:24px; color:#9da8b5; }
.content { padding:16px; }
.eyebrow { font-size:11px; text-transform:uppercase; letter-spacing:.09em; color:#aab6c4; }
h2 { font-size:19px; line-height:1.25; margin:10px 0; overflow-wrap:anywhere; }
.metadata { font-size:13px; color:#b5bdc9; } .status { font-size:12px; letter-spacing:.04em; font-weight:700; }
dl { display:grid; grid-template-columns:98px minmax(0,1fr); gap:7px 10px; font-size:12px; }
dt { color:#a7b3c2; } dd { margin:0; overflow-wrap:anywhere; }
a { color:#b3cfff; } .hold { font-size:12px; font-weight:700; color:#e6c589; margin-top:20px; }
</style>
</head>
<body>
<header>
<h1>Existing-title artwork review</h1>
<p class="subtitle">Only records already in Cinema &amp; Series are included. These are Wikidata P18 / Wikimedia Commons images, NOT verified theatrical posters. Image orientation is only a hint. Review identity, licensing, attribution and suitability before any app publication. This static gallery does not change the live database.</p>
<div class="metrics"><div class="metric">""" + str(len(candidates)) + """ title records</div><div class="metric">""" + summary + """</div><div class="metric">""" + counts + """</div></div>
</header>
<main class="gallery">
""" + tiles + """
</main>
</body>
</html>
"""


def safe_csv_cell(value: object) -> str:
    """Prevent formula execution when source-supplied fields open in Excel."""
    text = str(value if value is not None else "")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def csv_rows(pilot: dict) -> list[dict]:
    candidates = validate_pilot(pilot)
    result = []
    for candidate in candidates:
        image = candidate.get("image") if isinstance(candidate.get("image"), dict) else {}
        record = {key: "" for key in CSV_FIELDS}
        for field in ("source_table", "source_id", "wikidata_qid", "title", "year",
                      "language", "country", "status", "file_name"):
            record[field] = candidate.get(field) or ""
        record["image_shape"] = image_shape(image)
        for field in ("file_page_url", "license", "license_url", "artist"):
            record[field] = image.get(field) or ""
        record["review_decision"] = "PENDING"
        record["review_notes"] = ""
        record = {key: safe_csv_cell(value) for key, value in record.items()}
        result.append(record)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    pilot = json.loads(args.input.read_text(encoding="utf-8"))
    gallery = render_html(pilot)
    records = csv_rows(pilot)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.html.write_text(gallery, encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print("ARTWORK_REVIEW_GALLERY=" + json.dumps({
        "selected_titles": len(records), "decisions": "PENDING",
        "publication": False, "d1_reads": 0, "d1_writes": 0,
    }, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
