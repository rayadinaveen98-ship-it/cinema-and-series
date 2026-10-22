#!/usr/bin/env python3
"""Read-only production prewrite check and optionally AES-GCM seal full-row recovery.

No UPDATE, DELETE, INSERT, migrations, exports, restore, or staging provisioning.
A captured bookmark is NOT an approval and becomes stale before a later write.
Missing encryption secret means no row snapshot is published, and the
production-write approval gate remains closed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows
from foundation_filebacked_rollback import validated_rows, load_d1_rows_from_response

PRODUCTION = "cinema-and-series"
SCHEMA = "foundation-v2-final-approval-preflight-v1"
QID = re.compile(r"Q[1-9][0-9]*\Z")
ID = re.compile(r"[a-fA-F0-9-]{36}\Z")
BEFORE_KEYS = ("id", "wikidata_qid", "title", "release_year",
               "country_code", "language_name")


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def guarded_select(packet: dict) -> str:
    require(packet.get("schema") == "data-foundation-v2-20-film-dryrun-v1"
            and packet.get("batch_size") == 20 and packet.get("production_writes") == 0
            and packet.get("ready_for_production_write") is False,
            "Original film packet is not the held review data")
    qids = [r["before"]["wikidata_qid"] for r in packet["items"]]
    require(len(qids) == len(set(qids)) == 20
            and all(QID.fullmatch(v) for v in qids), "Invalid review ID set")
    return ("SELECT * FROM catalogue_titles WHERE wikidata_qid IN ("
            + ", ".join("'" + q + "'" for q in sorted(qids)) + ")"
            + " ORDER BY wikidata_qid;")


def read_bookmark() -> tuple[str | None, str]:
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    require(re.fullmatch(r"[a-fA-F0-9]{32}", account) is not None
            and bool(token), "Cloudflare read credentials not configured")

    listed = subprocess.run(["npx", "wrangler", "d1", "list", "--json"],
                            check=False, text=True, capture_output=True,
                            timeout=90)
    require(listed.returncode == 0, "D1 control-plane listing unavailable")
    parsed = json.loads(listed.stdout)
    prod = [x for x in parsed if x.get("name") == PRODUCTION]
    require(len(prod) == 1, "Production D1 identity is missing or ambiguous")
    uuid = prod[0].get("uuid") or prod[0].get("id")
    require(isinstance(uuid, str) and ID.fullmatch(uuid) is not None,
            "Invalid production D1 UUID")

    url = ("https://api.cloudflare.com/client/v4/accounts/" + account
           + "/d1/database/" + uuid + "/time_travel/bookmark")
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "cinema-series-data-foundation-v2-read-only",
    }, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read(16384).decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None, "unavailable_from_cloudflare_api"
    if not data.get("success"):
        return None, "not_enabled_or_not_permitted"
    bookmark = (data.get("result") or {}).get("bookmark")
    if not isinstance(bookmark, str) or not bookmark.strip():
        return None, "missing_bookmark"
    return bookmark, "captured_read_only"


def make_report(packet: dict, reviewed: dict, raw: list[dict],
                bookmark: str | None, bookmark_status: str,
                key_b64: str | None) -> tuple[dict, dict | None]:
    # Reuse the exact 17/3 source and archived before-value gates.
    eligible, held = validated_rows(packet, reviewed, raw)
    rows = load_d1_rows_from_response(raw)
    require(len(rows) == 20, "Expected exactly 20 current full production rows")
    require(all(len(r) > len(BEFORE_KEYS) for r in rows),
            "This is not a full-column production row snapshot")
    by_id = {row.get("wikidata_qid"): row for row in rows}
    require(len(by_id) == 20, "Ambiguous current Wikidata IDs")
    require(len(eligible) == 17 and len(held) == 3, "17/3 review set changed")
    fingerprints = []
    for item in eligible + held:
        old = item["before"]
        new = by_id[old["wikidata_qid"]]
        require(all(new.get(k) == old[k] for k in BEFORE_KEYS),
                "Current identity or before-value drift")
        fingerprints.append({
            "wikidata_qid": old["wikidata_qid"], "title": old["title"],
            "year": old["release_year"],
            "proposed_language": item["after"],
            "status": "REVIEW_ONLY" if item in eligible else "HELD",
            "full_row_sha256": canonical_hash(new),
        })
    sealed = None
    encryption_status = "blocked_missing_foundation_backup_key"
    if key_b64:
        key = base64.b64decode(key_b64, validate=True)
        require(len(key) == 32, "Backup secret must decode to exactly 32 bytes")
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(12)
        plain = {
            "schema": "foundation-v2-sealed-recovery-payload-v1",
            "rows": rows, "reviewed_count": 17, "held_count": 3,
            "production_db": PRODUCTION, "bookmark": bookmark,
            "bookmark_status": bookmark_status,
        }
        aad = b"cinema-and-series/data-foundation-v2/recovery-only"
        encrypted = AESGCM(key).encrypt(
            nonce,
            json.dumps(plain, ensure_ascii=False, sort_keys=True).encode("utf-8"),
            aad)
        # Immediate authenticated-decrypt self-test; never expose decrypted data.
        recovered = json.loads(AESGCM(key).decrypt(nonce, encrypted, aad))
        require(recovered == plain, "Authenticated encryption round trip failed")
        sealed = {
            "schema": "foundation-v2-encrypted-backup-v1",
            "algorithm": "AES-256-GCM", "key_management": "GitHub repository secret FOUNDATION_BACKUP_KEY_B64",
            "nonce_base64": base64.b64encode(nonce).decode("ascii"),
            "ciphertext_base64": base64.b64encode(encrypted).decode("ascii"),
            "plaintext_sha256": canonical_hash(plain),
            "row_count": len(rows),
        }
        encryption_status = "encrypted_aes256gcm_and_self_tested"
    report = {
        "schema": SCHEMA, "mode": "READ_ONLY_NO_PRODUCTION_UPDATES",
        "database": PRODUCTION, "current_rows_checked": 20,
        "reviewed_candidates": 17, "held_disputed_films": 3,
        "saved_full_column_rows": 20 if sealed else 0,
        "backup_sealed_and_uploaded_by_workflow": sealed is not None,
        "encryption": encryption_status,
        "bookmark_status": bookmark_status,
        "bookmark_sha256": hashlib.sha256(bookmark.encode()).hexdigest() if bookmark else None,
        "bookmark_raw_disclosed": False,
        "current_full_row_fingerprint": canonical_hash(rows),
        "candidates": sorted(fingerprints, key=lambda x: x["wikidata_qid"]),
        "production_reads": "single 20-row read-only SELECT plus control-plane bookmark",
        "production_writes": 0, "sql_updates_generated": 0,
        "write_approved": False,
        "ready_to_write": False,
        "required_before_write": [
            "Explicit owner approval of exact 17 verified existing film records",
            "Fresh full-column backup, current recovery bookmark and immediate pre-write identity check",
            "Atomic guarded UPDATE with 17 rows exactly, no release-year changes",
            "No writes to three disputed records, other titles, posters or UI",
        ],
        "note": "Any bookmark captured here is informational; capture a NEW bookmark immediately before any later authorized write.",
    }
    require(report["write_approved"] is False and report["production_writes"] == 0,
            "Unexpected authorization state")
    return report, sealed


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("query", "report"))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--sealed", type=Path)
    parser.add_argument("--query-out", type=Path)
    args = parser.parse_args()

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    if args.mode == "query":
        require(args.query_out is not None, "--query-out required")
        args.query_out.parent.mkdir(parents=True, exist_ok=True)
        args.query_out.write_text(guarded_select(packet) + "\n", encoding="utf-8")
        print("FOUNDATION_FINAL_READONLY_QUERY=20 validated existing QIDs")
        return

    require(all(x is not None for x in (args.review, args.current, args.summary, args.sealed)),
            "Missing read-only preflight input")
    # Verify existing DB before invoking any bookmark read.
    assert guarded_select(packet).startswith("SELECT * FROM catalogue_titles")
    reviewed = json.loads(args.review.read_text(encoding="utf-8"))
    raw = json.loads(args.current.read_text(encoding="utf-8"))
    require(json.loads(Path("ops/data-foundation-v2-freeze.json").read_text())["active"] is True,
            "Production ingestion freeze not active")
    bookmark, status = read_bookmark()
    report, sealed = make_report(
        packet, reviewed, raw, bookmark, status,
        os.environ.get("FOUNDATION_BACKUP_KEY_B64", "").strip() or None)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    if sealed:
        args.sealed.parent.mkdir(parents=True, exist_ok=True)
        args.sealed.write_text(json.dumps(sealed, indent=2) + "\n", encoding="utf-8")
    print("FOUNDATION_FINAL_APPROVAL_GATE=" + json.dumps({
        "rows_checked": 20, "review_only": 17, "held": 3,
        "encrypted_backup": bool(sealed),
        "bookmark_status": status, "production_writes": 0,
        "write_authorized": False,
    }, sort_keys=True))


if __name__ == "__main__":
    run()
