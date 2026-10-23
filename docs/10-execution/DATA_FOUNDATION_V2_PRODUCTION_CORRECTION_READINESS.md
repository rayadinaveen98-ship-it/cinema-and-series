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


## Remote D1 account preflight (read-only staging admission gate)

Before allowing even a small remote disposable D1 rehearsal:

1. Verify the production catalogue freeze is still active at **70,175**.
2. List D1 account database identities (control plane only), prove exactly one
   `cinema-and-series` production identity, and reject duplicate names/UUIDs
   or orphaned `foundation-v2-qa-` databases.
3. Reserve **two Free-plan database slots** (require no more than 8 existing
   databases before attempting scratch creation).
4. Read account-wide, UTC-calendar-day D1 GraphQL `rowsRead` and
   `rowsWritten` analytics. Fail closed on missing permissions, malformed
   values, a truncated result or ambiguous account identity. Assume Free-plan
   limits conservatively: 5,000,000 read rows/day and 100,000 written
   rows/day, across **all** databases in the account.
5. A small canary requires **at least 1,000,000 estimated read and 40,000
   estimated write rows** of headroom at the time of the check. This is a
   precautionary reserve, **not an estimate of canary cost**. A zero-group or
   unavailable metrics response must not be interpreted as zero usage.
6. Never treat GraphQL's sampled/delayed analytics as a guaranteed
   real-time allowance. Before a *manual* staging action the owner must
   independently check the dashboard's account billable usage, existing
   traffic and daily reset timing.
7. Do **not** extrapolate small canary success into authorization for the
   full 16,681-row workload. Index maintenance and schema operations can
   multiply metered writes; remote full-size staging remains a separate gate.

Implementation:
- `scripts/foundation_remote_account_preflight.py` uses only
  `wrangler d1 list --json` and read-only Cloudflare GraphQL analytics;
  never runs SQL or creates/modifies a database.
- `.github/workflows/foundation-d1-account-readonly-preflight.yml`
  runs after an approved main-branch merge and may be dispatched manually.
  Its cloud credentials are restricted to the single read-only step;
  its artifact contains safe aggregate counts only.
- `.github/workflows/foundation-d1-account-preflight-offline-qa.yml`
  validates safety logic on branches/PRs **without credentials**.
- `.github/workflows/foundation-remote-staging-d1.yml` is changed
  from push-triggered to **manual dispatch only**, checks the account gate
  before disposable staging, and scopes credentials to the stages that need
  them and the always-run exact-UUID cleanup step.

**No remote staging dispatch and no production data writes are authorized by
merging these protections.** The post-merge read-only preflight determines
whether the account's control-plane and metrics checks are functioning, not
whether full-size staging or production mutation can proceed.

Cloudflare reference:
- https://developers.cloudflare.com/d1/platform/limits/
- https://developers.cloudflare.com/d1/platform/pricing/
- https://developers.cloudflare.com/d1/observability/metrics-analytics/


## Actual Worker-binding remote D1 canary preparation — 23 Oct 2026

The original disposable 17-film remote Wrangler test uses SQL files. Even when
that experiment succeeds, it must NOT be presented as proof of transactional
behavior for the real Worker D1 `db.batch()` executor.

A distinct, safer, **manual-dispatch-only** end-to-end path is now prepared:

- `scripts/foundation_staging_worker_probe.mjs` uses the **actual guarded
  `applyApprovedBatch()` and `applyApprovedInverseBatch()` functions** through
  a D1 Worker Binding, with only synthetic **3 film + 3 series** candidates and
  an untouched control record in each table. It checks full-row inverse, a
  stale-last-row abort, a conflicting-edit inverse abort and exact restoration.
- The Worker has **no production entrypoint/deployment**. Its request requires
  a high-entropy ephemeral header token; arbitrary GET/paths cannot execute.
  An exact `foundation-v2-qa-<GitHub run>-<attempt>` staging name and a
  UUID unequal to production are mandatory.
- More importantly, the actual bound D1 database must contain a
  `foundation_v2_stage_proof` record matching the scratch name, UUID and
  ephemeral nonce, **created only on the newly provisioned scratch DB**.
  Environment variables or a misleading Wrangler config are not sufficient.
  No such marker is created in production.
- `scripts/foundation_remote_worker_binding_runner.py` creates a temporary
  database, pins only its verified UUID into a private preview config,
  applies the current film+series migrations, writes the scratch proof, starts
  a **temporary remote development preview** rather than deploying the live
  Worker, calls the canary POST once, stops preview, confirms exact-ID scratch
  deletion, and erases the temporary config containing the ephemeral nonce.
  An uncertain response is never retried.
- `.github/workflows/foundation-remote-worker-binding-canary.yml` runs
  **only when explicitly dispatched with YES_SCRATCH_D1_ONLY** and only after
  fresh account-wide read/write quota preflight. CI has a second always-run
  scratch-cleanup step. Its artifacts contain non-sensitive counts and pass
  flags, never database records, keys, UUIDs or access tokens.
- The Worker and Python runner have independent credential-free local tests.

**Current status:** code and local tests prepared; do NOT call this remote
canary completed until the explicit manual GitHub Actions run succeeds. It
still does **not** validate all 16,681 rows against remote Cloudflare D1,
retention of an owner-accessible backup, production row freshness, independent
studio confirmation, or owner-approved production changes. No production write
workflow has been enabled. The 70,175-title freeze remains.

### Operational caution

Cloudflare remote development previews are temporary infrastructure on
Cloudflare's network. The test code must never be redeployed as the production
Worker or bound to `cinema-and-series`. Unexpected behaviour should trigger
cleanup and stop, not automatic retries or broadened credentials.

References:
- https://developers.cloudflare.com/d1/worker-api/d1-database/
- https://developers.cloudflare.com/workers/local-development/


## Free-plan per-invocation safety refinement (23 Oct 2026)

The synthetic scratch Worker canary originally performed all tests in a
single HTTP invocation. Cloudflare Workers Free restricts requests to
**50 D1 queries/subrequests per Worker invocation**, so that design had
an avoidable resource-limit risk even with only eight QA identities.

The nonproduction canary now uses **six separate, one-time HTTP requests**,
in this exact order: `seed`, `film`, `series`, `stale`, `conflict`,
`finish`. Every request:

- Authenticates the exact ephemeral header nonce.
- Verifies the database-resident proof of scratch name, UUID and nonce
  **before** any writes.
- Confirms a persisted `stage_phase` matches the *immediately previous*
  phase. Skipped, repeated, malformed or uncertain requests fail closed.
- Runs only a bounded subset of the synthetic forward/inverse/conflict cases,
  then advances the scratch phase checkpoint once.
- Does not retry an indeterminate request; any failure triggers
  exact-UUID scratch cleanup (not continuation).

The `finish` phase verifies the eight original scratch records and
language/source fields are restored, and returns only pass/fail flags.
`foundation_remote_worker_binding_runner.py` verifies the response of
**each** of the six requests. The step remains manual-only and never
operates on production. No remote pass is claimed until the manual
Cloudflare action actually runs successfully.

This refinement does not establish a safe real-production batch size.
A full 100-row batch emits 200 SQL statements and must be separately
proven against the plan's current query/subrequest, parameter and
D1 execution limits before production is even considered.

Official limits: https://developers.cloudflare.com/d1/platform/limits/


## Remote Worker D1 canary failure and scratch schema optimization — 23 October 2026

The owner dispatched scratch-only Worker Binding canary
[run 39954207551](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39954207551).
**21 Python safety tests, six local Worker Binding tests and Cloudflare D1
account read-only quota preflight PASSED**. The separate remote test failed,
and the unconditional cleanup action reported
`FOUNDATION_STAGING_CLEANUP=verified_absent`. Because the cleanup found a
recorded scratch identity, the disposable D1 had actually been provisioned;
no production correction was authorized or executed.

The exact failing remote substep was not observable because this run preceded
categorical stage diagnostics from PR #214. Do not claim schema setup was
proven to cause the failure.

The local code identified a reliability/performance concern: the scratch
schema loader spawned one remote Wrangler process per individual statement
across five trusted film/series migrations. It is now configured to:

- Parse and allowlist all trusted `CREATE`, `ALTER` and one fixed
  `UPDATE series_titles` migration statement.
- Validate the exact scratch naming convention plus the private Wrangler
  binding's scratch UUID versus production UUID **before issuing any SQL**.
- Write the fixed schema SQL to one temporary runner-local file, invoke
  `wrangler d1 execute --remote --file ...` **once**, then always remove
  the temporary schema file, including after a failed remote command.
- Keep scratch-only UUID and database-resident nonce controls, automatic
  exact cleanup and the frozen 70,175-title catalogue unchanged.
- Record a fixed `probe_seed`, `probe_film`, `probe_series`,
  `probe_stale`, `probe_conflict`, or `probe_finish` diagnostic if a
  phase fails, with no raw Cloudflare/network exception contents.

These are **preventive improvements**, not evidence of remote success.
A new manually dispatched test, not a retry of a stale failed job, is
needed to verify real Cloudflare D1 behavior. If it fails again, use the
safe diagnostic artifact and `FOUNDATION_REMOTE_CANARY_STAGE` markers to
locate the failing step before changing any further code.


## Third remote Worker canary result — preview startup blocker

The next manually requested scratch-only remote Worker canary
[run 39963004524](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39963004524)
failed after **all five trusted schema files and the database-resident scratch
identity proof succeeded**. The last safe diagnostic marker was
`preview_start`; **no synthetic Worker data phase was reached**.
The unconditional cleanup confirmed the scratch D1 was absent. This does
not prove any problem with the full correction executor.

Cloudflare's current configuration docs explain that Preview URLs default
to the `workers_dev` value when no explicit setting exists, and we had
`workers_dev=false` with no explicit Preview URL setting. This is a
credible **configuration hypothesis**, not an independently proven root
cause. To test safely without deploying the application:

- Keep `workers_dev=false` and add `preview_urls=true` **only to the
  temporary scratch Worker configuration**.
- Require an authenticated, **read-only** GET to the dedicated
  `/__foundation_staging_probe_health` path to prove that the actual bound
  remote D1 contains the expected scratch name, UUID and ephemeral nonce
  with `stage_phase=new`.
- Disallow the earlier generic 404 readiness shortcut: an HTTP 404 could
  come from an unrelated localhost/gateway handler, not from our Worker.
- Keep phase execution on six one-time POST requests only AFTER positive
  scratch-binding health, and preserve exact UUID deletion and
  never-retry-on-uncertainty behavior.

No remote success can be claimed until a new manually dispatched run proves
the bounded forward/rollback cases and scratch cleanup. The production
catalogue remains frozen at **70,175** titles.

Documentation:
https://developers.cloudflare.com/workers/wrangler/configuration/
https://developers.cloudflare.com/workers/local-development/
