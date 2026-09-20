#!/usr/bin/env python3
"""Bind the existing production D1 database into transient CI config.

Unlike cloudflare_bootstrap.py, this helper is intentionally incapable of
creating a D1 database. It is intended for read-only audit/observability jobs
that must fail closed if the expected production database cannot be found.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
DB_NAME = "cinema-and-series"
WRANGLER = Path("wrangler.jsonc")


def run_wrangler(*args: str) -> str:
    completed = subprocess.run(
        ["npx", "wrangler", *args],
        check=False,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    if completed.returncode != 0:
        details = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
        )
        raise RuntimeError(
            f"Wrangler {' '.join(args)} failed with exit code {completed.returncode}:\n{details}"
        )
    return completed.stdout.strip()


def validate_credentials_shape() -> None:
    if not ACCOUNT_ID or not TOKEN:
        raise RuntimeError("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", ACCOUNT_ID):
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID is not a 32-character Cloudflare account identifier"
        )


def resolve_existing_database_id() -> str:
    raw = run_wrangler("d1", "list", "--json")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Wrangler returned invalid JSON for d1 list: {raw[:500]}") from exc
    if not isinstance(parsed, list):
        raise RuntimeError("Unexpected Wrangler d1 list response shape")

    exact = [item for item in parsed if item.get("name") == DB_NAME]
    if len(exact) != 1:
        raise RuntimeError(
            f"Expected exactly one existing D1 database named {DB_NAME}; found {len(exact)}"
        )

    db_id = exact[0].get("uuid") or exact[0].get("id")
    if not db_id:
        raise RuntimeError("D1 database record did not include a UUID")
    return str(db_id)


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
    print(f"Bound existing production D1 database: {DB_NAME}")


def main() -> int:
    try:
        validate_credentials_shape()
        bind_database(resolve_existing_database_id())
        return 0
    except Exception as exc:
        print(f"Read-only D1 binding failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
