#!/usr/bin/env python3
"""File-backed, offline rollback rehearsal for Data Foundation V2.

Use only saved 20-row production SELECT, frozen correction packet and externally
reviewed decisions. Create/backup/restore a local SQLite test database. There is
NO production D1 connection, update workflow, cloud credential or generated
production SQL. None of these tests authorize real writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows

FIELDS = ("id", "wikidata_qid", "title", "release_year", "country_code", "language_name")
HELD_QIDS = frozenset(("Q20967570", "Q109519684", "Q20649744"))
TABLE_DDL = """CREATE TABLE catalogue_titles (
    id TEXT PRIMARY KEY,
    wikidata_qid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    release_year INTEGER NOT NULL,
    country_code TEXT NOT NULL,
    language_name TEXT,
    extra_note TEXT NOT NULL DEFAULT 'preserve'
)"""
FORWARD_SQL = """UPDATE catalogue_titles SET language_name = ?
 WHERE id = ? AND wikidata_qid = ? AND title = ?
 AND release_year = ? AND country_code = ? AND language_name IS ?"""
REVERSE_SQL = """UPDATE catalogue_titles SET language_name = ?
 WHERE id = ? AND wikidata_qid = ? AND title = ?
 AND release_year = ? AND country_code = ? AND language_name = ?"""


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def validated_rows(packet: dict, reviewed: dict, response: list[dict]) -> tuple[list[dict], list[dict]]:
    require(packet.get("schema") == "data-foundation-v2-20-film-dryrun-v1"
            and packet.get("batch_size") == 20 and packet.get("production_writes") == 0
            and packet.get("ready_for_production_write") is False,
            "Frozen 20-film packet is not the expected held review input")
    require(reviewed.get("schema") == "data-foundation-v2-reviewed-current-20-v1"
            and reviewed.get("preflight_existing_titles") == 20
            and reviewed.get("review_candidates") == 17 and reviewed.get("held") == 3
            and reviewed.get("d1_writes") == 0
            and reviewed.get("production_write_authorized") is False
            and reviewed.get("automatically_approved") == 0,
            "External review is not the accepted 17/3 non-write assessment")
    require(isinstance(response, list) and len(response) == 1
            and response[0].get("success") is True,
            "Saved D1 read-only SELECT did not succeed")
    live = load_d1_rows_from_response(response)
    require(len(live) == 20, "Saved current 20-row read response is incomplete")
    by_qid = {}
    for row in live:
        qid = row.get("wikidata_qid")
        require(isinstance(qid, str) and qid not in by_qid,
                "Duplicate or missing production snapshot QID")
        by_qid[qid] = row
    review_index = {r.get("qid"): r for r in reviewed["results"]}
    require(len(review_index) == 20 and len(reviewed["results"]) == 20,
            "Duplicate reviewed identity")
    eligible, held = [], []
    for record in packet["items"]:
        old = record["before"]
        qid = old["wikidata_qid"]
        source = review_index.get(qid)
        current = by_qid.get(qid)
        require(source is not None and current is not None,
                "Review identity is missing from exact current snapshot")
        require(old.get("table") == "catalogue_titles"
                and all(old.get(k) == current.get(k) for k in FIELDS),
                "Original production row changed since 20-row preflight")
        require(record.get("human_approval") is False
                and record.get("source_independent_confirmation") == "NOT_YET_OBTAINED"
                and record.get("status", "").startswith("HOLD_"),
                "Frozen record improperly marked approved")
        require(source["source_id"] == old["id"]
                and source["year"] == old["release_year"]
                and source["title"] == old["title"]
                and source["proposed_language"] == record["proposed"]["language_name"]
                and source["current_language"] == old["language_name"],
                "External review and frozen before/after mismatch")
        item = {"before": old, "after": record["proposed"]["language_name"]}
        if source["status"] == "REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED":
            require(qid not in HELD_QIDS and source["external_status"] == "SUPPORT"
                    and source["production_status"] == "CURRENT_PRECONDITIONS_MATCH",
                    "A disputed item was unexpectedly proposed for a change")
            eligible.append(item)
        else:
            require(qid in HELD_QIDS and source["status"] == "HOLD",
                    "Unreviewed item incorrectly held or omitted")
            held.append(item)
    require(len(eligible) == 17 and len(held) == 3
            and {x["before"]["wikidata_qid"] for x in held} == HELD_QIDS
            and len({x["before"]["wikidata_qid"] for x in eligible + held}) == 20,
            "Correction selection drift")
    return eligible, held


def load_d1_rows_from_response(response: list[dict]) -> list[dict]:
    batch = response[0].get("results")
    require(isinstance(batch, list), "Malformed read-only query result")
    return batch


def snapshot(conn: sqlite3.Connection) -> list[tuple]:
    return conn.execute(
        "SELECT id,wikidata_qid,title,release_year,country_code,language_name,extra_note "
        "FROM catalogue_titles ORDER BY wikidata_qid"
    ).fetchall()


def populate(conn: sqlite3.Connection, original: list[dict]) -> None:
    conn.execute(TABLE_DDL)
    for row in original:
        conn.execute(
            "INSERT INTO catalogue_titles(id,wikidata_qid,title,release_year,"
            "country_code,language_name,extra_note) VALUES (?,?,?,?,?,?,?)",
            tuple(row[k] for k in FIELDS) + ("no collateral edits",))
    # Prove the recovery path does not accidentally mutate unrelated rows.
    conn.execute(
        "INSERT INTO catalogue_titles VALUES(?,?,?,?,?,?,?)",
        ("unrelated-1", "Q999999999", "Unrelated film", 1975, "IN",
         "Tamil", "must remain unchanged"))
    conn.commit()


def guarded_apply(conn: sqlite3.Connection, eligible: list[dict]) -> None:
    conn.execute("BEGIN IMMEDIATE")
    try:
        for item in eligible:
            old = item["before"]
            cur = conn.execute(
                FORWARD_SQL,
                (item["after"],) + tuple(old[k] for k in FIELDS))
            if cur.rowcount != 1:
                raise ValueError("Stale before-value; atomic local forward transaction aborted")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def guarded_reverse(conn: sqlite3.Connection, eligible: list[dict]) -> None:
    conn.execute("BEGIN IMMEDIATE")
    try:
        for item in reversed(eligible):
            old = item["before"]
            cur = conn.execute(
                REVERSE_SQL,
                (old["language_name"], old["id"], old["wikidata_qid"],
                 old["title"], old["release_year"], old["country_code"], item["after"]))
            if cur.rowcount != 1:
                raise ValueError("Newer current value detected; inverse must never overwrite it")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def run_rehearsal(packet: dict, reviewed: dict, response: list[dict]) -> dict:
    eligible, held = validated_rows(packet, reviewed, response)
    live = load_d1_rows_from_response(response)
    with tempfile.TemporaryDirectory(prefix="foundation-v2-rollback-") as folder:
        root = Path(folder)
        conn = sqlite3.connect(root / "fixture.sqlite")
        populate(conn, live)
        original = snapshot(conn)
        fingerprint = hashlib.sha256(repr(original).encode("utf-8")).hexdigest()
        backup = sqlite3.connect(root / "original-backup.sqlite")
        conn.backup(backup)
        require(snapshot(backup) == original, "Backup differs from exact original SQLite table")
        backup.close()

        guarded_apply(conn, eligible)
        after = snapshot(conn)
        require(len(after) == len(original) and len(after) == 21,
                "Local update inserted or removed a row")
        post = {r[1]: r[5] for r in after}
        require(all(post[x["before"]["wikidata_qid"]] == x["after"] for x in eligible),
                "Not all supported languages were updated in isolation")
        require(all(post[x["before"]["wikidata_qid"]] == x["before"]["language_name"]
                    for x in held), "Disputed language was edited")
        require(post["Q999999999"] == "Tamil", "Unrelated row was edited")

        guarded_reverse(conn, eligible)
        require(snapshot(conn) == original, "Guarded inverse failed exact full-row round trip")

        # Explicit backup/restore rehearsal on another disposable database.
        guarded_apply(conn, eligible)
        restored = sqlite3.connect(root / "restored.sqlite")
        src = sqlite3.connect(root / "original-backup.sqlite")
        src.backup(restored)
        require(snapshot(restored) == original, "SQLite restored file differs from backup")
        restored.close()
        src.close()
        conn.close()

        # Inject a stale current value at the LAST chosen update: the previous
        # 16 writes must rollback atomically, preserving the other actor's edit.
        drift = sqlite3.connect(root / "original-backup.sqlite")
        clone = sqlite3.connect(root / "stale-fixture.sqlite")
        drift.backup(clone)
        drift.close()
        last = eligible[-1]["before"]["wikidata_qid"]
        clone.execute("UPDATE catalogue_titles SET language_name='Edited by another actor' "
                      "WHERE wikidata_qid=?", (last,))
        clone.commit()
        stale_original = snapshot(clone)
        rejected = False
        try:
            guarded_apply(clone, eligible)
        except ValueError:
            rejected = True
        require(rejected and snapshot(clone) == stale_original,
                "Stale forward update did not rollback ALL earlier writes")

        # Inverse must refuse to overwrite an independently edited language,
        # even if 16 rows could have been restored.
        clone.execute("UPDATE catalogue_titles SET language_name=? WHERE wikidata_qid=?",
                      (eligible[-1]["before"]["language_name"], last))
        clone.commit()
        guarded_apply(clone, eligible)
        clone.execute("UPDATE catalogue_titles SET language_name='More recent user edit' "
                      "WHERE wikidata_qid=?", (eligible[0]["before"]["wikidata_qid"],))
        clone.commit()
        tampered_post = snapshot(clone)
        inverse_rejected = False
        try:
            guarded_reverse(clone, eligible)
        except ValueError:
            inverse_rejected = True
        require(inverse_rejected and snapshot(clone) == tampered_post,
                "Inverse incorrectly overwrote intervening edits")
        clone.close()

    return {
        "schema": "data-foundation-v2-filebacked-rollback-proof-v1",
        "original_20_existing_records": 20,
        "supported_review_only": len(eligible),
        "disputed_held": len(held),
        "test_database": "isolated_file_backed_sqlite",
        "local_simulated_updates": len(eligible),
        "full_row_exact_inverse": True,
        "sqlite_backup_created_and_verified": True,
        "sqlite_restore_to_separate_file_verified": True,
        "held_and_unrelated_rows_unchanged": True,
        "stale_forward_aborts_atomically": True,
        "intervening_edit_blocks_inverse": True,
        "original_snapshot_sha256": fingerprint,
        "cloudflare_d1_restore_tested": False,
        "cloudflare_d1_time_travel_bookmark_captured": False,
        "production_revalidated_at_write_time": False,
        "production_write_authorized": False,
        "production_reads_this_run": 0,
        "production_writes": 0,
        "sql_output_generated": False,
        "notes": ("Validated against a file-backed SQLite fixture cloned from saved real 20-row "
                  "D1 query. This is NOT a full D1 clone or verified production restore. "
                  "A fresh pre-write row validation, Cloudflare recovery bookmark, approval "
                  "and test on a non-production D1 database remain mandatory."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("packet", "review", "current", "out"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    review = json.loads(args.review.read_text(encoding="utf-8"))
    current = json.loads(args.current.read_text(encoding="utf-8"))
    result = run_rehearsal(packet, review, current)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FOUNDATION_FILEBACKED_ROLLBACK=" + json.dumps({
        key: result[key] for key in (
            "supported_review_only", "disputed_held", "full_row_exact_inverse",
            "sqlite_backup_created_and_verified",
            "sqlite_restore_to_separate_file_verified",
            "stale_forward_aborts_atomically", "intervening_edit_blocks_inverse",
            "production_reads_this_run", "production_writes",
            "production_write_authorized",
        )
    }, sort_keys=True))


if __name__ == "__main__":
    main()
