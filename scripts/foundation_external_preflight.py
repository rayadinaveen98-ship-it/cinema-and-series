#!/usr/bin/env python3
"""Merge reviewed external evidence and CURRENT read-only D1 preflight with 20-film packet.

Never writes D1 or generates production SQL. Disputed release years, weak external
identity evidence, duplicate/current-missing rows and stale before-values remain
held. Third-party corroboration != official certification/owner approval.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows, norm

QID = re.compile(r"Q[1-9][0-9]*\Z")
FIELDS=("qid","title","year","proposed_language","current_language","external_status",
        "production_status","status","evidence_url","reason")


def build(packet:dict,evidence:dict,current:list[dict]) -> dict:
    if packet.get("schema")!="data-foundation-v2-20-film-dryrun-v1":
        raise ValueError("Unrecognized dryrun")
    if packet.get("production_writes")!=0 or packet.get("ready_for_production_write") is not False or packet.get("batch_size")!=20:
        raise ValueError("Source dryrun is not immutable")
    if evidence.get("schema")!="data-foundation-v2-external-evidence-20-v1" or evidence.get("proposed_writes")!=0:
        raise ValueError("External evidence is not review-only")
    items=packet["items"]
    if not isinstance(items,list) or len(items)!=20:
        raise ValueError("Expected the fixed 20 existing films")
    checks=evidence["records"]
    if not isinstance(checks,list) or len(checks)!=20:
        raise ValueError("Exactly 20 externally reviewed film entries required")
    eindex={r.get("wikidata_qid"):r for r in checks}
    if len(eindex)!=20:
        raise ValueError("Duplicate evidence identity")
    indexes={}
    for row in current:
        qid=row.get("wikidata_qid")
        if not isinstance(qid,str) or not QID.fullmatch(qid):
            raise ValueError("Unexpected D1 QID in current snapshot")
        indexes.setdefault(qid,[]).append(row)
    outcomes=[]
    for item in items:
        before=item["before"]; after=item["proposed"]; qid=before["wikidata_qid"]
        check=eindex.get(qid)
        if not check or check.get("frozen_release_year")!=before["release_year"] or check.get("proposed_language")!=after["language_name"]:
            raise ValueError("External corroboration does not match frozen title/year/language")
        if check.get("production_update_authorized") is not False:
            raise ValueError("External review illegally marked production authorized")
        url=check.get("source_url")
        if (not isinstance(url,str) or not url.startswith("https://")
                or "wikidata.org" in url or "wikipedia.org" in url
                or check.get("decision") not in {"SUPPORT","HOLD_YEAR_CONFLICT","HOLD_WEAK_INDEPENDENT_IDENTITY"}):
            raise ValueError("Unsupported external evidence")
        matches=indexes.get(qid,[])
        if len(matches)!=1:
            prod="HOLD_MISSING_OR_MULTIPLE_CURRENT_ROWS"
        else:
            r=matches[0]
            same = (str(r.get("id"))==str(before["id"])
                    and r.get("title")==before["title"]
                    and r.get("release_year")==before["release_year"]
                    and r.get("country_code")==before["country_code"]
                    and norm(r.get("language_name"))==norm(before["language_name"])
                    and norm(r.get("language_name")) in {"","unknown"})
            prod="CURRENT_PRECONDITIONS_MATCH" if same else "HOLD_PRODUCTION_DRIFT"
        status=("REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED"
                if check["decision"]=="SUPPORT" and prod=="CURRENT_PRECONDITIONS_MATCH"
                else "HOLD")
        outcomes.append({
            "qid":qid,"title":before["title"],
            "year":before["release_year"],"proposed_language":after["language_name"],
            "current_language":matches[0].get("language_name") if len(matches)==1 else None,
            "external_status":check["decision"],"production_status":prod,
            "status":status,"evidence_url":url,"reason":check.get("review_note",""),
            "source_id":before["id"],
        })
    if len({r["qid"] for r in outcomes})!=20:
        raise ValueError("Duplicate packet QIDs")
    if set(eindex)!={r["qid"] for r in outcomes}:
        raise ValueError("External evidence QIDs do not cover batch exactly")
    counts=Counter(x["status"] for x in outcomes)
    return {
        "schema":"data-foundation-v2-reviewed-current-20-v1",
        "frozen_baseline_titles":70175,
        "preflight_existing_titles":len(outcomes),
        "production_query_type":"single_read_only_select_for_20_qids",
        "d1_writes":0,"new_title_inserts":0,"poster_writes":0,"sql_generated":False,
        "automatically_approved":0,"production_write_authorized":False,
        "review_candidates":counts.get("REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED",0),
        "held":counts.get("HOLD",0),"results":outcomes,
        "warning":"Independent public evidence and exact current D1 values still require owner approval, tested backup+rollback and a separately reviewed guarded write workflow."
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("packet","evidence","current","out","csv"):
        p.add_argument("--"+name,required=True,type=Path)
    args=p.parse_args()
    result=build(json.loads(args.packet.read_text(encoding="utf-8")),
                 json.loads(args.evidence.read_text(encoding="utf-8")),
                 load_d1_rows(args.current))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with args.csv.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=FIELDS,extrasaction="ignore")
        writer.writeheader();writer.writerows(result["results"])
    print("FOUNDATION_EXTERNAL_PREFLIGHT="+json.dumps({
        "total":result["preflight_existing_titles"],"supported_not_authorized":result["review_candidates"],
        "held":result["held"],"d1_writes":0,
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
