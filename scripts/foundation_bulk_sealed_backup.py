#!/usr/bin/env python3
"""Safely seal CURRENT full D1 rows for the complete film+series P364 queue.

Source-only film and series artifacts are immutable inputs. This module never
executes SQL and never authorizes writes. It refuses keys already shown in chat,
snapshots only exact matches to the latest production rows, and encrypts the
whole recovery payload before any artifact upload.

Modes:
  check-key : validate a private AES-256 key (NO database requests)
  seal      : read 2 saved D1 SELECT responses, cross-check identities, seal
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_catalogue_quality import load_d1_rows, norm
from foundation_final_prewrite import read_bookmark

QID = re.compile(r"Q[1-9][0-9]*\Z")
REVOKED_KEY_FINGERPRINTS = frozenset({"fe78ca718b8e68951767f23d1d4b3cfddd5100f2c30b9cb56ccbde8731eb795f", "3c3b59bae62877ece9f1a0f12ba617d08260a9723fb3166fdba52a7a506f4da1"})
AAD = b"cinema-and-series/data-foundation-v2/full-bulk-recovery-v1"
UNKNOWN = {"", "unknown", "xx", "und", "n/a", "na", "none", "null"}
DISPUTED = {"Q20967570", "Q20649744", "Q109519684"}


def check_key(value: str) -> bytes:
    if not value:
        raise ValueError("FOUNDATION_BACKUP_KEY_B64 is missing; no backup attempted")
    try:
        key = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("Backup key must be valid base64") from exc
    if len(key) != 32:
        raise ValueError("Backup key must contain exactly 32 random bytes")
    if hashlib.sha256(key).hexdigest() in REVOKED_KEY_FINGERPRINTS:
        raise ValueError("Backup key was previously disclosed in chat. Replace GitHub secret with a fresh PRIVATE key.")
    return key


def checked_manifest(film: dict, series: dict) -> tuple[list[dict], list[dict]]:
    if film.get("schema") != "foundation-v2-bulk-existing-films-v1" or \
       film.get("writes_authorized") is not False or film.get("d1_writes") != 0:
        raise ValueError("Unexpected or writable film evidence package")
    if series.get("schema") != "foundation-v2-bulk-existing-series-v1" or \
       series.get("writes_authorized") is not False or series.get("d1_writes") != 0:
        raise ValueError("Unexpected or writable series evidence package")
    if film.get("frozen_catalogue_movies") != 51872 or \
       series.get("total_existing_series") != 18303:
        raise ValueError("Catalogue baseline drift")
    fs = film.get("records")
    ss = series.get("records")
    if not isinstance(fs,list) or len(fs)!=film.get("correction_candidates") or \
       not isinstance(ss,list) or len(ss)!=series.get("language_candidates"):
        raise ValueError("Unreconciled language-correction record count")
    if len(fs)<1000 or len(ss)<1000:
        raise ValueError("Full-bulk source evidence is incomplete")
    all_ids=set()
    for table,items in (("catalogue_titles",fs),("series_titles",ss)):
        for row in items:
            qid=row.get("wikidata_qid")
            if not isinstance(qid,str) or not QID.fullmatch(qid) or \
               qid in DISPUTED or (table,qid) in all_ids:
                raise ValueError("Duplicate/disputed/invalid evidence QID")
            all_ids.add((table,qid))
            if table=="catalogue_titles":
                if row.get("source_table")!="catalogue_titles" or \
                   row.get("claim_property")!="P364" or \
                   row.get("review_status")!="SOURCE_MATCH_ONLY_NOT_PRODUCTION_APPROVED":
                    raise ValueError("Unsafe film evidence")
            else:
                if row.get("source")!="wikidata:P364" or \
                   row.get("review_status")!="SOURCE_P364_ONLY_NOT_APPROVED":
                    raise ValueError("Unsafe series evidence")
            if row.get("source_url",row.get("language_source_url"))!="https://www.wikidata.org/wiki/"+qid:
                raise ValueError("Unverifiable source URL")
    return fs,ss


def parse_rows(file: Path,table: str) -> dict[str,dict]:
    raw=load_d1_rows(file)
    index={}
    for row in raw:
        qid=row.get("wikidata_qid")
        if isinstance(qid,str) and QID.fullmatch(qid):
            if qid in index:
                raise ValueError("Duplicate current production "+table+" QID")
            index[qid]=row
    return index


def collect_matches(films:list[dict],shows:list[dict],film_current:dict,series_current:dict):
    matched=[];issues=[]
    for table, proposals,current in (
        ("catalogue_titles", films,film_current),
        ("series_titles",shows,series_current),
    ):
        for item in proposals:
            qid=item["wikidata_qid"]; row=current.get(qid)
            expected_id=item["source_id"] if table=="catalogue_titles" else item["id"]
            if row is None:
                reason="missing_current_or_known_language"
            elif str(row.get("id"))!=expected_id or row.get("title")!=item["title"]:
                reason="identity_changed"
            elif norm(row.get("language_name")) not in UNKNOWN:
                reason="language_already_known"
            elif norm(row.get("language_source")) not in UNKNOWN or \
                 norm(row.get("language_source_url")) not in UNKNOWN:
                reason="existing_language_provenance"
            elif table=="catalogue_titles" and (
                  row.get("release_year")!=item["year"] or row.get("country_code")!="IN"):
                reason="film_release_year_or_country_changed"
            elif table=="series_titles" and row.get("first_air_year")!=item["first_air_year"]:
                reason="series_first_air_year_changed"
            else:
                reason=None
            if reason is None:
                matched.append({"table":table,"row":row,
                                "proposed_language":item["proposed_language"],
                                "evidence_url":item["source_url"],
                                "qid":qid})
            else:
                issues.append({"table":table,"qid":qid,"reason":reason})
    if len(matched)+len(issues)!=len(films)+len(shows):
        raise AssertionError("Candidates omitted during current-row preflight")
    return matched,issues


def make_capsule(film:dict,series:dict,film_current:dict,series_current:dict,
                 *,key:bytes,bookmark:str|None,bookmark_status:str):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    fs,ss=checked_manifest(film,series)
    matched,issues=collect_matches(fs,ss,film_current,series_current)
    counts=dict(Counter(x["table"] for x in matched))
    summary={
        "schema":"foundation-v2-bulk-sealed-backup-summary-v1",
        "frozen_baseline":70175,"film_source_candidates":len(fs),
        "series_source_candidates":len(ss),"total_source_candidates":len(fs)+len(ss),
        "full_production_rows_backed_up":len(matched),
        "backed_up_by_table":counts,"held_on_fresh_live_check":len(issues),
        "issue_counts":dict(Counter(x["reason"] for x in issues)),
        "held_qids":issues[:1000],
        "bookmark_status":bookmark_status,
        "bookmark_sha256":hashlib.sha256(bookmark.encode()).hexdigest() if bookmark else None,
        "bookmark_raw_public":False,
        "encrypted_backup_created":True,
        "disclosed_key_fingerprint_rejected":True,
        "writes_authorized":False,"production_writes":0,
        "next_gate":"Test owner-held decrypt key; perform FRESH prewrite queries and approval. This snapshot will be stale later.",
    }
    plain={
        "schema":"foundation-v2-full-row-recovery-v1","captured_at":datetime.now(timezone.utc).isoformat(),
        "production_database":"cinema-and-series","full_rows":matched,
        "drift_issues":issues,"bookmark":bookmark,
        "bookmark_status":bookmark_status,
        "film_review_sha256":film.get("records_sha256"),
        "series_review_sha256":series.get("records_sha256"),
        "production_writes":0,"ready_to_apply":False,
    }
    value=json.dumps(plain,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    nonce=os.urandom(12)
    ciphertext=AESGCM(key).encrypt(nonce,value,AAD)
    verified=AESGCM(key).decrypt(nonce,ciphertext,AAD)
    if verified!=value:
        raise AssertionError("Encrypted full-row recovery failed local verification")
    sealed={
        "schema":"foundation-v2-bulk-aes256gcm-capsule-v1",
        "algorithm":"AES-256-GCM","key_ref":"GitHub secret FOUNDATION_BACKUP_KEY_B64",
        "aad":"cinema-and-series/data-foundation-v2/full-bulk-recovery-v1",
        "nonce_base64":base64.b64encode(nonce).decode(),
        "ciphertext_base64":base64.b64encode(ciphertext).decode(),
        "plaintext_sha256":hashlib.sha256(value).hexdigest(),
        "full_rows":len(matched),
    }
    return summary,sealed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("check-key","seal"))
    for name in ("films","series","current-films","current-series","summary","sealed"):
        p.add_argument("--"+name,type=Path)
    args=p.parse_args()
    key=check_key(os.environ.get("FOUNDATION_BACKUP_KEY_B64",""))
    if args.mode=="check-key":
        print("FOUNDATION_BACKUP_KEY_CHECK=present_valid_32_byte_private_not_chat_disclosed")
        return
    if any(getattr(args,n.replace("-","_")) is None for n in (
        "films","series","current-films","current-series","summary","sealed")):
        raise ValueError("All manifest, current D1 and output paths are required")
    film=json.loads(args.films.read_text(encoding="utf-8"))
    shows=json.loads(args.series.read_text(encoding="utf-8"))
    current_films=parse_rows(args.current_films,"catalogue_titles")
    current_series=parse_rows(args.current_series,"series_titles")
    bookmark,status=read_bookmark()
    summary,sealed=make_capsule(film,shows,current_films,current_series,
                                key=key,bookmark=bookmark,bookmark_status=status)
    args.summary.parent.mkdir(parents=True,exist_ok=True)
    args.sealed.parent.mkdir(parents=True,exist_ok=True)
    args.summary.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    args.sealed.write_text(json.dumps(sealed,indent=2)+"\n",encoding="utf-8")
    print("FOUNDATION_BULK_BACKUP="+json.dumps({
        "candidates":summary["total_source_candidates"],
        "backed_up":summary["full_production_rows_backed_up"],
        "held":summary["held_on_fresh_live_check"],
        "bookmark_status":status,"production_writes":0,"writes_authorized":False},sort_keys=True))


if __name__=="__main__":
    main()
