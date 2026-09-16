#!/usr/bin/env python3
"""Run the official website monitor with safe, source-specific crawl seeds.

Canonical source identity stays in source_registry.json. This layer only changes
where automated crawling begins, and only when the configured seed is on the
same normalized host as the canonical first-party website. Sources that cannot
be crawled safely can remain trusted provenance while being marked manual.
"""
from __future__ import annotations

import concurrent.futures
import json
import sys
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import website_monitor as monitor  # noqa: E402

REGISTRY = ROOT / "data/official/source_registry.json"
MONITOR_CONFIG = ROOT / "data/official/website_monitor_config.json"
OUT_JSON = ROOT / "data/generated/website-release-candidates.json"
OUT_SQL = ROOT / "data/generated/website-candidates-upsert.sql"
VALID_MODES = {"automatic", "manual"}


def load_monitor_config(path: Path = MONITOR_CONFIG) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources", {})
    if not isinstance(sources, dict):
        raise ValueError("website monitor config 'sources' must be an object keyed by source_key")
    for key, setting in sources.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("website monitor config contains a blank source_key")
        if not isinstance(setting, dict):
            raise ValueError(f"website monitor config for {key!r} must be an object")
    return sources


def resolve_monitor_url(source: dict, setting: dict | None = None) -> str | None:
    """Return an approved automated seed, or None for an explicitly manual source."""
    setting = setting or {}
    mode = str(setting.get("mode") or "automatic").casefold()
    if mode not in VALID_MODES:
        raise ValueError(f"{source.get('key')}: unsupported website monitor mode {mode!r}")
    if mode == "manual":
        return None

    canonical_url = str(source.get("website_url") or "").strip()
    if not canonical_url:
        raise ValueError(f"{source.get('key')}: automatic website monitoring requires website_url")
    monitor_url = str(setting.get("monitor_url") or canonical_url).strip()

    canonical = urllib.parse.urlparse(canonical_url)
    target = urllib.parse.urlparse(monitor_url)
    if canonical.scheme not in {"http", "https"} or not canonical.hostname:
        raise ValueError(f"{source.get('key')}: canonical website_url is not a valid HTTP(S) URL")
    if target.scheme not in {"http", "https"} or not target.hostname:
        raise ValueError(f"{source.get('key')}: website monitor URL is not a valid HTTP(S) URL")
    if monitor.normalized_host(monitor_url) != monitor.normalized_host(canonical_url):
        raise ValueError(
            f"{source.get('key')}: website monitor URL must stay on canonical first-party host "
            f"{monitor.normalized_host(canonical_url)!r}"
        )
    return monitor_url


def build_monitor_plan(sources: list[dict], settings: dict[str, dict]) -> tuple[list[tuple[dict, str]], list[dict]]:
    known_keys = {str(source.get("key")) for source in sources}
    unknown = sorted(set(settings) - known_keys)
    if unknown:
        raise ValueError(f"website monitor config references unknown source keys: {', '.join(unknown)}")

    plan: list[tuple[dict, str]] = []
    manual_results: list[dict] = []
    for source in sources:
        source_key = str(source["key"])
        setting = settings.get(source_key, {})
        monitor_url = resolve_monitor_url(source, setting)
        if monitor_url is None:
            manual_results.append(
                {
                    "source_key": source_key,
                    "monitor_mode": "manual",
                    "pages_checked": 0,
                    "errors": 0,
                    "candidates": 0,
                    "reason": str(setting.get("reason") or "manual first-party review"),
                }
            )
            continue
        plan.append((source, monitor_url))
    return plan, manual_results


def monitor_source_at(source: dict, scan_day: date, monitor_url: str) -> tuple[list[dict], dict]:
    # The mature crawler can stay unchanged: give it a copy whose website_url is
    # the approved same-host seed. Canonical source identity is preserved in the
    # registry and in the SQL sync performed by main().
    effective_source = dict(source)
    effective_source["website_url"] = monitor_url
    observations, result = monitor.monitor_source(effective_source, scan_day)
    result["monitor_url"] = monitor_url
    result["monitor_mode"] = "automatic"
    return observations, result


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    website_sources = [
        source
        for source in registry.get("sources", [])
        if source.get("active") and source.get("website_url")
    ]
    settings = load_monitor_config()
    plan, manual_results = build_monitor_plan(website_sources, settings)

    scan_day = datetime.now(timezone.utc).date()
    observations: list[dict] = []
    source_results: list[dict] = list(manual_results)

    with concurrent.futures.ThreadPoolExecutor(max_workers=monitor.MAX_SOURCE_WORKERS) as executor:
        futures = {
            executor.submit(monitor_source_at, source, scan_day, monitor_url): source
            for source, monitor_url in plan
        }
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                source_observations, result = future.result()
            except Exception as exc:
                print(f"warning: website monitor crashed for {source['name']}: {exc}", file=sys.stderr)
                source_observations = []
                result = {
                    "source_key": source["key"],
                    "monitor_mode": "automatic",
                    "pages_checked": 0,
                    "errors": 1,
                }
            observations.extend(source_observations)
            source_results.append(result)

    observations.sort(key=lambda item: (item["source_key"], item["page_url"], item["external_id"]))
    source_results.sort(key=lambda item: item["source_key"])
    checked = sum(1 for result in source_results if result.get("pages_checked", 0) > 0)
    pages_checked = sum(result.get("pages_checked", 0) for result in source_results)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "policy": (
                    "first-party websites only; optional crawl seeds must remain on the canonical host; "
                    "explicit day-level release signals become pending review observations and never auto-verify"
                ),
                "websites_registered": len(website_sources),
                "websites_automated": len(plan),
                "websites_manual": len(manual_results),
                "websites_checked": checked,
                "pages_checked": pages_checked,
                "source_results": source_results,
                "candidates": observations,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    # Keep canonical website_url values in D1; monitor seed URLs are crawl-only.
    OUT_SQL.write_text(monitor.build_sql(observations, website_sources), encoding="utf-8")
    print(
        f"checked {checked}/{len(plan)} automated official websites "
        f"({len(website_sources)} registered, {len(manual_results)} manual) "
        f"across {pages_checked} pages and found {len(observations)} release-date candidates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
