#!/usr/bin/env python3
"""Build a local-only visual review gallery from the existing 70-title artwork queue.

This generates HTML referencing original Wikimedia thumbnails. It does not
download/host images, approve rights, change D1, or publish artwork in the app.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

from artwork_review_queue_70 import make_queue

KNOWN_SITES = {
    "commons.wikimedia.org",
    "en.wikipedia.org", "te.wikipedia.org", "hi.wikipedia.org",
    "ta.wikipedia.org", "ml.wikipedia.org", "kn.wikipedia.org",
    "bn.wikipedia.org",
}
IMAGE_SITES = {"upload.wikimedia.org", "thumb.wikimedia.org"}

DOCUMENT_START = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>Cinema &amp; Series | Artwork source review</title>
<style>
:root{color-scheme:dark;--bg:#090b10;--card:#151923;--line:#343c4b;--muted:#a7b0c0;--text:#f5f6f9;--accent:#8daaff}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 5% 0%,#151e35 0%,var(--bg) 42%);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;color:var(--text)}
.container{max-width:1450px;margin:auto;padding:28px 22px 64px}
h1{font-size:clamp(29px,4vw,45px);line-height:1.12;letter-spacing:-.04em;margin:5px 0 14px}
h2{font-size:17px;line-height:1.25;margin:0;overflow-wrap:anywhere}
.eyebrow{color:#b9c8fb;letter-spacing:.18em;text-transform:uppercase;font-size:11px;font-weight:700}
.intro,.notice{color:var(--muted);max-width:900px}
.notice{border:1px solid #715937;background:#2b231b;border-radius:13px;padding:12px 16px;color:#f5d9a8;margin:20px 0}
.summary{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0}
.summary span{padding:10px 16px;border-radius:12px;background:#181e2a;border:1px solid var(--line);font-size:13px}
.summary strong{font-size:21px;margin-right:7px}
.controls{position:sticky;top:0;z-index:2;padding:14px 0;background:#090b10f0;backdrop-filter:blur(14px);display:flex;gap:11px;align-items:center;flex-wrap:wrap}
.search{font:inherit;background:#191f2c;border:1px solid var(--line);color:#fff;border-radius:9px;padding:11px 14px;min-width:240px;flex:1}
.search:focus-visible,button:focus-visible,a:focus-visible{outline:2px solid #a6beff;outline-offset:3px}
.filters{display:flex;gap:6px;flex-wrap:wrap}
button{border:1px solid var(--line);border-radius:9px;color:#d6dfed;background:#1a1e29;padding:10px 13px;font:inherit;font-size:12px;font-weight:650;cursor:pointer}
button[aria-pressed=true]{background:#2e436f;border-color:#6b8ad0;color:#fff}
#visible-count{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(225px,1fr));gap:16px;margin-top:12px}
.card{min-width:0;background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.card[hidden]{display:none}
.poster{aspect-ratio:2/3;display:grid;place-items:center;background:linear-gradient(155deg,#30394a,#141925);position:relative;overflow:hidden}
.poster img{width:100%;height:100%;object-fit:contain;display:block}
.poster .missing{color:var(--muted);font-size:12px;padding:20px;text-align:center}
.picture-label{position:absolute;top:12px;left:12px;background:#05070bcf;padding:5px 9px;border:1px solid #4a5566;border-radius:7px;font-size:11px;letter-spacing:.05em}
.info{padding:14px;display:flex;flex-direction:column;gap:10px;flex:1}
.meta{color:var(--muted);font-size:12px}
.tag{display:inline-block;padding:4px 8px;border-radius:6px;background:#28304a;color:#c6d6fb;font-size:11px;font-weight:700;align-self:start}
.tag.hold{background:#482c22;color:#ffd4aa}
.tag.missing{background:#28303d;color:#d2d8e0}
.source{display:flex;flex-wrap:wrap;gap:7px;margin-top:auto}
.source a{color:#bfd0ff;font-size:12px;text-decoration:none;border:1px solid #465777;border-radius:8px;padding:7px 9px}
.source a:hover{text-decoration:underline;background:#273855}
.warning{font-size:11px;color:#d1b995;margin-top:4px}
footer{color:var(--muted);padding-top:35px;font-size:12px}
@media(max-width:580px){.container{padding:20px 13px}.controls{position:static}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.info{padding:10px}h2{font-size:14px}.poster{aspect-ratio:2/3}.search{min-width:100%}}
</style>
</head>
<body>
<main class="container">
<p class="eyebrow">Cinema &amp; Series / Source-only review</p>
<h1>Artwork candidate gallery</h1>
<p class="intro">Review saved poster and backdrop leads against exact film/series identities. Open each source article to check whether the artwork actually belongs to the title. This page does not approve or import any image.</p>
<div class="notice" role="note"><strong>Not cleared for publication.</strong> Wikipedia and Wikimedia preview images may be copyrighted or non-free. A matching article is not a license. Independently confirm rights and attribution before using any image in the application.</div>
"""

DOCUMENT_END = """
</section>
<footer>No database reads or writes. No new image searches. Thumbnails link to the original Wikimedia delivery URL and are requested by your browser only when you open this local gallery. Broken thumbnails may be opened at the source link for manual inspection.</footer>
</main>
<script>
(function(){
  'use strict';
  const cards = Array.from(document.querySelectorAll('.card'));
  const search = document.getElementById('search');
  const buttons = Array.from(document.querySelectorAll('[data-filter]'));
  const count = document.getElementById('visible-count');
  let filter = 'all';
  function update(){
    const q = search.value.trim().toLocaleLowerCase();
    let total = 0;
    for(const card of cards){
      const matches = (filter === 'all' || card.dataset.kind === filter)
        && card.dataset.search.includes(q);
      card.hidden = !matches;
      if(matches) total++;
    }
    count.textContent = total + ' of ' + cards.length + ' titles shown';
  }
  for(const button of buttons){
    button.addEventListener('click', () => {
      filter = button.dataset.filter;
      for(const b of buttons){ b.setAttribute('aria-pressed', String(b === button)); }
      update();
    });
  }
  search.addEventListener('input', update);
  update();
}());
</script>
</body>
</html>
"""


def safe_url(value: object, *, thumbnail: bool = False) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username or parsed.password or parsed.port is not None):
            return ""
        if parsed.hostname not in (IMAGE_SITES if thumbnail else KNOWN_SITES):
            return ""
        if thumbnail and not parsed.path.startswith("/wikipedia/"):
            return ""
        if not thumbnail and not parsed.path.startswith("/wiki/"):
            return ""
        return value
    except ValueError:
        return ""


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def render_gallery(report: dict) -> str:
    if (report.get("schema") != "artwork70-manual-review-queue-v1" or
            report.get("publication_performed") is not False or
            report.get("ready_for_publication") != 0 or
            report.get("database_reads") != 0 or report.get("database_writes") != 0 or
            not isinstance(report.get("queue"), list) or
            len(report["queue"]) != report.get("selected_count") or
            len(report["queue"]) > 70):
        raise ValueError("Expected a validated, unpublished 70-title review queue")
    counts = report["action_counts"]
    kinds = {
        "RESOLVE_IDENTITY_BEFORE_IMAGE_REVIEW": ("hold", "Identity hold"),
        "CHECK_ORIGINAL_POSTER_AND_USAGE_RIGHTS": ("poster", "Poster lead"),
        "BACKDROP_ONLY_FIND_POSTER": ("backdrop", "Backdrop only"),
        "NO_POSTER_FOUND_FIND_TRUSTED_SOURCE": ("missing", "No image"),
    }
    sections = [DOCUMENT_START, '<div class="summary" aria-label="Review queue summary">']
    for action, (_, label) in kinds.items():
        sections.append("<span><strong>" + esc(counts.get(action, 0)) + "</strong>" + esc(label) + "</span>")
    sections.append("</div><div class=\"controls\">"
                    "<input class=\"search\" id=\"search\" type=\"search\" "
                    "aria-label=\"Search artwork titles\" placeholder=\"Search title, language or year…\">"
                    "<div class=\"filters\" role=\"group\" aria-label=\"Filter by review status\">"
                    "<button type=\"button\" data-filter=\"all\" aria-pressed=\"true\">All</button>")
    for kind, label in kinds.values():
        sections.append('<button type="button" data-filter="' + kind +
                        '" aria-pressed="false">' + esc(label) + "</button>")
    sections.append('</div><span id="visible-count" aria-live="polite"></span></div>'
                    '<section class="grid" id="cards" aria-label="Artwork candidate cards">')

    for row in report["queue"]:
        if row.get("rights_status") != "UNVERIFIED_NOT_FOR_PUBLICATION" or row.get("approved_for_publication") is not False:
            raise ValueError("Review gallery may not show approved or published imagery")
        if row.get("action") not in kinds:
            raise ValueError("Unexpected artwork review status")
        kind, label = kinds[row["action"]]
        poster_url = safe_url(row.get("poster_preview_url"), thumbnail=True)
        backdrop_url = safe_url(row.get("backdrop_preview_url"), thumbnail=True)
        poster_page = safe_url(row.get("poster_page_url"))
        backdrop_page = safe_url(row.get("backdrop_page_url"))
        is_poster = bool(poster_url)
        preview_url = poster_url or backdrop_url
        search = " ".join(str(row.get(key) or "") for key in
                          ("title", "year", "language", "media_type", "wikidata_qid"))
        sections.append('<article class="card" data-kind="' + kind +
                        '" data-search="' + esc(search.casefold()) + '">')
        sections.append('<div class="poster"><span class="picture-label">' +
                        ("Poster candidate" if is_poster else
                         "Backdrop source" if kind == "backdrop" else "No poster preview") +
                        '</span>')
        if preview_url:
            sections.append('<img src="' + esc(preview_url) + '" loading="lazy" decoding="async" '
                            'referrerpolicy="no-referrer" alt="' + esc(row["title"]) +
                            ' — unverified image candidate">')
        else:
            sections.append('<div class="missing">No verified poster preview</div>')
        sections.append('</div><div class="info"><span class="tag ' +
                        ("hold" if kind == "hold" else "missing" if kind == "missing" else "") +
                        '">' + esc(label) + '</span><h2>' + esc(row["title"]) + '</h2>')
        sections.append('<div class="meta">' + esc(row.get("year") or "Year unknown") +
                        " · " + esc(row.get("language") or "Unknown language") + " · " +
                        esc(row.get("media_type") or "Unknown type") + '</div>')
        sections.append('<div class="source">')
        for url, name in ((poster_page, "Open image source"), (backdrop_page, "Open backdrop source")):
            if url:
                sections.append('<a target="_blank" rel="noopener noreferrer" href="' +
                                esc(url) + '">' + esc(name) + '</a>')
        sections.append('</div><div class="warning">Rights unverified · Do not publish</div></div></article>')
    sections.append(DOCUMENT_END)
    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Archived 70-title discovery JSON")
    parser.add_argument("--output", required=True, type=Path, help="Self-contained local HTML file")
    args = parser.parse_args()
    queue = make_queue(json.loads(args.input.read_text(encoding="utf-8")))
    html_content = render_gallery(queue)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_content, encoding="utf-8")
    print("ARTWORK70_HTML_GALLERY=" + json.dumps({
        "cards": queue["selected_count"],
        "posters_for_manual_review": queue["poster_leads"],
        "licensed_for_publication": 0,
        "database_reads": 0, "database_writes": 0,
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
