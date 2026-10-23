#!/usr/bin/env python3
"""Read-only Cloudflare D1 account-capacity and daily-usage preflight.

NEVER creates a D1 database, sends SQL, deploys a Worker or changes catalogue.
Only uses `wrangler d1 list --json` and read-only Cloudflare GraphQL analytics.
Denies staging readiness if identity, metrics, or capacity cannot be proven.
GraphQL metrics can be delayed; a passing check is NOT staging authorization.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen

PRODUCTION = "cinema-and-series"
PREFIX = "foundation-v2-qa-"
UUID = re.compile(r"\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")
FREE_DATABASE_LIMIT = 10
FREE_WRITE_LIMIT = 100000
FREE_READ_LIMIT = 5000000
RESERVE_DATABASE_SLOTS = 2
MIN_CANARY_WRITE_HEADROOM = 40000
MIN_CANARY_READ_HEADROOM = 1000000

QUERY = """query FoundationD1DailyPreflight($accountTag: string!, $day: Date) {
  viewer {
    accounts(filter: { accountTag: $accountTag }) {
      d1AnalyticsAdaptiveGroups(
        limit: 10000
        filter: { date_geq: $day, date_leq: $day }
      ) {
        dimensions { date databaseId }
        sum { rowsRead rowsWritten }
      }
    }
  }
}"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def inspect_list(databases: list[dict]) -> dict:
    require(isinstance(databases, list), "D1 database list is not an array")
    require(len(databases) <= FREE_DATABASE_LIMIT - RESERVE_DATABASE_SLOTS,
            "Not enough conservatively reserved Free D1 database slots")
    names: set[str] = set()
    uuids: set[str] = set()
    production: list[str] = []
    orphans: list[str] = []
    for item in databases:
        require(isinstance(item, dict), "Unexpected D1 listing item")
        name = item.get("name")
        ident = item.get("uuid") or item.get("id")
        require(isinstance(name, str) and name and isinstance(ident, str)
                and UUID.fullmatch(ident), "Unidentifiable D1 database")
        require(name not in names and ident.lower() not in uuids,
                "Duplicate D1 name or UUID")
        names.add(name)
        uuids.add(ident.lower())
        if name == PRODUCTION:
            production.append(ident.lower())
        if name.startswith(PREFIX):
            orphans.append(name)
    require(len(production) == 1, "Exact production database identity unavailable")
    require(not orphans, "An earlier disposable staging D1 still exists; inspect it")
    return {"database_count": len(databases), "free_database_slots":
            FREE_DATABASE_LIMIT - len(databases), "production_found": True,
            "staging_orphans_found": 0}


def inspect_graphql(payload: dict, today: str) -> dict:
    require(isinstance(payload, dict) and not payload.get("errors"),
            "Cloudflare GraphQL analytics is unavailable")
    viewer = payload.get("data", {}).get("viewer", {})
    accounts = viewer.get("accounts")
    require(isinstance(accounts, list) and len(accounts) == 1,
            "Ambiguous or inaccessible Cloudflare account analytics")
    groups = accounts[0].get("d1AnalyticsAdaptiveGroups")
    require(isinstance(groups, list) and len(groups) < 10000,
            "D1 usage groups missing, invalid or possibly truncated")
    rows_read = rows_written = 0
    for group in groups:
        require(isinstance(group, dict) and isinstance(group.get("sum"), dict)
                and isinstance(group.get("dimensions"), dict),
                "Invalid D1 usage group")
        require(group["dimensions"].get("date") == today,
                "D1 metrics day does not match current UTC day")
        for key in ("rowsRead", "rowsWritten"):
            n = group["sum"].get(key)
            require(isinstance(n, (int, float)) and not isinstance(n, bool)
                    and n >= 0 and int(n) == n, "Invalid D1 rows metric")
        rows_read += int(group["sum"]["rowsRead"])
        rows_written += int(group["sum"]["rowsWritten"])
    remaining_write = max(0, FREE_WRITE_LIMIT - rows_written)
    remaining_read = max(0, FREE_READ_LIMIT - rows_read)
    return {
        "utc_day": today, "account_rows_read_reported": rows_read,
        "account_rows_written_reported": rows_written,
        "free_rows_read_remaining_estimate": remaining_read,
        "free_rows_written_remaining_estimate": remaining_write,
        "minimum_canary_read_headroom": MIN_CANARY_READ_HEADROOM,
        "minimum_canary_write_headroom": MIN_CANARY_WRITE_HEADROOM,
        "usage_data_empty": len(groups) == 0,
        "reported_usage_headroom_sufficient":
            bool(groups) and remaining_read >= MIN_CANARY_READ_HEADROOM
            and remaining_write >= MIN_CANARY_WRITE_HEADROOM,
    }


def assess(databases: list[dict], analytics: dict, today: str) -> dict:
    capacity = inspect_list(databases)
    usage = inspect_graphql(analytics, today)
    return {
        "schema": "foundation-v2-remote-d1-account-readiness-v1",
        **capacity, **usage,
        "read_only_cloudflare_control_plane_and_analytics": True,
        "production_sql_executed": False,
        "production_d1_reads": 0, "production_d1_writes": 0,
        "remote_staging_database_created": False,
        "canary_capacity_indicated_not_authorized":
            usage["reported_usage_headroom_sufficient"],
        "full_staging_authorized": False,
        "production_corrections_authorized": False,
        "caveats": [
            "GraphQL analytics may lag live D1 usage",
            "Indexes, migrations and failed/retried operations consume extra rows",
            "Free-plan limits assumed conservatively for all accounts",
            "Manual quota recheck and isolated cleanup are required before staging",
        ],
    }


def fetch_database_list() -> list[dict]:
    try:
        proc = subprocess.run(
            ["npx", "wrangler", "d1", "list", "--json"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            check=False, timeout=90,
        )
        require(proc.returncode == 0, "Read-only D1 database listing failed")
        return json.loads(proc.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        raise ValueError("Read-only D1 database listing unavailable") from e


def fetch_graphql(account_id: str, token: str, today: str) -> dict:
    require(re.fullmatch(r"[0-9a-fA-F]{32}", account_id) is not None,
            "Invalid Cloudflare account identifier")
    require(bool(token), "Cloudflare API token unavailable")
    body = json.dumps({"query": QUERY,
                       "variables": {"accountTag": account_id, "day": today}}).encode()
    req = Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=35) as response:
            return json.loads(response.read(2_000_000))
    except Exception as e:
        # Do not log token, credential-bearing headers or response body.
        raise ValueError("Cloudflare account-wide analytics check failed") from e


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    freeze = json.loads(Path("ops/data-foundation-v2-freeze.json").read_text())
    require(freeze.get("active") is True and
            freeze.get("baseline", {}).get("total") == 70175,
            "Frozen production catalogue baseline has changed")
    today = datetime.now(timezone.utc).date().isoformat()
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    dbs = fetch_database_list()
    analytics = fetch_graphql(account, token, today)
    report = assess(dbs, analytics, today)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("FOUNDATION_REMOTE_ACCOUNT_PREFLIGHT=" + json.dumps({
        "utc_day": today, "databases": report["database_count"],
        "remaining_estimated_writes": report["free_rows_written_remaining_estimate"],
        "provisional_canary_capacity":
            report["canary_capacity_indicated_not_authorized"],
        "production_writes": 0, "staging_created": False,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FOUNDATION_REMOTE_ACCOUNT_PREFLIGHT=fail_closed_no_writes")
        raise SystemExit(1)
