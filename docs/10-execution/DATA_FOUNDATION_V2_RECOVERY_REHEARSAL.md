# Data Foundation V2 — Recovery rehearsal and correction approval gate

## Operating state (22 October 2026)

Catalogue growth, poster, UI and P1 writers remain **frozen** via
`ops/data-foundation-v2-freeze.json`. The existing 20-film batch is not authorized
to change production. Seventeen films have externally corroborated language/year
and matching current values; three are held:

- `Q20967570` — Asurakulam: conflicting 2015, 2017 and TBA release data
- `Q20649744` — Saadey CM Saab: 2015 stored versus 27 May 2016 release
- `Q109519684` — Mr. Romeo: external identity disambiguation remains weak

The evidence and exact source identities are archived in prior read-only runs
39764251711 (20-film packet), 39775564153 (current 20 D1 rows),
39776850310 (external verification).

## This milestone: isolated backup and rollback

`scripts/foundation_filebacked_rollback.py` builds a **disposable file-backed
SQLite database**, populated with the 20 real saved D1 row values plus an
unrelated sentinel. It:

1. Saves an SQLite backup and compares it with every original row.
2. Simulates exactly 17 guarded language changes, while verifying three held
   films and the unrelated row remain untouched.
3. Performs 17 inverse, guard-checked updates and proves the entire table
   returned to the original values.
4. Separately restores the backup into another file and verifies all rows.
5. Injects a stale original in the **last** forward item and verifies all prior
   simulated updates in that transaction were atomically rolled back.
6. Injects a third-party edit before the inverse, and proves the inverse
   refuses to overwrite it.

Each pass is performed on a *temporary database file* on the GitHub Actions
runner. The workflow has no Cloudflare credentials, accesses no live D1, emits
no executable production SQL, and does not re-enable frozen jobs.

**Limits:** This proves guarded row-level update/reverse behavior on SQLite
matching the sampled record columns; it does **not** prove full-table schema,
triggers, FKs, performance, or `wrangler`/D1 restore behavior. The SQLite backup
is not a backup of the entire production catalogue.

## Next gate: disposable Miniflare local D1 API rehearsal

`scripts/foundation_local_d1_rehearsal.mjs` uses the actual D1 binding
interface through **Miniflare**, applied to an isolated local database with
the production `catalogue_titles` schema from migrations **0017 and 0027**.

This test consumes the exact saved 20-row preflight snapshot and the
17-reviewed/3-held decisions, then exercises:

- Parameter-bound, conditional language + provenance updates;
- Guard statements that trigger an SQL constraint error on stale values,
  causing the **entire D1 batch** to abort rather than silently skip a row;
- An exact guarded inverse after a successful 17-row batch;
- An unrelated sentinel and three disputed rows, which must never change;
- A forced stale last-row forward batch after 16 earlier writes;
- A forced newer edit that prevents inverse from overwriting it;
- Local D1 persistence across emulator restart.

The local D1 test uses a **synthetic database UUID**, creates only temporary
runner-local state, requires no Cloudflare credentials, and never issues
`--remote` commands. It tests production catalogue table shape and indexes,
but is **not** a real remote nonproduction D1 clone and does not verify
Cloudflare Time Travel. Keep those separate gates open.

## Remote staging D1 test — disposal and strict scope

The workflow `.github/workflows/foundation-remote-staging-d1.yml` exercises
the 20-record correction preview in a **new, disposable remote D1 database**
using the account's GitHub secret. It does **not** access the existing
`cinema-and-series` production database beyond listing its control-plane
identity to ensure that the scratch UUID is different. It neither deploys
the app nor updates production data.

Safety controls in `scripts/foundation_remote_staging_d1.py`:

- Unique scratch name `foundation-v2-qa-<GitHub run ID>-<attempt>`
  with numeric validation; never use the production database name.
- Before creation, check Cloudflare's D1 account database count. If the
  account has more than eight databases, **abort without creating a QA DB**
  to reserve a free slot on a possible Free account.
- Record the newly created database's UUID and verify it differs from
  production; generate a temporary Wrangler config binding **only that
  UUID**, never the production DB.
- Apply production `catalogue_titles` migrations 0017 and 0027 to scratch
  only; seed 20 archived records plus one unrelated sentinel.
- Run a 17-record guarded update/inverse and an intentional failed forward
  and inverse. Fail on partial updates or accidental edits to held films.
- Delete scratch by its exact UUID-verified name in a finally block; GitHub
  also runs a second `if: always()` cleanup step. Refuse deletion if the
  control-plane UUID doesn't match the one created by the current run.
- Persist only a non-sensitive JSON result; do not archive secret-bearing
  runner configuration or the original production snapshot in this workflow.

If cleanup cannot be verified, the workflow is **not successful**. Use the
run's unique name and account D1 dashboard to investigate orphan staging
resources; do not delete any other database.

Because this test uses only a 20-record copy, it does not certify the whole
70,175-record production schema or demonstrate a safe full production
Time Travel restore. Production changes remain blocked pending separate
backup, fresh before-value checks, and owner authorization.

## Remaining mandatory gates before any real correction

- [ ] Owner explicitly approves **a separate proposed correction PR** with
      exact source IDs and dates. The user saying "continue" with foundation
      development does not pre-approve a production data modification.
- [ ] One nonproduction D1 clone/test database is provisioned, with matching
      schema, unique indexes and constraints; verify guarded forward and inverse
      behavior there without changing production.
- [ ] Current production D1 Time Travel bookmark retrieved **immediately before
      the write**, and a separate full-column snapshot of the 17 original rows
      securely retained in a restricted artifact. Do not treat a saved earlier
      SELECT of six fields as complete recovery data.
- [ ] Pre-write query rechecks record identities and `Unknown` before-values;
      any missing/change/duplicate aborts the **entire** batch.
- [ ] Confirm independent original-language evidence for each film remains
      current, and that disambiguation concerns have been resolved.
- [ ] Only the 17 explicitly eligible existing film IDs are considered;
      never insert, delete, update years, touch the three held films, or
      normalize unrelated records in the same operation.
- [ ] Dedicated manual approval and tightly scoped production credentials.
      No schedule, on-push or automatic workflow resume.
- [ ] Guarded, atomic transaction with expected changed-row count and
      immediate post-write API and DB verification; preserve an auditable
      rollback plan. Failure must stop the workflow without partial commits.

Cloudflare D1 Time Travel is **whole-database recovery**: restoring a bookmark
overwrites intervening changes to *other* records. It is never the default way
to undo 17 language corrections. Prefer guarded row-level inverse operations
unless a separately authorized disaster recovery incident requires Time Travel.

See:
- https://developers.cloudflare.com/d1/reference/time-travel/
- https://developers.cloudflare.com/d1/wrangler-commands/
