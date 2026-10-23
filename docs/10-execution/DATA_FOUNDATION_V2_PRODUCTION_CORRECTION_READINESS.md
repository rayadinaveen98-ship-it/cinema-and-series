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
