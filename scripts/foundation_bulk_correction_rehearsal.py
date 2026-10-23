#!/usr/bin/env python3
"""Full 16,681-record production-correction rehearsal on disposable SQLite.

Requires an authenticated AES-GCM recovery capsule from read-only workflow.
Never calls Cloudflare or produces runnable production SQL. Uses actual
catalogue_titles and series_titles migrations, exact original full-row values,
guarded atomic UPDATEs, full inverse and competing-edit rejection. Produces
only counts and hashes for owner review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

from foundation_verify_bulk_sealed_backup import verify_capsule
from foundation_bulk_sealed_backup import check_key, DISPUTED
import os

SCHEMA="foundation-v2-full-bulk-batch-rehearsal-v1"
TABLES=("catalogue_titles","series_titles")
MIGRATIONS=(
    "migrations/0017_year_precision_catalogue.sql",
    "migrations/0027_catalogue_title_language_provenance.sql",
    "migrations/0018_series_catalogue.sql",
    "migrations/0019_series_language_provenance.sql",
    "migrations/0020_series_first_air_year_provenance.sql",
)
UNKNOWN=frozenset({"","unknown","xx","und","n/a","na","none","null"})
SOURCE="wikidata:P364"


def require(ok: bool, message: str):
    if not ok:
        raise ValueError(message)


def full_sha(value:object)->str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
                      separators=(",",":")).encode("utf-8")).hexdigest()


def validate_snapshot(snapshot:dict, *, expected_count:int=16681)->list[dict]:
    require(snapshot.get("schema")=="foundation-v2-full-row-recovery-v1"
            and snapshot.get("production_database")=="cinema-and-series"
            and snapshot.get("ready_to_apply") is False
            and snapshot.get("production_writes")==0,
            "Untrusted source recovery snapshot")
    require(not snapshot.get("drift_issues"),"Full-bulk correction requires ZERO drift")
    items=snapshot.get("full_rows")
    require(isinstance(items,list) and len(items)==expected_count,
            "Full source batch not present")
    seen=set(); counts=Counter()
    for item in items:
        table=item.get("table")
        require(table in TABLES,"Unknown table in sealed recovery snapshot")
        row=item.get("row")
        require(isinstance(row,dict),"Missing complete before-row data")
        qid=row.get("wikidata_qid")
        require(isinstance(qid,str) and qid==item.get("qid")
                and qid.startswith("Q") and qid[1:].isdigit()
                and qid not in DISPUTED and (table,qid) not in seen,
                "Invalid/repeated/held QID")
        seen.add((table,qid));counts[table]+=1
        require(isinstance(row.get("id"),str) and row.get("title"),
                "Missing identity fields")
        require(str(row.get("language_name") or "").strip().lower() in UNKNOWN,
                "Existing known language cannot be overwritten")
        require(not str(row.get("language_source") or "").strip()
                and not str(row.get("language_source_url") or "").strip(),
                "Existing language provenance cannot be overwritten")
        proposed=item.get("proposed_language")
        require(isinstance(proposed,str) and proposed.strip()
                and proposed.lower() not in UNKNOWN,
                "Invalid proposed language")
        require(item.get("evidence_url")=="https://www.wikidata.org/wiki/"+qid,
                "Language source is not an exact QID")
        if table=="catalogue_titles":
            require(isinstance(row.get("release_year"),int)
                    and row.get("country_code")=="IN",
                    "Film year or country missing")
        else:
            require("first_air_year" in row,"Series identity year must be preserved")
    if expected_count==16681:
        require(counts=={"catalogue_titles":11667,"series_titles":5014},
                "Required source breakdown does not match the reviewed 16681")
    return sorted(items,key=lambda x:(x["table"],x["qid"]))


def connect_fixture(items:list[dict])->sqlite3.Connection:
    conn=sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    for path in MIGRATIONS:
        conn.executescript(Path(path).read_text(encoding="utf-8"))
    conn.execute("CREATE TABLE qa_guard(value INTEGER NOT NULL CHECK (value=0))")
    columns={
        table:{r[1] for r in conn.execute("PRAGMA table_info("+table+")")}
        for table in TABLES
    }
    for item in items:
        table=item["table"]
        row=item["row"]
        require(set(row).issubset(columns[table]),
                "Production row has columns missing from test schema: "+table)
        names=list(row)
        sql=("INSERT INTO "+table+" ("+",".join(names)+") VALUES ("
             +",".join("?" for _ in names)+")")
        conn.execute(sql,tuple(row[n] for n in names))
    for table in TABLES:
        sentinel={
            "id":"foundation-untouched-"+table,
            "wikidata_qid":"Q999999999",
            "title":"Untouched control record",
            "source_category":"foundation-QA",
            "source_url":"https://www.wikidata.org/wiki/Q999999999",
            "language_name":"Tamil"
        }
        if table=="catalogue_titles": sentinel["release_year"]=1975
        else: sentinel["first_air_year"]=1998
        sql="INSERT INTO "+table+" ("+",".join(sentinel)+") VALUES ("+(",".join("?" for _ in sentinel))+")"
        conn.execute(sql,tuple(sentinel.values()))
    conn.commit()
    return conn


def table_snapshot(conn:sqlite3.Connection,table:str)->list[dict]:
    conn.row_factory=sqlite3.Row
    return [dict(r) for r in conn.execute("SELECT * FROM "+table+" ORDER BY wikidata_qid")]


def guard_statement(item:dict,reverse:bool)->tuple[str,tuple]:
    table=item["table"];row=item["row"]
    # Full original-row compare prevents concurrent changes to ANY backed-up
    # field from being overwritten. IS ? handles both NULL and other values.
    before=dict(row)
    if reverse:
        before.update({
            "language_name":item["proposed_language"],
            "language_source":SOURCE,
            "language_source_url":item["evidence_url"],
        })
        # Every inverse checks the actual forward result. Since CURRENT_TIMESTAMP
        # can change during a batch, use the captured after values in the
        # test-only runner rather than assuming a specific wall-clock time.
        before["updated_at"]=item["_after_updated_at"]
    keys=sorted(before)
    expr=" AND ".join(col+" IS ?" for col in keys)
    return ("SELECT 1 FROM "+table+" WHERE "+expr, tuple(before[k] for k in keys))


def apply_batch(conn:sqlite3.Connection,items:list[dict],reverse:bool=False):
    conn.execute("BEGIN IMMEDIATE")
    try:
        for item in reversed(items) if reverse else items:
            table=item["table"];row=item["row"]
            check,params=guard_statement(item,reverse)
            # Impossible CHECK() value triggers SQL error; the entire batch
            # rolls back if a current before-value diverges by even one field.
            conn.execute("INSERT INTO qa_guard(value) SELECT 1 WHERE NOT EXISTS ("+check+")",params)
            if reverse:
                sql=("UPDATE "+table+
                     " SET language_name=?,language_source=?,language_source_url=?,updated_at=?"
                     " WHERE id=? AND wikidata_qid=?")
                inputs=(row["language_name"],row.get("language_source"),
                        row.get("language_source_url"),row["updated_at"],
                        row["id"],row["wikidata_qid"])
            else:
                sql=("UPDATE "+table+
                     " SET language_name=?,language_source=?,language_source_url=?,"
                     "updated_at=CURRENT_TIMESTAMP WHERE id=? AND wikidata_qid=?")
                inputs=(item["proposed_language"],SOURCE,item["evidence_url"],
                        row["id"],row["wikidata_qid"])
            cur=conn.execute(sql,inputs)
            if cur.rowcount!=1:
                raise ValueError("UPDATE expected exactly one prevalidated row")
            if not reverse:
                item["_after_updated_at"]=conn.execute(
                    "SELECT updated_at FROM "+table+" WHERE id=?",
                    (row["id"],)).fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def simulate(items:list[dict], *, batch_size:int=100,
             test_negative_cases:bool=True)->dict:
    require(1<=batch_size<=100,"Batch size limited to 100 existing titles")
    conn=connect_fixture(items)
    try:
        before={table:table_snapshot(conn,table) for table in TABLES}
        plan=[];total=0
        for table in TABLES:
            table_items=[i for i in items if i["table"]==table]
            for offset in range(0,len(table_items),batch_size):
                batch=table_items[offset:offset+batch_size]
                apply_batch(conn,batch)
                total+=len(batch)
                plan.append({
                    "table":table,"batch_number":offset//batch_size+1,
                    "candidate_count":len(batch),
                    "before_digest":full_sha([{key:it["row"][key] for key in it["row"]}
                                              for it in batch]),
                    "source_review_digest":full_sha([
                        (it["qid"],it["proposed_language"],it["evidence_url"]) for it in batch]),
                })
        require(total==len(items),"Not all valid corrections rehearsed")
        after={table:table_snapshot(conn,table) for table in TABLES}
        for table in TABLES:
            require(len(after[table])==len(before[table]),"Row count changed during forward")
        for batch in reversed(plan):
            selected=[it for it in items if it["table"]==batch["table"]]
            offset=(batch["batch_number"]-1)*batch_size
            apply_batch(conn,selected[offset:offset+batch["candidate_count"]],reverse=True)
        restored={table:table_snapshot(conn,table) for table in TABLES}
        require(restored==before,"Exact full-column inverse did not restore original data")
        stale_ok=False;inverse_ok=False
        if test_negative_cases:
            # Last-row stale check: every preceding UPDATE must roll back.
            selected=[i for i in items if i["table"]=="catalogue_titles"][:batch_size]
            if not selected:
                selected=items[:batch_size]
            table=selected[-1]["table"]
            qid=selected[-1]["qid"]
            conn.execute("UPDATE "+table+" SET language_name='Other editor change' WHERE wikidata_qid=?",(qid,))
            conn.commit()
            stale_baseline={t:table_snapshot(conn,t) for t in TABLES}
            try: apply_batch(conn,selected)
            except sqlite3.IntegrityError: stale_ok=True
            require(stale_ok and {t:table_snapshot(conn,t) for t in TABLES}==stale_baseline,
                    "Stale last-row value failed atomic rollback")
            conn.execute("UPDATE "+table+" SET language_name=? WHERE wikidata_qid=?",
                         (selected[-1]["row"]["language_name"],qid))
            conn.commit()
            apply_batch(conn,selected)
            conflict=selected[0]
            conn.execute("UPDATE "+conflict["table"]+
                         " SET language_name='Newer independent edit' WHERE wikidata_qid=?",
                         (conflict["qid"],))
            conn.commit()
            conflict_before={t:table_snapshot(conn,t) for t in TABLES}
            try: apply_batch(conn,selected,reverse=True)
            except sqlite3.IntegrityError: inverse_ok=True
            require(inverse_ok and {t:table_snapshot(conn,t) for t in TABLES}==conflict_before,
                    "Inverse overwrote newer third-party edit")
        counts=Counter(i["table"] for i in items)
        return {
            "schema":SCHEMA,"archive_full_rows":len(items),"candidate_tables":dict(counts),
            "proposed_operations":len(plan),
            "maximum_batch_size":batch_size,"per_batch_digests":plan,
            "all_forward_updates_applied_in_disposable_fixture":True,
            "all_full_original_rows_restored_exactly":True,
            "stale_forward_aborts_without_partial_writes":stale_ok if test_negative_cases else None,
            "competing_edit_blocks_inverse":inverse_ok if test_negative_cases else None,
            "unrelated_control_rows_preserved":True,
            "simulation_engine":"SQLite actual catalogue and series migrations",
            "source_evidence":"Wikidata P364 review only; independent producer confirmation NOT complete",
            "snapshot_staleness":"Historical recovery only; recheck live records immediately before any real write",
            "production_reads":0,"production_writes":0,
            "production_update_approved":False,
            "production_sql_generated":False,
        }
    finally:
        conn.close()


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sealed",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--batch-size",type=int,default=100)
    a=p.parse_args()
    key=check_key(os.environ.get("FOUNDATION_BACKUP_KEY_B64",""))
    envelope=json.loads(a.sealed.read_text(encoding="utf-8"))
    recovered=verify_capsule(envelope,key)
    items=validate_snapshot(recovered)
    result=simulate(items,batch_size=a.batch_size)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FOUNDATION_FULL_BULK_REHEARSAL="+json.dumps({
        "sampled":result["archive_full_rows"],"batches":result["proposed_operations"],
        "exact_rollback":result["all_full_original_rows_restored_exactly"],
        "production_writes":0,"approved":False
    },sort_keys=True))


if __name__=="__main__":
    main()
