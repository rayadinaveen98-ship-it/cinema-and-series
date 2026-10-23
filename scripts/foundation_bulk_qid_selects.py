#!/usr/bin/env python3
"""Generate small QID-only SELECT chunks and combine private D1 reads.

No production updates. Source manifests must already pass the bulk backup
manifest validation. Exact QID filtering prevents expensive full-table scans.
Private read files must stay on ephemeral CI runner; only sealed output uploads.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from foundation_bulk_sealed_backup import checked_manifest, QID


def create_queries(film:dict,series:dict,out:Path,size:int=400)->dict:
    if size<1 or size>500:
        raise ValueError("SELECT chunk must contain 1–500 QIDs")
    fs,ss=checked_manifest(film,series)
    out.mkdir(parents=True,exist_ok=True)
    counts={}
    for table, records in (("catalogue_titles",fs),("series_titles",ss)):
        ids=sorted(r["wikidata_qid"] for r in records)
        if len(ids)!=len(set(ids)) or not all(QID.fullmatch(q) for q in ids):
            raise ValueError("Invalid or duplicate exact catalogue QIDs")
        batches=[]
        for index,start in enumerate(range(0,len(ids),size)):
            qids=ids[start:start+size]
            path=out/f"{table}-{index:03d}.sql"
            statement=("SELECT * FROM "+table+" WHERE wikidata_qid IN ("
                       +",".join("'"+qid+"'" for qid in qids)
                       +") ORDER BY wikidata_qid;\n")
            path.write_text(statement,encoding="utf-8")
            batches.append(path.name)
        counts[table]={"candidates":len(ids),"queries":batches}
    manifest={"schema":"foundation-v2-guarded-select-chunks-v1","tables":counts,
              "total_candidates":len(fs)+len(ss),"sql_mode":"READ_ONLY_SELECT_ONLY",
              "production_writes":0}
    (out/"query-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


def combine_sql_results(folder:Path,table:str,out:Path)->None:
    if table not in {"catalogue_titles","series_titles"}:
        raise ValueError("Unapproved table")
    folder_manifest=json.loads((folder/"queries/query-manifest.json").read_text())
    batches=folder_manifest["tables"][table]["queries"]
    allrows=[]
    for index,filename in enumerate(batches):
        response_file=folder/"private-reads"/(table+"-"+str(index).zfill(3)+".json")
        if not response_file.is_file():
            raise ValueError("Missing current D1 read chunk")
        payload=json.loads(response_file.read_text(encoding="utf-8"))
        if not isinstance(payload,list) or not payload or \
           any(part.get("success") is not True for part in payload):
            raise ValueError("D1 query did not report successful read")
        for part in payload:
            result=part.get("results")
            if not isinstance(result,list):
                raise ValueError("D1 query result malformed")
            allrows.extend(result)
    # Results may omit candidates that have become known or been deleted.
    seen=set()
    for record in allrows:
        qid=record.get("wikidata_qid")
        if not isinstance(qid,str) or not QID.fullmatch(qid) or qid in seen:
            raise ValueError("Current D1 result has duplicate or missing QID")
        seen.add(qid)
    if len(seen)>folder_manifest["tables"][table]["candidates"]:
        raise ValueError("D1 supplied more rows than approved QID list")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps([{"success":True,"results":allrows}],
                                ensure_ascii=False)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","merge"))
    for field in ("films","series","folder","table","out"):
        p.add_argument("--"+field,type=Path if field!="table" else str)
    args=p.parse_args()
    if args.mode=="plan":
        if args.films is None or args.series is None or args.folder is None:
            raise ValueError("Missing source review manifest or output folder")
        film=json.loads(args.films.read_text(encoding="utf-8"))
        series=json.loads(args.series.read_text(encoding="utf-8"))
        r=create_queries(film,series,args.folder)
        print("FOUNDATION_BULK_SELECTS="+json.dumps({
            "candidate_count":r["total_candidates"],
            "film_queries":len(r["tables"]["catalogue_titles"]["queries"]),
            "series_queries":len(r["tables"]["series_titles"]["queries"]),
            "production_writes":0},sort_keys=True))
    else:
        if args.folder is None or args.out is None or args.table is None:
            raise ValueError("Missing private D1 read parts")
        combine_sql_results(args.folder,args.table,args.out)


if __name__=="__main__":
    main()
