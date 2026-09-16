# Catalogue Growth 10K Runbook

This runbook operationalizes `docs/10-execution/CATALOGUE_GROWTH_MILESTONE_10K.md`.

## Phase A — Baseline
- Capture production movie and series counts.
- Inspect latest movie catalogue, series catalogue, Wikipedia year catalogue, and Wikidata backfill workflow results.

## Phase B — Throughput
- Keep each D1 write batch within free-tier write limits.
- Favor idempotent UPSERT/INSERT OR IGNORE semantics and bounded source batches.
- Alternate movie and series growth batches so both catalogues advance.

## Phase C — Verification
After each production import:
- confirm workflow success;
- confirm production `/api` catalogue endpoints respond;
- record movie and series totals;
- continue until combined total >= 10,000.

## Stop conditions
Stop only for:
- target achieved and verified; or
- external block requiring credentials/quota/user action.
