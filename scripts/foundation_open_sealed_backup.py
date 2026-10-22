#!/usr/bin/env python3
"""Open a Data Foundation V2 AES-256-GCM recovery capsule on an owner's local machine.

This utility NEVER connects to Cloudflare or generates UPDATE/RESTORE commands.
Only prints a minimal verification summary. Explicit --out-json creates a
plaintext local copy; safeguard and promptly delete it after an approved use.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def open_backup(sealed: dict, key_b64: str) -> dict:
    if sealed.get("schema") != "foundation-v2-encrypted-backup-v1":
        raise ValueError("Invalid recovery envelope schema")
    key = base64.b64decode(key_b64, validate=True)
    if len(key) != 32:
        raise ValueError("FOUNDATION_BACKUP_KEY_B64 must decode to 32 bytes")
    nonce = base64.b64decode(sealed["nonce_base64"], validate=True)
    ciphertext = base64.b64decode(sealed["ciphertext_base64"], validate=True)
    plaintext = AESGCM(key).decrypt(
        nonce, ciphertext, b"cinema-and-series/data-foundation-v2/recovery-only"
    )
    data = json.loads(plaintext)
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != sealed["plaintext_sha256"]:
        raise ValueError("Backup fingerprint validation failed")
    if (data.get("schema") != "foundation-v2-sealed-recovery-payload-v1"
            or data.get("production_db") != "cinema-and-series"
            or len(data.get("rows", [])) != 20
            or data.get("reviewed_count") != 17
            or data.get("held_count") != 3):
        raise ValueError("Unexpected backup identity or row count")
    return data


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sealed_json", type=Path)
    p.add_argument("--out-json", type=Path, help="Create LOCAL plaintext file explicitly")
    args = p.parse_args()
    key = os.environ.get("FOUNDATION_BACKUP_KEY_B64", "")
    if not key:
        raise SystemExit("Missing owner-held FOUNDATION_BACKUP_KEY_B64")
    restored = open_backup(json.loads(args.sealed_json.read_text(encoding="utf-8")), key)
    if args.out_json is not None:
        if args.out_json.exists():
            raise SystemExit("Refusing to overwrite an existing plaintext file")
        args.out_json.write_text(
            json.dumps(restored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            os.chmod(args.out_json, 0o600)
        except OSError:
            pass
    print(json.dumps({
        "authenticated_backup_verified": True,
        "rows": len(restored["rows"]),
        "reviewed": restored["reviewed_count"],
        "held": restored["held_count"],
        "bookmark_present": bool(restored["bookmark"]),
        "production_writes": 0,
    }))


if __name__ == "__main__":
    main()
