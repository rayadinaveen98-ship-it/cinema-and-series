#!/usr/bin/env python3
"""Combine four P364 source-only shards into one existing-series correction queue.

Archived production snapshot only. No live D1 access, DB updates or guessed
original languages. All series QIDs and existing Unknown values must match.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from enrich_series_languages import load_d1_rows, select_candidates, language_unknown, valid_qid

SCHEMA="foundation-v2-bulk-existing-series-v1"


def require(ok:bool,reason:str)->None:
    if not ok: raise ValueError(reason)


def combine(rows:list[dict],shards:list[dict],*,baseline:bool=True)->dict:
    if baseline: require(len(rows)==18303,"Production series baseline changed")
    require(len(shards)==4 and {s.get("shard_index") for s in shards}==set(range(4)),
            "Four unique series evidence shards are required")
    require(all(s.get("schema_version")=="series-language-enrichment-v1"
                and s.get("property")=="P364" and s.get("shard_count")==4 for s in shards),
            "Only original-language P364 source shards accepted")
    by_qid={}
    for row in rows:
        qid=str(row.get("wikidata_qid") or "").upper()
        if valid_qid(qid):
            require(qid not in by_qid,"Duplicate existing-series QID")
            by_qid[qid]=row
    source_candidates=sum(
        language_unknown(r.get("language_name")) and valid_qid(r.get("wikidata_qid"))
        for r in rows)
    unknown=sum(language_unknown(r.get("language_name")) for r in rows)
    selected_ids=set()
    supported=[]
    counters=Counter()
    for shard in sorted(shards,key=lambda s:s["shard_index"]):
        index=shard["shard_index"]
        expected=select_candidates(rows,8000,shard_index=index,shard_count=4)
        require(shard["candidate_count"]==len(expected),
                "One source shard omitted or double-counted existing series")
        counts=(shard["update_count"]+shard["ambiguous_count"]+
                shard["missing_claim_count"]+shard["missing_label_count"])
        require(counts==len(expected),"Series source shard outcomes do not reconcile")
        expected_qids={str(r["wikidata_qid"]).upper() for r in expected}
        for group in ("updates","ambiguous","missing_claim","missing_label"):
            require(len(shard[group])==shard[
               {"updates":"update_count","ambiguous":"ambiguous_count",
                "missing_claim":"missing_claim_count","missing_label":"missing_label_count"}[group]],
                "Mismatched source shard detail counts")
            for entry in shard[group]:
                qid=entry["wikidata_qid"].upper()
                require(qid in expected_qids and qid not in selected_ids,
                        "Unreviewed or duplicate shard QID")
                original=by_qid[qid]
                require(entry["id"]==original["id"] and entry["title"]==original["title"]
                        and language_unknown(original.get("language_name")),
                        "Series identity or current-language drift")
                selected_ids.add(qid)
        for item in shard["updates"]:
            qid=item["wikidata_qid"].upper()
            require(item["language_source"]=="wikidata:P364"
                    and item["language_source_url"]=="https://www.wikidata.org/wiki/"+qid
                    and item.get("language") and valid_qid(item.get("language_qid")),
                    "Source lacks original-language P364 provenance")
            original=by_qid[qid]
            supported.append({
                "id":item["id"],"wikidata_qid":qid,"title":item["title"],
                "first_air_year":original.get("first_air_year"),
                "original_language_name":original.get("language_name"),
                "proposed_language":item["language"],
                "language_qid":item["language_qid"],
                "source":item["language_source"],
                "source_url":item["language_source_url"],
                "review_status":"SOURCE_P364_ONLY_NOT_APPROVED",
            })
        counters.update({
            "ambiguous_count":shard["ambiguous_count"],
            "missing_claim_count":shard["missing_claim_count"],
            "missing_label_count":shard["missing_label_count"],
        })
    require(len(selected_ids)==source_candidates,"Entire valid-QID unknown series population not analyzed")
    require(len(supported)+sum(counters.values())==source_candidates,
            "Series source outcomes do not account for original unknown population")
    supported.sort(key=lambda x:x["wikidata_qid"])
    signature=hashlib.sha256(json.dumps(supported,sort_keys=True,
          ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
    return {
        "schema":SCHEMA,"total_existing_series":len(rows),
        "series_unknown_language":unknown,
        "unique_existing_unknown_qids":source_candidates,
        "series_without_valid_qid":unknown-source_candidates,
        "source_candidates":source_candidates,
        "language_candidates":len(supported),
        "ambiguous_count":counters["ambiguous_count"],
        "missing_claim_count":counters["missing_claim_count"],
        "missing_label_count":counters["missing_label_count"],
        "records_sha256":signature,"records":supported,
        "d1_reads":0,"d1_writes":0,"production_changes":0,
        "source_only":True,"writes_authorized":False,
        "note":"Unambiguous Wikidata P364 only; not official/studio original-language confirmation. No DB changes."
    }


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("input","shards","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    files=sorted(a.shards.glob("foundation-v2-series-source-shard-*/shard-*.json"))
    if len(files)!=4: raise ValueError("Four disjoint downloaded shard reports required")
    result=combine(load_d1_rows(a.input),
                   [json.loads(f.read_text(encoding="utf-8")) for f in files])
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FOUNDATION_BULK_SERIES_RECONCILIATION="+json.dumps({
        "source_candidates":result["source_candidates"],"language_candidates":result["language_candidates"],
        "ambiguous":result["ambiguous_count"],"missing_claim":result["missing_claim_count"],
        "missing_label":result["missing_label_count"],
        "d1_reads":0,"d1_writes":0},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
