#!/usr/bin/env python3
"""Fast offline, entire-catalogue P364 reconciliation from existing source evidence.

Consumes a SAVED production snapshot + durable source checkpoint. No D1, no
network, no title creation, no DB writes. Generates deterministic, guarded
per-table correction *proposals* for later batch approval. Known conflicting
film QIDs are held. Each proposal retains original title/year, source URL.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from foundation_language_review import build as original_review
from production_catalogue_quality import load_d1_rows, movie_projection, known, norm, valid_qid

SCHEMA="foundation-v2-bulk-existing-films-v1"
HELD_QIDS=frozenset({"Q20967570","Q20649744","Q109519684"})
ALLOWED_TABLES=("catalogue_titles","movies")
MAX_CHUNK=200


def require(predicate: bool, description: str) -> None:
    if not predicate:
        raise ValueError(description)


def quote(v: object) -> str:
    require(isinstance(v, (str,int)) and not isinstance(v,bool), "Invalid SQL value")
    return "'"+str(v).replace("'","''")+"'"


def build(movies:list[dict], catalogue:list[dict], series:list[dict], checkpoint:dict,
          *, require_production_baseline:bool=True) -> dict:
    report=original_review(movies,catalogue,series,checkpoint)
    canonical, overlaps=movie_projection(movies,catalogue)
    if require_production_baseline:
        require(len(canonical)==51872 and len(series)==18303 and overlaps==998,
                "Full production source snapshot differs from locked catalogue baseline")
        require(sum(not known(r.get("language_name")) for r in canonical+series)==50380,
                "Frozen production unknown-language baseline unexpectedly drifted")
        require(len(checkpoint.get("records",{}))>=14674,
                "Source language checkpoint older than accelerated run")
    exact={(r.get("wikidata_qid") or "").upper():r for r in movies
           if valid_qid(r.get("wikidata_qid"))}
    selected, exclusions = [], []
    for row in report["proposals"]:
        qid=row["wikidata_qid"]
        if qid in HELD_QIDS:
            exclusions.append({"wikidata_qid":qid,"title":row["title"],
                               "hold_reason":"KNOWN_IDENTITY_OR_RELEASE_YEAR_CONFLICT"})
            continue
        require(row["source_table"] in ALLOWED_TABLES, "Unsafe proposal table")
        require(row["claim_property"]=="P364" and row["status"]=="REVIEW_REQUIRED"
                and row["source_url"]=="https://www.wikidata.org/wiki/"+qid,
                "Non-P364 evidence entered reviewed output")
        require(norm(row["current_language"]) in {"","unknown","xx","und","n/a","na","none","null"},
                "Attempt to overwrite known language")
        row=dict(row)
        row["language_source"]="wikidata:P364"
        row["language_source_url"]=row["source_url"]
        row["review_status"]="SOURCE_MATCH_ONLY_NOT_PRODUCTION_APPROVED"
        if row["source_table"]=="movies":
            source=exact.get(qid)
            require(source is not None and str(source.get("id"))==row["source_id"],
                    "Exact-date movies source QID identity drift")
            date=source.get("release_date")
            require(isinstance(date,str) and date[:4]==str(row["year"]),
                    "Missing exact date guard on movies")
            row["original_release_date"]=date
        else:
            row["original_release_date"]=None
        selected.append(row)
    selected.sort(key=lambda x:(x["source_table"],x["wikidata_qid"]))
    require(len({(p["source_table"],p["wikidata_qid"]) for p in selected})==len(selected),
            "Repeated selected film identity")
    counts=Counter(x["source_table"] for x in selected)
    languages=Counter(x["proposed_language"] for x in selected)
    digest=hashlib.sha256(json.dumps(selected,sort_keys=True,ensure_ascii=False,
                                     separators=(",",":")).encode("utf-8")).hexdigest()
    return {
        "schema":SCHEMA,"read_only":True,"source_checkpoint_records":len(checkpoint["records"]),
        "frozen_catalogue_movies":len(canonical),"frozen_catalogue_series":len(series),
        "overlapping_catalogue_rows_suppressed":overlaps,
        "correction_candidates":len(selected),
        "by_table":dict(sorted(counts.items())),
        "by_language":dict(sorted(languages.items())),
        "manual_held":exclusions,
        "source_rule_holds":len(report["holds"]),
        "source_review_counts":report["counts"],
        "records":selected,
        "records_sha256":digest,
        "d1_reads":0,"d1_writes":0,"production_changes":0,
        "source_evidence_independently_officially_verified":False,
        "writes_authorized":False,
        "note":("All candidates have exact existing film QID/title/year and P364 claim evidence. "
                "These are NOT individually independent studio verifications. No production edits."),
    }


def guarded_sql(row:dict)->str:
    table=row["source_table"]
    require(table in ALLOWED_TABLES and valid_qid(row.get("wikidata_qid")),
            "Unsafe table or film identity")
    require(row["claim_property"]=="P364" and row["review_status"]==
            "SOURCE_MATCH_ONLY_NOT_PRODUCTION_APPROVED",
            "Source rule authorization failed")
    where=("id="+quote(row["source_id"])+" AND wikidata_qid="+quote(row["wikidata_qid"])
           +" AND title="+quote(row["title"])+" COLLATE NOCASE"
           +" AND country_code='IN'")
    if table=="catalogue_titles":
        where+=" AND release_year="+str(int(row["year"]))
        set_values=("language_name="+quote(row["proposed_language"])
                    +",language_source='wikidata:P364'"
                    +",language_source_url="+quote(row["source_url"]))
        guard=" AND (language_source IS NULL OR TRIM(language_source)='')"
    else:
        where+=" AND release_date="+quote(row["original_release_date"])
        set_values="language_name="+quote(row["proposed_language"])
        # No language_source field currently exists in movies; exact original
        # evidence is instead retained in this complete review manifest.
        guard=""
    return ("UPDATE "+table+" SET "+set_values+",updated_at=CURRENT_TIMESTAMP "
            +"WHERE "+where
            +" AND (language_name IS NULL OR LOWER(TRIM(language_name)) "
            +"IN ('','unknown','xx','und','n/a','na','none','null'))"
            +guard+";")


def write_package(result:dict, folder:Path, *, chunk_size:int=150)->None:
    require(1<=chunk_size<=MAX_CHUNK,"Excessive D1 statement batch")
    require(result["read_only"] and not result["writes_authorized"]
            and result["d1_reads"]==result["d1_writes"]==0,
            "This is a review-only bulk output")
    folder.mkdir(parents=True,exist_ok=True)
    (folder/"all-candidates.json").write_text(json.dumps(result,ensure_ascii=False,
                            sort_keys=True,indent=2)+"\n",encoding="utf-8")
    fields=("source_table","source_id","wikidata_qid","title","year",
            "original_release_date","current_language","proposed_language",
            "language_source","language_source_url","review_status")
    with (folder/"all-candidates.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(result["records"])
    batches=[]
    for table in ALLOWED_TABLES:
        found=[x for x in result["records"] if x["source_table"]==table]
        for i in range(0,len(found),chunk_size):
            chunk=found[i:i+chunk_size]
            name=f"{table}-{i//chunk_size:03d}.sql"
            path=folder/name
            header=("-- REVIEW ONLY: do NOT run without owner-approved recovery backup "
                    "and fresh full-row D1 preflight.\n")
            path.write_text(header+"\n".join(guarded_sql(row) for row in chunk)+"\n",
                            encoding="utf-8")
            batches.append({"file":name,"table":table,"rows":len(chunk),
                            "from":i,"to_exclusive":i+len(chunk)})
    plan={key:result[key] for key in (
        "schema","frozen_catalogue_movies","frozen_catalogue_series",
        "source_checkpoint_records","correction_candidates",
        "by_table","by_language","manual_held","source_rule_holds",
        "records_sha256","d1_reads","d1_writes","writes_authorized")}
    plan["sql_batches"]=batches
    plan["batch_size_max"]=chunk_size
    plan["writes_executed"]=0
    plan["requires_owner_authorized_sealed_backup"]=True
    plan["source_evidence_still_requires_fresh_validation"]=True
    (folder/"batch-plan.json").write_text(json.dumps(plan,ensure_ascii=False,
                                   indent=2)+"\n",encoding="utf-8")


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("movies","catalogue","series","checkpoint","out-dir"):
        p.add_argument("--"+arg,required=True,type=Path)
    a=p.parse_args()
    result=build(load_d1_rows(a.movies),load_d1_rows(a.catalogue),
                 load_d1_rows(a.series),
                 json.loads(a.checkpoint.read_text(encoding="utf-8")))
    write_package(result,a.out_dir)
    print("FOUNDATION_BULK_FILM_RECONCILIATION="+json.dumps({
        "checkpoint":result["source_checkpoint_records"],
        "candidates":result["correction_candidates"],
        "by_table":result["by_table"],"held":len(result["manual_held"]),
        "source_holds":result["source_rule_holds"],
        "writes":result["d1_writes"]},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
