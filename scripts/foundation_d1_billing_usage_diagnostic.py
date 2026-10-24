#!/usr/bin/env python3
"""Manual-only independent billing-data visibility check (NEVER quota admission).

Queries Cloudflare Billing Usage V1 alpha with a dedicated Billing Read token.
The billing system updates daily: it cannot establish real-time D1 quota,
nor authorize scratch DB creation or any production catalogue correction.

No D1 SQL, no D1 identifiers, no output of costs, tokens, account IDs or raw
billable rows. One bounded GET with no retries; HTTP errors are classified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCHEMA = "foundation-v2-billing-usage-d1-visibility-v1"
MAX_BYTES = 2_000_000
MAX_ROWS = 3000
WINDOW_DAYS = 7
PERMITTED_STATUSES = frozenset((
    "billing_token_not_configured",
    "billing_permission_unavailable",
    "billing_api_unavailable",
    "billing_response_unverified",
    "billing_rows_absent",
    "d1_rows_absent_in_billing",
    "historical_d1_billing_rows_visible",
))
ACCOUNT = re.compile(r"\A[0-9a-fA-F]{32}\Z")


def safe_result(status: str, utc_day: str) -> dict:
    if status not in PERMITTED_STATUSES:
        raise ValueError("Unrecognized billing diagnostic state")
    return {
        "schema": SCHEMA,
        "utc_day": utc_day,
        "status": status,
        "billable_usage_source": "cloudflare_billing_v1_daily_not_realtime",
        "billing_read_permission_required": True,
        "billing_period_days_requested": WINDOW_DAYS,
        "billing_row_count": None,
        "d1_billing_row_count": None,
        "most_recent_d1_charge_period_start_utc": None,
        "full_daily_d1_read_allowance_known": False,
        "full_daily_d1_write_allowance_known": False,
        "free_tier_quota_exhausted_proven": False,
        "current_quota_headroom_verified": False,
        "scratch_staging_authorized": False,
        "production_corrections_authorized": False,
        "production_d1_sql_executed": False,
        "production_d1_reads": 0,
        "production_d1_writes": 0,
        "database_created_or_deleted": False,
    }


def checked_day(text: str) -> datetime:
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError("Invalid UTC analysis day")
    try:
        return datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError("Invalid UTC analysis day") from error


def parse_charge_start_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Missing charge period")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Charge period has no timezone")
        return timestamp.astimezone(timezone.utc)
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid charge period") from error


def inspect_billing_data(body: dict, utc_day: str, account_id: str) -> dict:
    """Fail-closed billing visibility; never interpret absent records as zero."""
    today = checked_day(utc_day)
    if not isinstance(account_id, str) or not ACCOUNT.fullmatch(account_id):
        raise ValueError("Account identity unavailable")
    if not isinstance(body, dict) or body.get("success") is not True or body.get("errors") not in (None, []):
        raise ValueError("Billing API response unverified")
    rows = body.get("result")
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("Billing usage response missing or possibly truncated")
    result = safe_result("billing_rows_absent", utc_day)
    result["billing_row_count"] = len(rows)
    result["d1_billing_row_count"] = 0
    if not rows:
        return result

    latest = None
    count = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid billing record")
        # Billing V1 responds at the account level, separate from D1 GraphQL.
        # Reject cross-account rows rather than report someone else's charges.
        billing_id = row.get("BillingAccountId")
        if not isinstance(billing_id, str) or billing_id.lower() != account_id.lower():
            raise ValueError("Billing account mismatch or missing")
        service_name = row.get("ServiceName")
        service_family = row.get("ServiceFamilyName")
        if not isinstance(service_name, str) or not isinstance(service_family, str):
            raise ValueError("Billing product identity unavailable")
        start = parse_charge_start_utc(row.get("ChargePeriodStart"))
        end = parse_charge_start_utc(row.get("ChargePeriodEnd"))
        if not (start < end and today-timedelta(days=WINDOW_DAYS+1) <= start
                and start < today + timedelta(days=1)
                and end <= today + timedelta(days=2)):
            raise ValueError("Charge period invalid for bounded window")
        if re.search(r"\bD1\b", service_name + " " + service_family, re.IGNORECASE):
            count += 1
            latest = start if latest is None or start > latest else latest

    result["d1_billing_row_count"] = count
    if count:
        result["status"] = "historical_d1_billing_rows_visible"
        result["most_recent_d1_charge_period_start_utc"] = latest.date().isoformat()
    else:
        result["status"] = "d1_rows_absent_in_billing"
    return result


def fetch_billing_data(account_id: str, token: str, utc_day: str,
                       opener=urlopen) -> dict:
    checked_day(utc_day)
    if not isinstance(account_id, str) or not ACCOUNT.fullmatch(account_id):
        raise ValueError("Account identity unavailable")
    if not isinstance(token, str) or not token:
        return safe_result("billing_token_not_configured", utc_day)
    date = checked_day(utc_day)
    params = urlencode({"from": (date-timedelta(days=WINDOW_DAYS)).date().isoformat(),
                        "to": date.date().isoformat()})
    url = ("https://api.cloudflare.com/client/v4/accounts/" +
           account_id + "/billable-usage?" + params)
    request = Request(url, headers={"Authorization": "Bearer " + token,
                                    "Accept": "application/json"},
                      method="GET")
    try:
        with opener(request, timeout=30) as response:
            body = response.read(MAX_BYTES+1)
            if len(body) > MAX_BYTES:
                raise ValueError("Billing response too large")
        return inspect_billing_data(json.loads(body), utc_day, account_id)
    except HTTPError as error:
        return safe_result(
            "billing_permission_unavailable" if error.code in (401, 403)
            else "billing_api_unavailable", utc_day)
    except (URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
        return safe_result("billing_response_unverified", utc_day)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(Path("ops/data-foundation-v2-freeze.json")
                        .read_text(encoding="utf-8"))
    if freeze.get("active") is not True or freeze.get("baseline", {}).get("total") != 70175:
        raise ValueError("Frozen production catalogue baseline unverified")
    day = datetime.now(timezone.utc).date().isoformat()
    report = fetch_billing_data(os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
                                os.environ.get("CLOUDFLARE_BILLING_READ_TOKEN", ""),
                                day)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print("FOUNDATION_BILLING_D1_DIAGNOSTIC=" + json.dumps({
        "status": report["status"],
        "utc_day": day,
        "historical_d1_rows": report["d1_billing_row_count"],
        "real_time_quota_verified": False,
        "production_d1_writes": 0,
        "staging_authorized": False,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # No token, raw billing rows, account identifiers, response bodies or URLs.
        print("FOUNDATION_BILLING_D1_DIAGNOSTIC=fail_closed_without_d1_access")
        raise SystemExit(1)
