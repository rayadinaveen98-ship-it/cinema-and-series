# Data Foundation V2 — 17-film final safety/approval package

## Non-negotiable state

The 70,175-title production catalogue is frozen while we strengthen existing
records. The 17 language corrections in the verified 20-film pilot are NOT
approved for production. Three films remain held (Asurakulam, Saadey CM Saab,
Mr. Romeo). No new film imports, poster work or UI changes may resume.

The 22 October 2026 remote staging trial passed: run 39804042061 used one
isolated, temporary D1 database, tested 17 guarded updates + rollback and
three held records, and verified that the staging database was removed.

## This read-only prewrite report

The one-time workflow `.github/workflows/foundation-final-prewrite.yml`:

1. Downloads immutable 20-record proposal and the 17/3 external-evidence review.
2. Asserts the freeze marker is active and builds a narrow SQL **SELECT** from
   exactly the approved 20 existing QIDs.
3. Queries **full columns** of those 20 current `catalogue_titles` rows.
4. Rejects changed IDs, titles, release years, countries, previous languages,
   missing/duplicate records or a discrepancy in the 17/3 reviewer decisions.
5. Retrieves a **read-only current Cloudflare D1 Time Travel bookmark** from
   the officially documented API if available, without restoring the DB.
6. Writes a public-safe JSON approval manifest of current full-row fingerprints,
   proposed languages, evidence status, and the held-record list.
7. **Only when** a repository secret `FOUNDATION_BACKUP_KEY_B64` is configured,
   encrypts the complete 20 full-column rows and raw bookmark in AES-256-GCM,
   decrypts internally to verify integrity, and uploads the encrypted file.

No raw row snapshot, bookmark, bearer token or backup encryption key is logged,
committed to Git, or included in an unencrypted GitHub Actions artifact.
The GitHub run always reports `write_approved=false`, `ready_to_write=false`,
`production_writes=0`.

## Required owner-managed backup key

To retain an encrypted backup, the owner must create a fresh **32-byte random
key**, base64 encoded, and set it as the GitHub repository Actions secret
`FOUNDATION_BACKUP_KEY_B64`. Example generation on a private computer:

```python
import base64, secrets
print(base64.b64encode(secrets.token_bytes(32)).decode("ascii"))
```

On GitHub: Repository Settings → Secrets and variables → Actions → New repository
secret. Do not commit the key, send it in a chat, or share it in a PR. Store an
additional copy in an owner-controlled password manager or secure key vault.
**Losing the key makes the encrypted backup unrecoverable.** Rotating the key
without retaining the old value prevents recovery of older snapshots.

The prewrite workflow still completes a safe read-only review when this secret
is absent; its report will say `blocked_missing_foundation_backup_key`, and
**no raw or recoverable row backup** will be published. This outcome does not
clear the backup approval gate.

The owner can test decryption locally with
`python scripts/foundation_open_sealed_backup.py sealed-recovery.json`,
setting `FOUNDATION_BACKUP_KEY_B64` privately. To obtain a temporary plaintext
copy, add `--out-json private-recovery.json`; safeguard and securely delete
the plaintext afterward.

## Remaining conditions before the 17 production writes

1. A fresh complete encrypted backup must exist, with the matching owner-held
   decryption key independently tested, and a current valid Time Travel
   bookmark captured **immediately before** any write.
2. The user must explicitly approve a reviewed PR listing the exact 17 QIDs,
   before/after languages, external source evidence, and held 3 QIDs. General
   'continue' does **not** authorize writing.
3. Immediately requery each production row and abort all edits on any drift;
   never rely on a hours-old preflight snapshot or bookmark.
4. Only a guarded atomic 17-row transaction may change `language_name`,
   `language_source`, and `language_source_url` in `catalogue_titles`.
   No new titles, release-year updates, poster edits or changes to held films.
5. After write, reconcile 17 row counts and independent API retrieval. Retain
   audit trail, tested row-level inverse and the bookmark. Never automatically
   invoke whole-database Time Travel restore, which can erase intervening
   unrelated writes.

The snapshot process alone DOES NOT mean the catalogue may be unfrozen.

## References

- https://developers.cloudflare.com/api/resources/d1/subresources/database/subresources/time_travel/methods/get_bookmark/
- https://developers.cloudflare.com/d1/reference/time-travel/
- https://developers.cloudflare.com/d1/wrangler-commands/
