# Data Foundation V2 — guarded production-language correction preparation

**Status: IMPLEMENTED AND TESTED LOCALLY; NOT DEPLOYED; PRODUCTION WRITES DISABLED.**

This package follows the successful read-only recovery of 16,681 real existing
catalogue records, independent AES-256-GCM decryption in a separate CI runner,
and the complete 168-batch SQLite forward/restore rehearsal.

## Exact proposed release

- Existing film records: **11,667** in `catalogue_titles`.
- Existing series records: **5,014** in `series_titles`.
- Total: **16,681** only from explicit original-language Wikidata **P364** claims.
- Atomic group size: **at most 100** existing records; **168 batches**.
- Neither titles, years, dates, thumbnails, series lifecycle nor new records
  are changed.
- Three disputed film IDs remain excluded.
- Claims from Wikidata are traceable community-curated evidence, **not
  producer/studio-certified independent verification**. Owners must accept
  that data-quality standard separately before any production edits.

## Guarded D1 primitive

`scripts/foundation_d1_guarded_executor.mjs` is a **library with no deployed
Worker, HTTP route, cron trigger or access to production D1**. Its
`applyApprovedBatch(db, items, approval)` requires an explicit approval
object containing the exact row batch SHA-256, intended database, owner
approval reference and a separately enabled production switch.

For **every row**, the library uses prepared placeholders to:
1. Check **all original D1 column values**, null-safely, in the intended
   existing table.
2. Abort the transaction via an intentionally failing SQLite JSON function
   if even one row no longer matches.
3. Update only `language_name`, `language_source`,
   `language_source_url`, and `updated_at` on that exact original row.
4. Execute all guards and updates in one D1 Worker Binding `db.batch([...])`.
   Unlike relying on a generic multi-statement `wrangler d1 execute --file`,
   Cloudflare documents `db.batch()` as transactional.
5. Requery each result and validate exact new language + provenance while
   requiring all unrelated columns to remain unchanged. If a network
   response or verification is ambiguous, **never blindly retry**; reconcile
   the current state first.

`applyApprovedInverseBatch(db, originalItems, afterRows, approval)` adds
a second explicit rollback approval. It checks every actual **after-write**
column, atomically restores the four original fields (including the exact
original `updated_at`), then verifies every restored column. A newer edit
blocks the inverse instead of being erased. Time Travel restore of the
**entire** production DB is deliberately not automated.

Tests use Miniflare's isolated D1 Worker Binding and include missing approval,
7-film forward, stale last-row rollback, 6-series forward, full inverse,
and newer third-party edit rejection. Previous full-batch SQLite simulation
recovered all 16,681 rows; the full workload has **not yet been exercised
on a real remote staging D1 at this batch size**.

## Owner approval manifest

`.github/workflows/foundation-d1-owner-manifest.yml` independently
decrypts the existing approved-key recovery capsule **in ephemeral CI only**.
It emits public-safe hashes/counts for all 168 exact batches; no plaintext
database records or key are uploaded. The single top-level manifest SHA-256
and batch SHA-256s identify precisely what would change.

An approval must specify that exact manifest digest, title count and evidence
standard. This repository does **not** consider prior `continue` messages,
PR merges, or setup-key confirmations as data-write authorization.

## Required before activating a production runner

1. Retain an **owner-accessible copy** of the encrypted full-row backup and
   its *matching private key*, outside expiring GitHub Actions artifacts.
2. Test an independent full restoration to **isolated nonproduction** D1
   with film AND series schema, including failure halfway through one
   100-record batch. A 17-film remote staging result alone is insufficient.
3. Obtain explicit owner approval of the final exact 168-batch manifest and
   the source-evidence standard; record it in an owner-controlled issue or PR.
4. Add a **separate protected, manually dispatched production workflow**
   that verifies owner identity and the approval reference from GitHub,
   compares the locked manifest SHA-256, verifies bound production database
   UUID, captures a **new** encrypted row snapshot and recovery bookmark,
   and then uses `applyApprovedBatch()` exclusively.
5. Persist a durable private per-batch committed/verified journal. On a lost
   response, inspect live values before proceeding; do not auto-retry. Audit
   the complete film/series Unknown counts after completion.
6. Keep broader job-level film/series import, artwork, UI and automation freeze
   active until separate sign-off and independent QA.

**There is no reachable production write workflow in this PR.** That is
intentional: owner approval has not yet been obtained.

## Links

- [Original backup](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39935377448)
- [Independent archive validation](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39935974111)
- [16,681-row isolated SQLite rehearsal](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39936937501)
- [Official D1 Database `batch()` documentation](https://developers.cloudflare.com/d1/worker-api/d1-database/)


## Next safety gate: complete local D1-binding rehearsal (proposed)

This gate is deliberately separated from any remotely bound D1 or production
executor. It does not relax the **OWNER APPROVAL REQUIRED** state.

- `scripts/foundation_d1_full_snapshot_rehearsal.mjs` consumes the previously
  authenticated, **privately decrypted** historical backup in isolated Miniflare.
- It seeds the actual film and series migrations with **all 16,681 original rows**
  and one nonmatching untouched sentinel per table.
- It exercises the **same guarded D1 `db.batch()` primitive** across the
  **168 exact manifest-locked batches**, then exercises separately approved
  synthetic inverses and checks complete restoration of every original column.
- It tests an intentionally stale last film record and a competing new edit
  during series rollback. Both must reject the entire batch with no partial
  changes.
- The library now reads `PRAGMA table_info` before forwards **and** inverses,
  rejecting any missing snapshot column or unreviewed live schema drift.
- `.github/workflows/foundation-d1-full-sealed-local-qa.yml` has a main-branch
  / manual trigger and **no Cloudflare credential binding**. It briefly
  decrypts the historical capsule in the runner, wipes plaintext in an exit
  trap, and uploads **only non-sensitive booleans, counts and hashes**.
- The full-size test is **not marked PASSED** until its GitHub Actions run
  concludes successfully. A passing synthetic local run is **not** evidence
  of full-size remote staging, current production-row freshness, data-owner
  authorization, or independent studio confirmation of Wikidata P364.

**Still blocking any production correction:** an owner-held backup/key retained
outside expiring CI artifacts; full remote *disposable* D1 rehearsal, with both
film and series schema and forced halfway failure; an exact approved hash
manifest and evidence standard; a new prewrite snapshot/bookmark; a protected
explicitly dispatched production runner with private persistent journal; and
a post-write independent catalogue audit. Existing title/artwork/ingestion/UI
freeze stays active until a separate authorized decision.


## Verified complete local D1 rehearsal — 23 October 2026

Run [39942616541](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39942616541)
completed **successfully** on main after PR #207. Its guarded
forward updates, complete inverse, stale-last-row abort, competing-edit inverse
abort and upload of non-sensitive QA counts/hashes all passed against the
authenticated, historical **16,681-record / 168-batch** fixture.

The still-frozen **70,175-title live catalogue** was not mutated. The run
was LOCAL Miniflare, not remote Cloudflare D1. Real remote throughput, current
production-row freshness, owner-held backup durability and production
authorization remain unproven.

### Remote deployment limitation found before staging

Cloudflare D1's documented Worker Free limits include **50 queries per Worker
invocation**, **100 bound parameters per query**, a **10-database account
limit**, and **100,000 D1 rows written per day** shared across the account.
A guarded 100-title batch must therefore not issue a separate SELECT for each
title after the write. Even a successful local Miniflare 100-item transaction
does **not** guarantee that a remote Worker invocation can perform 100
sequential verification subrequests.

The guarded executor was optimized so verification uses a **single indexed
`SELECT ... WHERE wikidata_qid IN (100 bound placeholders)`** for each
100-item batch, both forward and inverse. It rejects missing, duplicate or
unexpected identities, compares every original column, and never silently
retries uncertain writes. This preserves all original transaction guards while
reducing remote read round trips. An explicit 100-row Miniflare test verifies
one post-write read per phase and a negative test rejects partial reads.

Before creating any full-size remote disposable D1, check the current
account's remaining D1 row-read/write allowance, database count and
storage, and test a **bounded canary using the same Worker Binding API**.
The expected base rehearsal would write at least **50,043 rows**
(16,681 seed + 16,681 forward + 16,681 inverse), excluding sentinels,
extra negative-case writes, schema writes and any other account activity.
Never equate this arithmetic minimum with actual metered Cloudflare usage.
Cloudflare documents that the Free daily allowance is enforced; risking a
quota stop could disrupt the live application.

Official limits: https://developers.cloudflare.com/d1/platform/limits/
and https://developers.cloudflare.com/d1/platform/pricing/

A complete remote staging test is **still required** and should remain
separate from automatic push and scheduled workflows until explicit
resource/quota checks and cleanup control have passed.


## Backup custody / secrets review — 23 October 2026

The authenticated, **encrypted** 16,681-record historical recovery artifact
from run [39935377448](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39935377448)
is currently retained in GitHub Actions **only until 22 November 2026**.
The owner must privately export it plus the *matching secret key* to a durable
location outside Actions before expiration. Never put the AES key in an
issue, chat, public commit, or attached public documentation. The artifact
is encrypted, but it is still a historical candidate-row recovery snapshot,
not a full backup of the 70,175-title production D1 database.

CI jobs that decrypt the recovery artifact must expose
`FOUNDATION_BACKUP_KEY_B64` only to their specific authenticated decryption /
sealing step, never to `npm install`, `pip install`, checkout, setup or
unrelated tests. The original read-only production bulk backup workflow must
remain **manual-dispatch-only** while the catalogue freeze is active.
Cloudflare account/API credentials are likewise scoped to the read-only
selection or encryption/bookmark steps, not package installation.

None of these safeguards authorize production writes. A fresh full original-row
snapshot and fresh recovery bookmark immediately before any future approved
correction are still mandatory.
