#!/usr/bin/env python3
"""Monitor first-party studio websites for reviewable release-date signals.

This monitor is intentionally conservative. It only visits registered first-party
websites, follows a small same-host set of release/movie/news links, extracts
explicit day-level dates near release-oriented language, and writes observations
as pending_review. Website observations never auto-promote a catalogue date to
verified; a human-curated entry in data/official/releases.json remains required.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

REGISTRY = Path("data/official/source_registry.json")
OUT_JSON = Path("data/generated/website-release-candidates.json")
OUT_SQL = Path("data/generated/website-candidates-upsert.sql")
MAX_PAGES_PER_SOURCE = 5
MAX_RESPONSE_BYTES = 1_500_000
REQUEST_TIMEOUT_SECONDS = 10
MAX_RELEASE_LEAD_DAYS = 1095
MAX_RELEASE_LAG_DAYS = 1
MAX_SOURCE_WORKERS = 5
USER_AGENT = "CinemaAndSeries-OfficialWebsiteMonitor/1.1 (+https://github.com/rayadinaveen98-ship-it/cinema-and-series)"

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*,?\s*(20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(20\d{2})\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b"),
]
RELEASE_CONTEXT = re.compile(
    r"\b(release|releasing|releases|released|worldwide|theatrical|cinema|cinemas|theatre|theatres|theater|theaters|in cinemas|in theatres|opens|arrives)\b",
    re.IGNORECASE,
)
LINK_CONTEXT = re.compile(
    r"\b(movie|movies|film|films|upcoming|release|releases|news|project|projects|slate|cinema)\b",
    re.IGNORECASE,
)
SKIP_LINK_CONTEXT = re.compile(
    r"\b(contact|privacy|terms|career|careers|jobs|about|login|register|press[- ]?kit)\b",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._capture_title = False
        self._capture_heading = False
        self._active_anchor: dict[str, object] | None = None
        self.text_parts: list[str] = []
        self.title_parts: list[str] = []
        self.heading_parts: list[str] = []
        self.anchors: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "svg", "noscript", "template"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attrs_dict = dict(attrs)
        if tag == "title":
            self._capture_title = True
        if tag in {"h1", "h2", "h3"}:
            self._capture_heading = True
        if tag == "a" and attrs_dict.get("href"):
            self._active_anchor = {"href": attrs_dict["href"], "parts": []}

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in {"script", "style", "svg", "noscript", "template"}:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._capture_title = False
        if tag in {"h1", "h2", "h3"}:
            self._capture_heading = False
        if tag == "a" and self._active_anchor:
            href = str(self._active_anchor["href"])
            text = " ".join(str(part) for part in self._active_anchor["parts"])
            self.anchors.append((href, clean_text(text)))
            self._active_anchor = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = clean_text(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._capture_title:
            self.title_parts.append(text)
        if self._capture_heading:
            self.heading_parts.append(text)
        if self._active_anchor is not None:
            parts = self._active_anchor["parts"]
            assert isinstance(parts, list)
            parts.append(text)

    @property
    def visible_text(self) -> str:
        return clean_text(" ".join(self.text_parts))

    @property
    def page_title(self) -> str:
        heading = clean_text(" ".join(self.heading_parts[:4]))
        title = clean_text(" ".join(self.title_parts))
        return (heading or title)[:220]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_date(match: re.Match[str]) -> date | None:
    groups = match.groups()
    try:
        if groups[0].isalpha():
            month = MONTHS[groups[0].casefold()]
            day = int(groups[1])
            year = int(groups[2])
        elif groups[1].isalpha():
            day = int(groups[0])
            month = MONTHS[groups[1].casefold()]
            year = int(groups[2])
        else:
            day, month, year = map(int, groups)
        return date(year, month, day)
    except (KeyError, ValueError):
        return None


def extract_release_signals(text: str, today: date | None = None) -> tuple[list[str], list[str]]:
    reference = today or datetime.now(timezone.utc).date()
    lower = reference - timedelta(days=MAX_RELEASE_LAG_DAYS)
    upper = reference + timedelta(days=MAX_RELEASE_LEAD_DAYS)
    dates: set[str] = set()
    excerpts: list[str] = []

    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            start = max(0, match.start() - 120)
            end = min(len(text), match.end() + 120)
            context = clean_text(text[start:end])
            if not RELEASE_CONTEXT.search(context):
                continue
            parsed = parse_date(match)
            if not parsed or parsed < lower or parsed > upper:
                continue
            dates.add(parsed.isoformat())
            if context not in excerpts:
                excerpts.append(context[:320])

    return sorted(dates), excerpts[:5]


def normalized_host(url: str) -> str:
    host = (urllib.parse.urlparse(url).hostname or "").casefold()
    return host[4:] if host.startswith("www.") else host


def normalize_url(base_url: str, href: str) -> str | None:
    joined = urllib.parse.urljoin(base_url, href)
    parsed = urllib.parse.urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        return None
    if normalized_host(joined) != normalized_host(base_url):
        return None
    if re.search(r"\.(?:jpg|jpeg|png|gif|webp|svg|pdf|zip|mp4|mp3|css|js)(?:$|\?)", parsed.path, re.IGNORECASE):
        return None
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
    query = [(key, value) for key, value in query if not key.casefold().startswith(("utm_", "fbclid", "gclid"))]
    clean = parsed._replace(fragment="", query=urllib.parse.urlencode(query)).geturl()
    return clean.rstrip("/") or clean


def candidate_links(base_url: str, anchors: list[tuple[str, str]], limit: int = MAX_PAGES_PER_SOURCE - 1) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for href, anchor_text in anchors:
        combined = f"{href} {anchor_text}"
        if SKIP_LINK_CONTEXT.search(combined):
            continue
        if not LINK_CONTEXT.search(combined):
            continue
        normalized = normalize_url(base_url, href)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(normalized)
        if len(candidates) >= limit:
            break
    return candidates


def load_robots(base_url: str) -> urllib.robotparser.RobotFileParser | None:
    parsed = urllib.parse.urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read(256_000)
            charset = response.headers.get_content_charset() or "utf-8"
            text = raw.decode(charset, errors="replace")
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(text.splitlines())
        return parser
    except Exception:
        return None


def allowed_by_robots(parser: urllib.robotparser.RobotFileParser | None, url: str) -> bool:
    return True if parser is None else parser.can_fetch(USER_AGENT, url)


def fetch_page(url: str) -> PageParser:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unsupported content type {content_type}")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("page exceeds monitor size limit")
        charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
    parser = PageParser()
    parser.feed(html)
    return parser


def observation_for_page(source: dict, url: str, parser: PageParser, today: date | None = None) -> dict | None:
    dates, excerpts = extract_release_signals(parser.visible_text, today=today)
    if not dates:
        return None
    page_title = parser.page_title or source["name"]
    fingerprint = f"{url}|{page_title}|{','.join(dates)}"
    external_id = "web-" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:24]
    review_title = page_title
    if excerpts:
        review_title = f"{page_title} — {excerpts[0]}"
    return {
        "source_key": source["key"],
        "source_name": source["name"],
        "external_id": external_id,
        "page_url": url,
        "page_title": page_title,
        "review_title": review_title[:420],
        "candidate_dates": dates,
        "candidate_release_date": dates[0] if len(dates) == 1 else None,
        "context_excerpts": excerpts,
        "status": "pending_review",
    }


def monitor_source(source: dict, scan_day: date) -> tuple[list[dict], dict]:
    base_url = source["website_url"]
    checked = 0
    errors = 0
    observations: list[dict] = []
    robots = load_robots(base_url)

    if not allowed_by_robots(robots, base_url):
        print(f"warning: robots.txt disallows monitoring {base_url}", file=sys.stderr)
        return observations, {"source_key": source["key"], "pages_checked": 0, "errors": 0, "robots_disallowed": True}

    try:
        home = fetch_page(base_url)
        checked += 1
        observation = observation_for_page(source, base_url, home, today=scan_day)
        if observation:
            observations.append(observation)
        urls = candidate_links(base_url, home.anchors)
    except Exception as exc:
        print(f"warning: website monitor failed for {source['name']} homepage: {exc}", file=sys.stderr)
        return observations, {"source_key": source["key"], "pages_checked": checked, "errors": 1}

    for url in urls:
        if not allowed_by_robots(robots, url):
            continue
        try:
            page = fetch_page(url)
            checked += 1
            observation = observation_for_page(source, url, page, today=scan_day)
            if observation:
                observations.append(observation)
        except Exception as exc:
            errors += 1
            print(f"warning: website monitor page failed for {source['name']} {url}: {exc}", file=sys.stderr)

    return observations, {
        "source_key": source["key"],
        "pages_checked": checked,
        "errors": errors,
        "candidates": len(observations),
    }


def esc(value: str) -> str:
    return value.replace("'", "''")


def sql_value(value: str | None) -> str:
    return "NULL" if value is None else f"'{esc(value)}'"


def build_sql(candidates: list[dict], sources: list[dict]) -> str:
    statements: list[str] = []
    for source in sources:
        statements.append(
            "INSERT INTO source_channels "
            "(source_key, source_name, source_type, website_url, youtube_channel_id, youtube_handle, active, updated_at) "
            f"VALUES ('{esc(source['key'])}','{esc(source['name'])}','{esc(source.get('source_type') or 'official_website')}',"
            f"{sql_value(source.get('website_url'))},{sql_value(source.get('youtube_channel_id'))},{sql_value(source.get('youtube_handle'))},"
            f"{1 if source.get('active', True) else 0},CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "source_name=excluded.source_name, source_type=excluded.source_type, website_url=excluded.website_url, "
            "youtube_channel_id=excluded.youtube_channel_id, youtube_handle=excluded.youtube_handle, "
            "active=excluded.active, updated_at=CURRENT_TIMESTAMP;"
        )

    for candidate in candidates:
        candidate_dates = json.dumps(candidate["candidate_dates"], ensure_ascii=False)
        date_value = sql_value(candidate.get("candidate_release_date"))
        statements.append(
            "INSERT INTO source_observations "
            "(source_key, external_id, external_url, title, published_at, candidate_release_date, candidate_dates_json, review_status, observed_at) "
            f"VALUES ('{esc(candidate['source_key'])}','{esc(candidate['external_id'])}','{esc(candidate['page_url'])}',"
            f"'{esc(candidate['review_title'])}',NULL,{date_value},'{esc(candidate_dates)}','pending_review',CURRENT_TIMESTAMP) "
            "ON CONFLICT(source_key, external_id) DO UPDATE SET "
            "external_url=excluded.external_url, title=excluded.title, candidate_release_date=excluded.candidate_release_date, "
            "candidate_dates_json=excluded.candidate_dates_json, observed_at=CURRENT_TIMESTAMP;"
        )
    return "\n".join(statements) + ("\n" if statements else "")


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    sources = [source for source in registry.get("sources", []) if source.get("active") and source.get("website_url")]
    scan_day = datetime.now(timezone.utc).date()
    observations: list[dict] = []
    source_results: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SOURCE_WORKERS) as executor:
        futures = {executor.submit(monitor_source, source, scan_day): source for source in sources}
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                source_observations, result = future.result()
            except Exception as exc:
                print(f"warning: website monitor crashed for {source['name']}: {exc}", file=sys.stderr)
                source_observations = []
                result = {"source_key": source["key"], "pages_checked": 0, "errors": 1}
            observations.extend(source_observations)
            source_results.append(result)

    observations.sort(key=lambda item: (item["source_key"], item["page_url"], item["external_id"]))
    source_results.sort(key=lambda item: item["source_key"])
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "policy": "first-party websites only; explicit day-level release signals become pending review observations and never auto-verify",
                "websites_registered": len(sources),
                "websites_checked": sum(1 for result in source_results if result.get("pages_checked", 0) > 0),
                "pages_checked": sum(result.get("pages_checked", 0) for result in source_results),
                "source_results": source_results,
                "candidates": observations,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    OUT_SQL.write_text(build_sql(observations, sources), encoding="utf-8")
    print(
        f"checked {sum(1 for result in source_results if result.get('pages_checked', 0) > 0)}/{len(sources)} official websites "
        f"across {sum(result.get('pages_checked', 0) for result in source_results)} pages and found {len(observations)} release-date candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
