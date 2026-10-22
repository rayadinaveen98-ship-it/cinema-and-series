#!/usr/bin/env python3
"""Review-only independent-source gate and 20-row production preflight.

Only SELECT on 20 exact indexed QIDs. Never creates SQL writes, patches
production values, re-enables jobs, or implies a provider's database is
official proof of production film language.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0,str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows

QID = re.compile(r"Q[1-9][0-9]*\Z")
FIELDS = ("wikidata_qid","title","release_year","current_language",
          "proposed_language","independent_source","evidence_status",
          "production_preflight","review_status")
KEYS = ("id","wikidata_qid","title","release_year","country_code","language_name")
DOMAINS = {
    "www.imdb.com","www.netflix.com","www.moviebuff.com",
    "tamil.filmibeat.com","tv.apple.com","d1f72a6kha0tf8.cloudfront.net",
    "www.zee5.com","www.indianfilmhistory.com","timesofindia.indiatimes.com",
    "ollywood.odiaportal.in","in.bookmyshow.com",
}


def validate_sources(packet: dict, evidence: dict) -> list[dict]:
    if (packet.get("schema") != "data-foundation-v2-20-film-dryrun-v1"
            or packet.get("batch_size") != 20
            or packet.get("production_writes") != 0
            or packet.get("ready_for_production_write") is not False
            or evidence.get("schema") != "foundation-v2-independent-source-review-v1"
            or evidence.get("no_d1_writes") is not True
            or evidence.get("automatically_approved") != 0):
        raise ValueError("Unexpected correction packet/evidence contract")
    items = packet.get("items") or []
    statuses = evidence.get("entries") or []
    if len(items) != 20 or len(statuses) != 20:
        raise ValueError("Exactly 20 frozen records and 20 evidence entries required")
    keyed = {}
    for entry in statuses:
        qid = entry.get("wikidata_qid")
        if not isinstance(qid,str) or not QID.fullmatch(qid) or qid in keyed:
            raise ValueError("Duplicate or invalid evidence QID")
        url = entry.get("independent_source_url")
        state = entry.get("status")
        if not (state == "SECONDARY_CORROBORATION_REVIEW_REQUIRED"
                or isinstance(state,str) and state.startswith("HOLD_")):
            raise ValueError("Unknown independent-source evidence status")
        if url:
            parts = urlsplit(url)
            if parts.scheme != "https" or parts.hostname not in DOMAINS:
                raise ValueError("Unapproved or non-independent source")
        if state == "SECONDARY_CORROBORATION_REVIEW_REQUIRED" and not url:
            raise ValueError("Accepted secondary corroboration must have a source")
        if entry.get("approve_production_update") is not False or entry.get("studio_verified") is not False:
            raise ValueError("Evidence must not imply official approval")
        keyed[qid] = entry
    found = []
    for item in items:
        old = item.get("before") or {}
        qid = old.get("wikidata_qid")
        source = keyed.get(qid)
        if not source or old.get("table") != "catalogue_titles" or not item.get("rollback"):
            raise ValueError("Evidence missing for exact catalogue record")
        if source.get("language") != item.get("proposed",{}).get("language_name"):
            raise ValueError("Language mismatch between source and proposed correction")
        if item.get("human_approval") is not False or item.get("source_independent_confirmation") != "NOT_YET_OBTAINED":
            raise ValueError("Previous packet must still be held")
        found.append({"before":old,"after":item["proposed"],"evidence":source,
                      "rollback":item["rollback"]})
    if len({x["before"]["wikidata_qid"] for x in found}) != 20:
        raise ValueError("Duplicate 20-film proposal")
    return found


def preflight_query(items: list[dict]) -> str:
    if len(items) != 20:
        raise ValueError("Exactly 20 rows are required for the bounded preflight")
    qids = sorted(x["before"]["wikidata_qid"] for x in items)
    if any(not QID.fullmatch(q) for q in qids):
        raise ValueError("Unsafe QID for read-only SQL")
    # Unique QID index idx_catalogue_titles_wikidata_qid was created in migration 0017.
    return ("SELECT id,wikidata_qid,title,release_year,country_code,language_name "
            "FROM catalogue_titles WHERE wikidata_qid IN ("
            + ",".join("'" + q + "'" for q in qids)
            + ") ORDER BY wikidata_qid;")


def evaluate(items: list[dict], live: list[dict]) -> dict:
    by_qid = {}
    for r in live:
        qid = r.get("wikidata_qid")
        if qid in by_qid:
            raise ValueError("Duplicate QID in current production results")
        by_qid[qid] = r
    results = []
    for item in items:
        before, source, after = item["before"], item["evidence"], item["after"]
        current = by_qid.get(before["wikidata_qid"])
        same = current is not None and all(current.get(key) == before.get(key) for key in KEYS)
        evidence_ok = source["status"] == "SECONDARY_CORROBORATION_REVIEW_REQUIRED"
        status = ("SOURCE_AND_LIVE_PRECONDITIONS_MET_REVIEW_REQUIRED"
                  if same and evidence_ok
                  else "HOLD_LIVE_ROW_MISSING_OR_CHANGED" if not same
                  else "HOLD_EXTERNAL_SOURCE_REVIEW")
        results.append({
            "wikidata_qid": before["wikidata_qid"],"title":before["title"],
            "release_year":before["release_year"],
            "current_language":current.get("language_name") if current else None,
            "before":before,"proposed":after,
            "external_source_status":source["status"],
            "independent_source":source["independent_source_url"],
            "external_source_review_note":source["evidence_description"],
            "fresh_production_preconditions_met":same,
            "rollback":item["rollback"],
            "review_status":status,
            "owner_approved":False,
        })
    counts = Counter(x["review_status"] for x in results)
    return {
        "schema":"foundation-v2-20-current-row-preflight-v1",
        "read_only":True,"d1_writes":0,"generated_write_sql":False,
        "automatic_updates":0,"owner_approved":False,
        "total":len(results),"status_counts":dict(sorted(counts.items())),
        "results":results,
        "note":"Non-Wikimedia source corroboration is a research finding, not a studio certification or authorization to correct production.",
    }


def test_rollback_simulation(items: list[dict]) -> dict:
    db=sqlite3.connect(":memory:")
    db.execute("""CREATE TABLE catalogue_titles (
        id TEXT PRIMARY KEY,wikidata_qid TEXT,title TEXT,release_year INTEGER,
        country_code TEXT,language_name TEXT)""")
    for entry in items:
        old=entry["before"]
        db.execute("INSERT INTO catalogue_titles VALUES(?,?,?,?,?,?)",
                   tuple(old[k] for k in KEYS))
    original=list(db.execute("SELECT * FROM catalogue_titles ORDER BY wikidata_qid"))
    # Simulate updating and restoring only entries whose independent sources
    # support language. This is isolated in-memory SQLite, never Cloudflare.
    for entry in items:
        if entry["evidence"]["status"] != "SECONDARY_CORROBORATION_REVIEW_REQUIRED":
            continue
        old=entry["before"]
        cursor=db.execute(
            "UPDATE catalogue_titles SET language_name=? WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name=?",
            (entry["after"]["language_name"],)+tuple(old[k] for k in KEYS))
        if cursor.rowcount != 1:
            raise ValueError("Simulated forward guarded update failed")
    for entry in items:
        if entry["evidence"]["status"] != "SECONDARY_CORROBORATION_REVIEW_REQUIRED":
            continue
        old=entry["before"]
        cursor=db.execute(
            "UPDATE catalogue_titles SET language_name=? WHERE id=? AND wikidata_qid=? AND title=? AND release_year=? AND country_code=? AND language_name=?",
            (old["language_name"],old["id"],old["wikidata_qid"],old["title"],
             old["release_year"],old["country_code"],entry["after"]["language_name"]))
        if cursor.rowcount != 1:
            raise ValueError("Simulated rollback failed")
    restored=list(db.execute("SELECT * FROM catalogue_titles ORDER BY wikidata_qid"))
    if original != restored:
        raise ValueError("Simulated rollback did not restore exact previous values")
    db.close()
    return {"simulated_in_memory":True,"source_supported_rows_tested":sum(
        x["evidence"]["status"]=="SECONDARY_CORROBORATION_REVIEW_REQUIRED" for x in items),
        "rollback_restores_all_original_rows":True,
        "production_rollback_tested":False,"production_writes":0}


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    for field in ("packet","sources","out","csv","query_file","live_json"):
        p.add_argument("--"+field.replace("_","-"),type=Path,required=(field!="live_json"))
    args=p.parse_args()
    packet=json.loads(args.packet.read_text(encoding="utf-8"))
    sources=json.loads(args.sources.read_text(encoding="utf-8"))
    items=validate_sources(packet,sources)
    args.query_file.parent.mkdir(parents=True,exist_ok=True)
    query=preflight_query(items)
    args.query_file.write_text(query+"\n",encoding="utf-8")
    if args.live_json is None:
        print("PREVIEW_ONLY: 20-record bounded SELECT and source evidence validated.")
        return
    raw=json.loads(args.live_json.read_text(encoding="utf-8"))
    if (not isinstance(raw,list) or not raw or
            not isinstance(raw[0],dict) or
            raw[0].get("success") is not True):
        raise ValueError("D1 current-record preflight query failed, refusing to infer success")
    live=load_d1_rows(args.live_json)
    report=evaluate(items,live)
    report["rollback_simulation"]=test_rollback_simulation(items)
    meta=[entry.get("meta") for entry in raw if isinstance(entry,dict)]
    report["production_query_row_reads"]=sum(int(m.get("rows_read") or 0) for m in meta if isinstance(m,dict))
    report["production_reads_are_only_indexed_qid_selection"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with args.csv.open("w",encoding="utf-8",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=FIELDS)
        writer.writeheader()
        for row in report["results"]:
            writer.writerow({
                "wikidata_qid":row["wikidata_qid"],"title":row["title"],
                "release_year":row["release_year"],
                "current_language":row["current_language"],
                "proposed_language":row["proposed"]["language_name"],
                "independent_source":row["independent_source"],
                "evidence_status":row["external_source_status"],
                "production_preflight":row["fresh_production_preconditions_met"],
                "review_status":row["review_status"],
            })
    print("FOUNDATION_20_PREFLIGHT="+json.dumps({
        "total":report["total"],"counts":report["status_counts"],
        "rows_read":report["production_query_row_reads"],
        "rollback_test":report["rollback_simulation"],
        "production_writes":0},sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
