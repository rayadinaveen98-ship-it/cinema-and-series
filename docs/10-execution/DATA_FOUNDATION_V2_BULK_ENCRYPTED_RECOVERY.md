# Data Foundation V2 — encrypted recovery for the 16,681-title queue

## Why this exists

The old read-only approval workflow checked just **20 films**. The verified
source-only bulk reconciliation now covers **11,667 existing film** and
**5,014 existing series** language proposals. Their Wikidata P364 assertions
are source evidence, **not official producer certification** and **not
authorization** to make production changes.

Workflow: `.github/workflows/foundation-bulk-sealed-backup.yml`.
No SQL updates, migrations, imports, posters, or UI changes.

## Owner-controlled encryption key

Use **a fresh private random 32-byte key encoded as base64**, set in the
repository's GitHub Actions secret `FOUNDATION_BACKUP_KEY_B64`.
The owner must retain a separate copy (e.g. encrypted password manager).

**Never use any key that has appeared in chat, a screenshot, a Git commit,
a PR comment or CI logs.** The workflow refuses fingerprints of both earlier
chat-disclosed example keys. It rejects missing, invalid, or disclosed keys
*before any production database query*.

On a trusted Windows computer, PowerShell can create a private key:

```powershell
$bytes = [byte[]]::new(32)
[Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes)
```

Put the result in **GitHub Settings → Secrets and variables → Actions**;
do not place the plaintext key into version control or send it in chat.

## What the backup workflow actually does

1. Fail closed if the encryption secret is missing/disclosed/invalid.
2. Retrieve the *previously reviewed* exact 11,667-film and 5,014-series
   evidence manifests from GitHub Actions artifacts.
3. Generate bounded **SELECT-only** groups of at most 400 original Wikidata
   IDs; query only these existing production identities, not all 70,175 titles.
4. Recheck exact ID/title, original year, current Unknown language and empty
   language provenance; mismatches go to an **exception list**, never to a
   correction operation.
5. Read a Cloudflare Time Travel bookmark without restoring the database.
6. Encrypt every matching complete row, proposed language, its source
   reference and the bookmark using **AES-256-GCM**, and immediately test
   authenticated decryption in the same runner.
7. Upload only `approval-summary.json` and `encrypted-recovery.json`
   (ciphertext). Raw D1 SELECT responses and the bookmark never become
   artifacts or commits.

The **single ZIP artifact expires after 30 days**. Save a backup copy
outside GitHub under owner control along with its matching secret.
Cloudflare Time Travel bookmarks are not a substitute for a recovered row-level
backup, and a snapshot becomes stale when production changes.

For a private local integrity check after downloading the artifact:

```bash
python scripts/foundation_verify_bulk_sealed_backup.py encrypted-recovery.json
```

Set the owner-held key privately in your local environment before running.
The command prints counts only and does not export plaintext unless
`--export-plaintext` is explicitly supplied.

## Gates that remain after the backup

- Owner independently proves the ciphertext can be decrypted with the retained
  secret on a **different machine / environment**, not only in GitHub.
- Full row/identity checks and a new bookmark are repeated **immediately**
  before any future production correction.
- Production updates require a **separate explicit owner approval** for the
  exact guarded batch. Prior `continue` or `done bro` messages permit
  preparatory engineering only.
- Partial match, known language, or ambiguous language QIDs are held.
- No release year, title, poster, new title, or series lifecycle change in
  these language-only batches.
- Preserve active Data Foundation V2 ingestion/poster freeze.

This workflow is a **recovery prerequisite**, not a write workflow.
