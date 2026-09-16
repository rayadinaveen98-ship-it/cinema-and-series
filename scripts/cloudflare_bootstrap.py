#!/usr/bin/env python3
"""Find or create the production D1 database and inject its binding into wrangler.jsonc.

Required environment variables:
- CLOUDFLARE_ACCOUNT_ID
- CLOUDFLARE_API_TOKEN

This CI bootstrap intentionally delegates D1 control-plane operations to Wrangler,
Cloudflare's supported CLI, rather than reimplementing the REST API. It never
prints either secret.
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


def list_databases() -> list[dict]:
    raw = run_wrangler("d1", "list", "--json")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Wrangler returned invalid JSON for d1 list: {raw[:500]}") from exc
    if not isinstance(parsed, list):
        raise RuntimeError("Unexpected Wrangler d1 list response shape")
    return parsed


def resolve_database_id() -> str:
    databases = list_databases()
    exact = [item for item in databases if item.get("name") == DB_NAME]
    if not exact:
        print(f"No D1 database named {DB_NAME}; creating it in APAC")
        run_wrangler("d1", "create", DB_NAME, "--location=apac")
        databases = list_databases()
        exact = [item for item in databases if item.get("name") == DB_NAME]

    if not exact:
        raise RuntimeError(f"D1 database {DB_NAME} was not found after creation")

    db_id = exact[0].get("uuid") or exact[0].get("id")
    if not db_id:
        raise RuntimeError("D1 database record did not include a UUID")

    print(f"Using D1 database: {DB_NAME}")
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
    print("Injected production D1 binding into transient CI wrangler config")


def main() -> int:
    try:
        validate_credentials_shape()
        bind_database(resolve_database_id())
        return 0
    except Exception as exc:
        print(f"Cloudflare bootstrap failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
