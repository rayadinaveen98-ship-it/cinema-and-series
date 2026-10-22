#!/usr/bin/env python3
"""Independently recheck a stratified sample of existing film-language proposals.

Uses Wikidata current item claims: QID, English label/aliases, film class,
recorded publication year, and a single P364 original-language entity label.
This is a read-only *evidence recheck*, not an official original-language
certification, SQL migration, or authorization for production writes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wikimedia_paced_fetch import fetch as paced_fetch
from production_catalogue_quality import norm, known

LANGUAGES = (
    "Hindi", "Tamil", "Malayalam", "Telugu", "Kannada",
    "Bengali", "Odia", "Marathi", "Punjabi", "Gujarati",
)
FILM_QID = "Q11424"
QID = re.compile(r"Q[1-9][0-9]*\Z")
DATE = re.compile(r"^[+-](\d{4,5})-")
HEADERS = ("wikidata_qid", "source_id", "title", "year", "proposed_language",
           "language_qid", "source_title", "source_years", "source_language",
           "decision", "source_url")
BATCH_SIZE = 12
PER_LANGUAGE = 8


def choose_sample(report: dict, *, per_language: int = PER_LANGUAGE) -> list[dict]:
    if (report.get("schema") != "foundation-v2-language-review-v1"
            or report.get("d1_writes") != 0
            or report.get("publication_performed") is not False
            or report.get("automatic_corrections") != 0
            or not isinstance(report.get("proposals"), list)):
        raise ValueError("Unexpected or mutable prior production review artifact")
    if not 1 <= per_language <= 15:
        raise ValueError("Unsafe sample size")
    rows = defaultdict(list)
    seen = set()
    for candidate in report["proposals"]:
        qid = candidate.get("wikidata_qid")
        if (not isinstance(qid, str) or not QID.fullmatch(qid) or qid in seen
                or candidate.get("source_table") not in ("movies", "catalogue_titles")
                or not candidate.get("source_id")
                or candidate.get("claim_property") != "P364"
                or candidate.get("status") != "REVIEW_REQUIRED"
                or candidate.get("current_language", "").casefold() != "unknown"
                or candidate.get("source_url") != "https://www.wikidata.org/wiki/" + qid):
            raise ValueError("Invalid / duplicate exact-title source proposal")
        seen.add(qid)
        lang = candidate.get("proposed_language")
        if lang in LANGUAGES:
            rows[lang].append(candidate)
    chosen = []
    for lang in LANGUAGES:
        options = rows[lang]
        # Seed independent of input-file order and measured outcomes; sample
        # from different years and avoid selecting only latest acquisitions.
        ordered = sorted(options, key=lambda r: (
            int(r["year"]),
            hashlib.sha256(r["wikidata_qid"].encode("ascii")).hexdigest(),
        ))
        if len(ordered) < per_language:
            raise ValueError(f"Too few eligible {lang} proposal rows")
        for i in range(per_language):
            index = (i * len(ordered) + len(ordered) // 2) // per_language
            chosen.append(dict(ordered[index]))
    if len(chosen) != per_language * len(LANGUAGES):
        raise AssertionError("Sample drift")
    return chosen


def claims_qids(entity: dict, prop: str) -> set[str]:
    values = set()
    for claim in (entity.get("claims") or {}).get(prop) or []:
        if not isinstance(claim, dict) or claim.get("rank") == "deprecated":
            continue
        snak = claim.get("mainsnak") or {}
        if snak.get("snaktype") != "value":
            continue
        data = (snak.get("datavalue") or {}).get("value")
        qid = data.get("id") if isinstance(data, dict) else None
        if isinstance(qid, str) and QID.fullmatch(qid):
            values.add(qid)
    return values


def claim_years(entity: dict) -> set[int]:
    years = set()
    for claim in (entity.get("claims") or {}).get("P577") or []:
        if not isinstance(claim, dict) or claim.get("rank") == "deprecated":
            continue
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if not isinstance(value, dict):
            continue
        match = DATE.match(str(value.get("time") or ""))
        if match:
            years.add(int(match.group(1)))
    return years


def names(entity: dict) -> set[str]:
    labels = entity.get("labels") or {}
    aliases = entity.get("aliases") or {}
    values = [x.get("value") for x in labels.values() if isinstance(x, dict)]
    for group in aliases.values():
        if isinstance(group, list):
            values.extend(x.get("value") for x in group if isinstance(x, dict))
    return {norm(v) for v in values if isinstance(v, str) and v.strip()}


def recheck_item(row: dict, entity: dict | None, language_labels: dict[str,str]) -> dict:
    qid = row["wikidata_qid"]
    source_title = ((entity or {}).get("labels") or {}).get("en") or {}
    result = {**row,
              "source_title": source_title.get("value", ""),
              "language_qid": "", "source_years": "",
              "source_language": "", "decision": "",
              "review_only": True, "production_written": False}
    if not isinstance(entity, dict) or entity.get("id") != qid or entity.get("missing"):
        result["decision"] = "HOLD_IDENTITY_MISSING_OR_REDIRECTED"
        return result
    if norm(row["title"]) not in names(entity):
        result["decision"] = "HOLD_CURRENT_SOURCE_TITLE_MISMATCH"
        return result
    classes = claims_qids(entity, "P31")
    if FILM_QID not in classes:
        result["decision"] = "HOLD_NOT_EXPLICIT_FILM_CLASS"
        return result
    years = claim_years(entity)
    result["source_years"] = ",".join(map(str, sorted(years)))
    if not years or int(row["year"]) not in years:
        result["decision"] = "HOLD_CURRENT_SOURCE_RELEASE_YEAR"
        return result
    languages = claims_qids(entity, "P364")
    if len(languages) != 1:
        result["decision"] = "HOLD_MULTILINGUAL_OR_MISSING_P364"
        return result
    language_qid = next(iter(languages))
    result["language_qid"] = language_qid
    label = language_labels.get(language_qid, "")
    result["source_language"] = label
    if not known(label) or norm(label) != norm(row["proposed_language"]):
        result["decision"] = "HOLD_CURRENT_SOURCE_LANGUAGE_MISMATCH"
        return result
    result["decision"] = "SOURCE_RECHECK_PASSED_REVIEW_REQUIRED"
    return result


def fetch_entities(qids: list[str], *, request=paced_fetch) -> tuple[dict, list]:
    by_qid = {}
    errors = []
    for start in range(0, len(qids), BATCH_SIZE):
        batch = qids[start:start + BATCH_SIZE]
        try:
            payload = request("https://www.wikidata.org/w/api.php", {
                "action":"wbgetentities", "ids":"|".join(batch),
                "props":"claims|labels|aliases", "languages":"en|hi|ta|te|ml|kn|bn|or|mr|pa|gu",
                "format":"json", "formatversion":"2", "maxlag":"5"
            })
            received = payload.get("entities") or {}
            if not isinstance(received, dict):
                raise ValueError("Malformed Wikimedia entities response")
            for qid in batch:
                entity = received.get(qid)
                if isinstance(entity, dict):
                    by_qid[qid] = entity
        except (ValueError, OSError, TimeoutError) as exc:
            errors.append({"qids": batch, "error_type": type(exc).__name__})
    return by_qid, errors


def recheck(report: dict, *, per_language=PER_LANGUAGE, get_entities=fetch_entities) -> dict:
    sample = choose_sample(report, per_language=per_language)
    entities, errors = get_entities([r["wikidata_qid"] for r in sample])
    language_qids = sorted(set().union(*(claims_qids(e, "P364") for e in entities.values())))
    lang_entities, lang_errors = get_entities(language_qids) if language_qids else ({}, [])
    labels = {}
    for qid, entity in lang_entities.items():
        en = (entity.get("labels") or {}).get("en") or {}
        if isinstance(en.get("value"), str):
            labels[qid] = en["value"].strip()
    checked = []
    errored = {q for event in errors for q in event["qids"]}
    lang_errored = {q for event in lang_errors for q in event["qids"]}
    for row in sample:
        item = recheck_item(row, entities.get(row["wikidata_qid"]), labels)
        if row["wikidata_qid"] in errored:
            item["decision"] = "SOURCE_UNAVAILABLE"
        elif item["language_qid"] in lang_errored:
            item["decision"] = "SOURCE_LANGUAGE_UNAVAILABLE"
        checked.append(item)
    counts = Counter(r["decision"] for r in checked)
    by_language = {
        l: dict(Counter(x["decision"] for x in checked if x["proposed_language"] == l))
        for l in LANGUAGES
    }
    return {
        "schema":"data-foundation-v2-live-p364-sample-v1",
        "sample_policy":f"{per_language} deterministic year-stratified films for each of 10 languages",
        "population_proposals":len(report["proposals"]),
        "sample_count":len(checked),
        "sample_languages":list(LANGUAGES),
        "decisions":dict(sorted(counts.items())),
        "by_language":by_language,
        "source_error_batches":len(errors)+len(lang_errors),
        "source_error_details":errors+lang_errors,
        "review_queue":checked,
        "no_database_access":True, "d1_reads":0, "d1_writes":0,
        "sql_generated":False, "automatically_approved":0,
        "warning":"Live Wikidata evidence corroboration is not studio/official-film verification or approval to write D1.",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("input","out","csv"):
        p.add_argument("--"+name,required=True,type=Path)
    args=p.parse_args()
    raw=json.loads(args.input.read_text(encoding="utf-8"))
    result=recheck(raw)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with args.csv.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS,extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["review_queue"])
    print("DATA_FOUNDATION_LIVE_P364_SAMPLE="+json.dumps({
        "population":result["population_proposals"],"sample":result["sample_count"],
        "decisions":result["decisions"],"source_error_batches":result["source_error_batches"],
        "d1_reads":0,"d1_writes":0,
    },sort_keys=True),flush=True)


if __name__=="__main__":
    main()
