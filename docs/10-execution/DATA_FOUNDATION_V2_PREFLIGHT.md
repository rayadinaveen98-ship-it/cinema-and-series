# Data Foundation V2 — external evidence and backup readiness

## Current position (22 October 2026)
Frozen review package: **20 existing films**. Source-only originally matched
80/80 samples, but independent external source review finds:

- **17** films with external corroboration of language and the recorded year,
  subject to fresh production row preflight and human approval.
- **3 held**: Asurakulam (2017 stored; TBA vs 2015 reports),
  Saadey CM Saab (2015 stored vs original release 27 May 2016),
  Mr. Romeo (2021 Odia TV film has a title collision with unrelated titles
  including a 2014 dubbed work; specialist entry cites Wikipedia).
- The support list is **not** a production update authorization or proof of
  official original-language records.

The evidence manifest is
`data/review/foundation-v2-external-evidence-20.json`.
The CI workflow joins those 20 exact frozen IDs to one read-only production
D1 query. If current values change, or a duplicate/new ID appears, hold.

## Backup and recovery requirements — NOT YET COMPLETE

Cloudflare documents that D1's Time Travel can retrieve a bookmark and
restore prior states within the supported retention window. This is not an
isolated full-table export or a substitute for a verified row-level rollback.

1. Before any writing workflow, capture **current D1 Time Travel bookmark**:
   `npx wrangler d1 time-travel info cinema-and-series --json`.
2. Capture the **exact original rows** and complete fields for records to
   change, not merely selected columns or the earlier quality-audit snapshot.
3. Recheck that each `id/wikidata_qid/title/year/country/current-language`
   precondition matches, in the same guarded write operation, and abort
   atomically if not. Never overwrite newly enriched or edited values.
4. Verify a nonproduction recovery path and independently test the inverse
   correction on a cloned/test database before applying production writes.
5. Confirm owner approval, then unlock only the dedicated 20-film correction
   workflow; all ingestion/artwork/UI freezes remain active.
6. Compare before/after counts, provenance, and filter/API behavior, and
   preserve an audit trail with a short rollback window.

**WARNING:** `wrangler d1 time-travel restore` overwrites **the entire
database**, not only the 20 affected rows, and is destructive to intervening
writes. Never invoke it automatically as the first rollback option. In
normal circumstances use guarded row-level inverse updates on a validated
snapshot; consider entire DB Time Travel only with explicit incident approval.

Source: https://developers.cloudflare.com/d1/reference/time-travel/
Docs: https://developers.cloudflare.com/d1/wrangler-commands/

## Greenlight conditions

Independent evidence **and** a matching live row allow only a
`REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED` status. No production correction
is approved by this milestone. Do not begin broad 6,048-title updates on
these 20 results. Reaudit duplicate identity collisions and normalized
language names before any mass changes.
