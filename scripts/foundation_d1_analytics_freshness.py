#!/usr/bin/env python3
"""Read-only D1 GraphQL freshness diagnostics for the current and two prior UTC days.

The Cloudflare dashboard uses the SAME GraphQL analytics source, so this
diagnostic is NOT an independent billing or quota balance verification.
NEVER issues D1 SQL, deploys, creates/deletes a database, or authorizes staging.
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

from scripts.foundation_remote_account_preflight import require, UUID

QUERY = """query FoundationD1RecentAnalytics($accountTag: string!, $start: Date, $end: Date) {
  viewer {
    accounts(filter: { accountTag: $accountTag }) {
      d1AnalyticsAdaptiveGroups(
        limit: 10000
        filter: { date_geq: $start, date_leq: $end }
        orderBy: [date_DESC]
      ) {
        dimensions { date databaseId }
        sum { rowsRead rowsWritten readQueries writeQueries }
      }
    }
  }
}"""
FIELDS = ("rowsRead", "rowsWritten", "readQueries", "writeQueries")


def parse_day(value: str) -> date:
    require(isinstance(value, str) and
            re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is not None,
            "Invalid UTC day")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Invalid UTC day") from exc


def inspect_recent_analytics(payload: dict, today: str, preflight: dict) -> dict:
    """Aggregate only public-safe daily counts; do not serialize database UUIDs."""
    day = parse_day(today)
    require(preflight.get("utc_day") == today and
            preflight.get("read_only_cloudflare_control_plane_and_analytics") is True
            and preflight.get("production_sql_executed") is False
            and preflight.get("production_d1_writes") == 0
            and preflight.get("remote_staging_database_created") is False,
            "Preflight identity or read-only status unavailable")
    require(isinstance(payload, dict) and not payload.get("errors"),
            "Recent D1 GraphQL analytics unavailable")
    accounts = payload.get("data", {}).get("viewer", {}).get("accounts")
    require(isinstance(accounts, list) and len(accounts) == 1,
            "Recent D1 account dataset unavailable or ambiguous")
    groups = accounts[0].get("d1AnalyticsAdaptiveGroups")
    require(isinstance(groups, list) and len(groups) < 10000,
            "Recent D1 analytics missing or potentially truncated")
    days = [(day - timedelta(days=i)).isoformat() for i in (2, 1, 0)]
    per_day = {
        d: {"group_count": 0, "rows_read": 0, "rows_written": 0,
            "read_queries": 0, "write_queries": 0} for d in days
    }
    seen = set()
    for group in groups:
        require(isinstance(group, dict) and isinstance(group.get("dimensions"), dict)
                and isinstance(group.get("sum"), dict),
                "Malformed recent D1 analytics group")
        dims, vals = group["dimensions"], group["sum"]
        source_day, dbid = dims.get("date"), dims.get("databaseId")
        require(source_day in per_day and isinstance(dbid, str)
                and UUID.fullmatch(dbid) is not None,
                "Unexpected recent D1 group dimension")
        identity = (source_day, dbid.lower())
        require(identity not in seen, "Duplicate recent D1 analytics group")
        seen.add(identity)
        for name in FIELDS:
            number = vals.get(name)
            require(isinstance(number, (int, float))
                    and not isinstance(number, bool)
                    and 0 <= number <= 9_007_199_254_740_991
                    and int(number) == number,
                    "Invalid recent D1 rows or query metric")
        dest = per_day[source_day]
        dest["group_count"] += 1
        dest["rows_read"] += int(vals["rowsRead"])
        dest["rows_written"] += int(vals["rowsWritten"])
        dest["read_queries"] += int(vals["readQueries"])
        dest["write_queries"] += int(vals["writeQueries"])

    today_data = per_day[today]
    past_present = any(per_day[d]["group_count"] > 0 for d in days[:-1])
    if today_data["group_count"] == 0:
        state = ("today_missing_historical_visible" if past_present
                 else "all_three_days_missing")
    elif preflight.get("usage_data_empty") is True:
        state = "same_day_snapshots_inconsistent"
    elif (today_data["rows_read"] != preflight.get("account_rows_read_reported")
          or today_data["rows_written"] !=
             preflight.get("account_rows_written_reported")):
        state = "same_day_snapshots_inconsistent"
    else:
        state = "today_present_same_source_counts_agree"

    return {
        "schema": "foundation-v2-d1-analytics-freshness-v1",
        "utc_day": today,
        "analysis_window_utc_days": days,
        "status": state,
        "current_day_groups_present": today_data["group_count"] > 0,
        "prior_day_groups_present": past_present,
        "daily_group_totals": per_day,
        "based_on_same_cloudflare_graphql_dataset": True,
        "independent_realtime_quota_verified": False,
        "canary_or_production_write_authorized": False,
        "production_d1_sql_executed": False,
        "production_d1_writes": 0,
        "remote_staging_database_created": False,
        "caveat": (
            "Cloudflare GraphQL analytics can be delayed; dashboard charts "
            "use the same source. Historical records do not prove current quota."
        ),
    }


def fetch_recent(account_id: str, token: str, today: str) -> dict:
    require(isinstance(account_id, str) and
            re.fullmatch(r"[0-9a-fA-F]{32}", account_id) is not None,
            "Invalid Cloudflare account identifier")
    require(isinstance(token, str) and bool(token),
            "Cloudflare API token unavailable")
    day = parse_day(today)
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "accountTag": account_id,
            "start": (day - timedelta(days=2)).isoformat(),
            "end": today,
        },
    }).encode()
    req = Request("https://api.cloudflare.com/client/v4/graphql",
                  data=body, method="POST",
                  headers={"Authorization": "Bearer " + token,
                           "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=35) as response:
            return json.loads(response.read(2_000_000))
    except Exception as exc:
        # Do not leak HTTP response bodies, SQL, account IDs or API credentials.
        raise ValueError("Recent D1 GraphQL query failed") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    preflight = json.loads(args.preflight.read_text(encoding="utf-8"))
    utc_day = preflight.get("utc_day", "")
    parse_day(utc_day)
    payload = fetch_recent(os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
                           os.environ.get("CLOUDFLARE_API_TOKEN", ""), utc_day)
    result = inspect_recent_analytics(payload, utc_day, preflight)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("FOUNDATION_D1_ANALYTICS_FRESHNESS=" + json.dumps({
        "status": result["status"],
        "utc_day": utc_day,
        "current_day_groups_present": result["current_day_groups_present"],
        "prior_day_groups_present": result["prior_day_groups_present"],
        "independent_realtime_quota_verified": False,
        "production_writes": 0,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FOUNDATION_D1_ANALYTICS_FRESHNESS=unavailable_fail_closed")
        raise SystemExit(1)
