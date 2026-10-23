#!/usr/bin/env python3
"""Owner-side AES-GCM recovery verification, strictly offline.

Read an encrypted GitHub Actions artifact with an owner-held 32-byte secret,
verify its authenticated contents and fingerprint. Never contacts Cloudflare,
generates SQL, exposes rows in logs or commits anything to Git.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD=b"cinema-and-series/data-foundation-v2/full-bulk-recovery-v1"


def verify_capsule(envelope:dict,key:bytes)->dict:
    if envelope.get("schema")!="foundation-v2-bulk-aes256gcm-capsule-v1" or \
       envelope.get("algorithm")!="AES-256-GCM" or len(key)!=32:
        raise ValueError("Invalid backup envelope/key")
    nonce=base64.b64decode(envelope["nonce_base64"],validate=True)
    ciphertext=base64.b64decode(envelope["ciphertext_base64"],validate=True)
    plaintext=AESGCM(key).decrypt(nonce,ciphertext,AAD)
    if hashlib.sha256(plaintext).hexdigest()!=envelope["plaintext_sha256"]:
        raise ValueError("Recovery snapshot fingerprint mismatch")
    report=json.loads(plaintext)
    if report.get("schema")!="foundation-v2-full-row-recovery-v1" or \
       report.get("production_database")!="cinema-and-series" or \
       report.get("production_writes")!=0 or report.get("ready_to_apply") is not False or \
       len(report.get("full_rows",[]))!=envelope["full_rows"]:
        raise ValueError("Invalid backup rows/production identity")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("encrypted_json",type=Path)
    p.add_argument("--export-plaintext",type=Path,help="Explicit LOCAL recovery export; store securely and promptly destroy")
    args=p.parse_args()
    val=os.environ.get("FOUNDATION_BACKUP_KEY_B64","")
    if not val:
        raise SystemExit("Owner-held backup key is required")
    try:
        key=base64.b64decode(val,validate=True)
    except Exception as exc:
        raise SystemExit("Invalid base64 backup key") from exc
    report=verify_capsule(json.loads(args.encrypted_json.read_text(encoding="utf-8")),key)
    if args.export_plaintext is not None:
        path=args.export_plaintext
        if path.exists():
            raise SystemExit("Refusing to overwrite local plaintext recovery file")
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        try: os.chmod(path,0o600)
        except OSError: pass
    print(json.dumps({"encrypted_backup_valid":True,
                      "full_existing_rows":len(report["full_rows"]),
                      "drift_holds":len(report["drift_issues"]),
                      "bookmark_present":bool(report.get("bookmark")),
                      "production_writes":0}))


if __name__=="__main__":
    main()
