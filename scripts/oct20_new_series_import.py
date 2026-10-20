#!/usr/bin/env python3
"""One-time batch of actual new year-backed TV/streaming series.

Use Wikipedia year+country television series debut categories, exact Wikidata
QIDs, and fresh DB snapshots to guard cross-type identity collisions. Source
category alone is not an officially confirmed first air date. No updates to
existing titles; new series remain unconfirmed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from india_daily_autopilot import D1QuotaReached, D1Error, d1_execute
from production_catalogue_quality import load_d1_rows, norm
from verify_indian_movie_candidates import QID, sql_quote

RUN_MAX = 7000
SQL_BATCH = 90
LIMIT_READS = 1_200_000


def choose(sources: list[dict], exact: list[dict], catalogue: list[dict],
           series: list[dict], limit: int = RUN_MAX) -> tuple[list[dict], dict]:
    if not 1 <= limit <= RUN_MAX:
        raise ValueError("Unsafe series source batch size")
    known_qids = {
        str(row.get("wikidata_qid") or "").upper()
        for row in (exact+catalogue+series)
        if QID.fullmatch(str(row.get("wikidata_qid") or "").upper())
    }
    known_title_year = set()
    for row in exact+catalogue+series:
        title = norm(row.get("title"))
        raw = row.get("first_air_year") or row.get("release_year")
        date = row.get("release_date")
        if raw is None and isinstance(date,str) and date[:4].isdigit():
            raw=int(date[:4])
        if title and isinstance(raw,int):
            known_title_year.add((title,raw))
    selected=[]
    seen_qids=set()
    seen_title_year=set()
    reasons=Counter()
    for item in sources:
        qid=str(item.get("wikidata_qid") or "").upper()
        title=str(item.get("title") or "").strip()
        year=item.get("first_air_year")
        page=item.get("wikipedia_page_id")
        source=str(item.get("source_category") or "")
        url=str(item.get("source_url") or "")
        if (not QID.fullmatch(qid) or not title or title.upper()==qid
                or not isinstance(year,int) or not 1950<=year<=2026
                or not isinstance(page,int) or page<=0
                or not re.fullmatch(r"Category:\d{4} .+television series debuts",source)
                or not url.startswith("https://en.wikipedia.org/?curid=")):
            reasons["not_exact_year_country_series"]+=1
            continue
        key=(norm(title),year)
        if qid in known_qids:
            reasons["already_in_d1_qid"]+=1
            continue
        if key in known_title_year:
            reasons["known_title_year_collision"]+=1
            continue
        if qid in seen_qids or key in seen_title_year:
            reasons["source_collision"]+=1
            continue
        item=dict(item)
        item["wikidata_qid"]=qid
        selected.append(item)
        seen_qids.add(qid)
        seen_title_year.add(key)
        if len(selected)>=limit:
            break
    return selected,{
        "source_rows":len(sources),"selected_net_new":len(selected),
        "held_reasons":dict(reasons),
        "limit":limit,
        "source":"Wikipedia specific YYYY country television series debut categories",
        "no_official_first_air_day_claim":True,
    }


def sql_for_series(item: dict) -> str:
    qid=str(item["wikidata_qid"]).upper()
    if not QID.fullmatch(qid):
        raise ValueError("Invalid series identifier")
    year=int(item["first_air_year"])
    if not 1950<=year<=2026:
        raise ValueError("Invalid first air year")
    title=str(item["title"]).strip()
    if not title:
        raise ValueError("Missing series title")
    category=str(item["source_category"])
    if not re.fullmatch(r"Category:\d{4} .+television series debuts",category):
        raise ValueError("Untrusted year category")
    page=int(item["wikipedia_page_id"])
    if page<=0:
        raise ValueError("Invalid source page")
    source=f"https://en.wikipedia.org/?curid={page}"
    country=str(item.get("country_code") or "XX").upper()
    if not re.fullmatch(r"[A-Z]{2}",country):
        country="XX"
    q=sql_quote
    return (
        "INSERT OR IGNORE INTO series_titles "
        "(id,wikidata_qid,wikipedia_page_id,title,series_kind,language_name,"
        "country_code,first_air_year,lifecycle_status,source_category,"
        "source_url,verification_status,updated_at) "
        f"SELECT {q('series-wd-'+qid)},{q(qid)},{page},{q(title)},'series',"
        f"'Unknown',{q(country)},{year},'unknown',{q(category)},{q(source)},"
        "'unconfirmed',CURRENT_TIMESTAMP "
        "WHERE NOT EXISTS (SELECT 1 FROM movies m WHERE "
        f"m.wikidata_qid={q(qid)}) "
        "AND NOT EXISTS (SELECT 1 FROM catalogue_titles c WHERE "
        f"c.wikidata_qid={q(qid)}) "
        "AND NOT EXISTS (SELECT 1 FROM series_titles s WHERE "
        f"s.wikidata_qid={q(qid)}) "
        "AND NOT EXISTS (SELECT 1 FROM series_titles s WHERE "
        f"s.wikipedia_page_id={page}) "
        "AND NOT EXISTS (SELECT 1 FROM series_titles s WHERE "
        f"s.first_air_year={year} AND s.title={q(title)} COLLATE NOCASE) "
        "AND NOT EXISTS (SELECT 1 FROM catalogue_titles c WHERE "
        f"c.release_year={year} AND c.title={q(title)} COLLATE NOCASE) "
        "AND NOT EXISTS (SELECT 1 FROM movies m WHERE "
        f"m.title={q(title)} COLLATE NOCASE AND m.release_date BETWEEN "
        f"{q(str(year)+'-01-01')} AND {q(str(year)+'-12-31')});"
    )


def qids_in_series(qids: list[str]) -> set[str]:
    found=set()
    for start in range(0,len(qids),75):
        subset=qids[start:start+75]
        where=",".join(sql_quote(qid) for qid in subset)
        raw,_=d1_execute(sql=f"SELECT wikidata_qid FROM series_titles WHERE wikidata_qid IN ({where});")
        payload=json.loads(raw)
        for batch in payload:
            for row in batch.get("results",[]):
                found.add(str(row.get("wikidata_qid") or "").upper())
    return found


def apply(rows: list[dict], root: Path, *, execute=d1_execute,
          get_qids=qids_in_series, max_reads: int=LIMIT_READS) -> dict:
    if not 10000<=max_reads<=1_500_000:
        raise ValueError("Unsafe read budget")
    root.mkdir(parents=True,exist_ok=True)
    new=set()
    used=0
    submitted=0
    status="completed"
    for off in range(0,len(rows),SQL_BATCH):
        if used>=max_reads:
            status="read_budget_paused"
            break
        batch=rows[off:off+SQL_BATCH]
        qids=[x["wikidata_qid"] for x in batch]
        if len(qids)!=len(set(qids)):
            raise ValueError("Duplicate series QID in batch")
        sql="\n".join(sql_for_series(x) for x in batch)+"\n"
        if sql.count("INSERT OR IGNORE INTO series_titles")!=len(batch):
            raise ValueError("Unsafe SQL statement count")
        filename=root/f"series-{off//SQL_BATCH:03d}.sql"
        filename.write_text("-- New year-only, unconfirmed series. Insert-only.\n"+sql)
        try:
            _, cost=execute(sql_file=filename)
            used+=cost
            submitted+=len(batch)
            new |= set(get_qids(qids))
        except D1QuotaReached:
            status="cloudflare_quota_paused"
            break
        except D1Error:
            raise
    return {"status":status,"submitted":submitted,"verified_present_new_qids":len(new),
            "sql_rows_read":used,"selected":len(rows),"source_only_not_counted":True}


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",action="append",type=Path,required=True)
    p.add_argument("--exact",type=Path,required=True)
    p.add_argument("--catalogue",type=Path,required=True)
    p.add_argument("--series",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    sources=[]
    for source in args.source:
        payload=json.loads(source.read_text(encoding="utf-8"))
        sources.extend(payload.get("series") or [])
    selected, preview=choose(sources,load_d1_rows(args.exact),
                             load_d1_rows(args.catalogue),load_d1_rows(args.series))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/"preview.json").write_text(json.dumps(preview,indent=2)+"\n")
    print("NEW_SERIES_PREVIEW="+json.dumps(preview,sort_keys=True),flush=True)
    result=apply(selected,args.output_dir/"sql") if selected else {
        "status":"no_net_new_candidate","submitted":0,"verified_present_new_qids":0,
        "sql_rows_read":0,"selected":0,"source_only_not_counted":True
    }
    (args.output_dir/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print("NEW_SERIES_RESULT="+json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
