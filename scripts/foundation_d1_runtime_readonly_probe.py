#!/usr/bin/env python3
"""Manually dispatched, ONE fixed read-only D1 REST query to a verified database.

This can show that one query is permitted NOW, or classify Cloudflare's
documented daily limit errors. It can NEVER prove account-wide remaining
rows, authorize scratch D1 creation, or authorize any catalogue writes.

No dynamic SQL, schema operations, mutations, or query retries.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.foundation_remote_account_preflight import (
    PRODUCTION, UUID, fetch_database_list, inspect_list, require,
)

SQL = "SELECT 1 AS probe_ok"
SCHEMA = "foundation-v2-d1-runtime-readonly-probe-v1"
LIMIT_READ = "free tier daily row read limit"
LIMIT_WRITE = "free tier daily row write limit"


def current_probe_status(databases: list[dict], account: str, token: str,
                         http_open=urlopen) -> dict:
    """One bounded direct D1 query against the UUID of the ONE production D1."""
    safe = inspect_list(databases)  # Reject staging orphan, duplicate and capacity issues.
    require(safe["production_found"] is True and
            safe["staging_orphans_found"] == 0, "Scratch/production identity unverified")
    require(isinstance(account, str) and re.fullmatch(r"[0-9a-fA-F]{32}", account),
            "Account identity unavailable")
    require(isinstance(token, str) and bool(token), "D1 token missing")
    ids = [d.get("uuid") or d.get("id") for d in databases
           if d.get("name") == PRODUCTION]
    require(len(ids) == 1 and UUID.fullmatch(ids[0]) is not None,
            "Production D1 UUID unavailable")
    database_id = ids[0]
    # UUID is passed ONLY to the REST API endpoint, never serialized or logged.
    url = ("https://api.cloudflare.com/client/v4/accounts/" + account +
           "/d1/database/" + database_id + "/query")
    payload = json.dumps({"sql": SQL}).encode("utf-8")
    request = Request(url, data=payload, method="POST", headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    })
    result = {
        "schema": SCHEMA,
        "target": "verified_single_existing_production_d1",
        "probe_sql_class": "constant_read_only_select_one",
        "probe_attempt_count": 1,
        "runtime_status": "query_unverified",
        "query_succeeded": False,
        "d1_rows_read_reported": None,
        "d1_rows_written_reported": None,
        "independent_current_query_health_evidence": False,
        "independent_realtime_quota_headroom_verified": False,
        "account_remaining_reads": None,
        "account_remaining_writes": None,
        "scratch_creation_authorized": False,
        "production_corrections_authorized": False,
        "database_creation_or_deletion": False,
        "data_mutation_requested": False,
    }
    try:
        with http_open(request, timeout=20) as response:
            reply = json.loads(response.read(8192))
        require(isinstance(reply, dict) and reply.get("success") is True and
                reply.get("errors") in (None, []),
                "D1 response was not positively verified")
        items = reply.get("result")
        require(isinstance(items, list) and len(items) == 1,
                "Unexpected D1 response cardinality")
        item = items[0]
        require(isinstance(item, dict) and item.get("success") is True
                and isinstance(item.get("meta"), dict),
                "Query completion not verified")
        meta = item["meta"]
        read, write = meta.get("rows_read"), meta.get("rows_written")
        require(isinstance(read, int) and not isinstance(read, bool)
                and 0 <= read <= 100 and write == 0
                and type(write) is int
                and meta.get("changes") == 0
                and meta.get("changed_db") is False,
                "Read-only query metadata rejected")
        rows = item.get("results")
        require(isinstance(rows, list) and len(rows) == 1
                and isinstance(rows[0], dict)
                and rows[0] == {"probe_ok": 1},
                "Unexpected read-only query result")
        result.update({
            "runtime_status": "read_succeeded_no_write",
            "query_succeeded": True,
            "d1_rows_read_reported": read,
            "d1_rows_written_reported": 0,
            "independent_current_query_health_evidence": True,
        })
    except HTTPError as exc:
        # Only inspect a tiny bounded error body for documented quota phrases;
        # NEVER print HTTP errors, URL, token, account ID, or response text.
        try:
            body = exc.read(2048).decode("utf-8", "replace").lower()
        except Exception:
            body = ""
        if LIMIT_READ in body:
            result["runtime_status"] = "cloudflare_reported_daily_read_limit"
        elif LIMIT_WRITE in body:
            result["runtime_status"] = "cloudflare_reported_daily_write_limit"
    except (URLError, OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(Path("ops/data-foundation-v2-freeze.json")
                        .read_text(encoding="utf-8"))
    require(freeze.get("active") is True
            and freeze.get("baseline", {}).get("total") == 70175,
            "Catalogue freeze guard is missing")
    dbs = fetch_database_list()
    report = current_probe_status(
        dbs,
        os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
        os.environ.get("CLOUDFLARE_API_TOKEN", ""),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("FOUNDATION_D1_RUNTIME_READONLY=" + json.dumps({
        "status": report["runtime_status"],
        "one_readonly_query_succeeded": report["query_succeeded"],
        "rows_written": report["d1_rows_written_reported"],
        "independent_headroom_verified": False,
        "scratch_authorized": False,
        "production_writes_authorized": False,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FOUNDATION_D1_RUNTIME_READONLY=identity_or_protection_failure")
        raise SystemExit(1)
