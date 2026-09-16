#!/usr/bin/env python3
"""Find or create the production D1 database and inject its binding into wrangler.jsonc.

Required environment variables:
- CLOUDFLARE_ACCOUNT_ID
- CLOUDFLARE_API_TOKEN

This file is intended for CI. It never prints the token.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
DB_NAME = "cinema-and-series"
API_ROOT = "https://api.cloudflare.com/client/v4"
WRANGLER = Path("wrangler.jsonc")


def api(method: str, path: str, body: dict | None = None) -> dict:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=payload,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "CinemaAndSeries-CI/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if not result.get("success"):
        raise RuntimeError(f"Cloudflare API error: {result.get('errors')}")
    return result


def resolve_database_id() -> str:
    query = urllib.parse.urlencode({"name": DB_NAME, "per_page": 100})
    listed = api("GET", f"/accounts/{ACCOUNT_ID}/d1/database?{query}").get("result") or []
    exact = [item for item in listed if item.get("name") == DB_NAME]
    if exact:
        db_id = exact[0].get("uuid")
        if not db_id:
            raise RuntimeError("Existing D1 database did not include a UUID")
        print(f"Using existing D1 database: {DB_NAME}")
        return db_id

    created = api(
        "POST",
        f"/accounts/{ACCOUNT_ID}/d1/database",
        {
            "name": DB_NAME,
            "primary_location_hint": "apac",
        },
    ).get("result") or {}
    db_id = created.get("uuid")
    if not db_id:
        raise RuntimeError("D1 create response did not include a UUID")
    print(f"Created D1 database: {DB_NAME}")
    return db_id


def bind_database(db_id: str) -> None:
    config = json.loads(WRANGLER.read_text(encoding="utf-8"))
    config["d1_databases"] = [
        {
            "binding": "DB",
            "database_name": DB_NAME,
            "database_id": db_id,
            "migrations_dir": "migrations",
        }
    ]
    WRANGLER.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print("Injected production D1 binding into transient CI wrangler config")


def main() -> int:
    if not ACCOUNT_ID or not TOKEN:
        print("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN", file=sys.stderr)
        return 2
    try:
        bind_database(resolve_database_id())
        return 0
    except Exception as exc:
        print(f"Cloudflare bootstrap failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
