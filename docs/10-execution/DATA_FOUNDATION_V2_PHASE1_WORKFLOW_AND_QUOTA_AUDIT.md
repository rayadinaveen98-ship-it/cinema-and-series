# Data Foundation V2 — Phase 1: scheduled workflow and quota-reporting audit

**Prepared 2026-10-24. Production catalogue freeze remains active.**
This report is about **automation visibility and quota reporting**, not a
production write request or a declaration that Cloudflare quota was exhausted.

## Verified incident

Owner-dispatched scratch D1 canary
[run 40060701564](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40060701564)
passed its local safety checks, then stopped at read-only account preflight.
The Cloudflare D1 GraphQL daily-usage query returned **zero groups** on
2026-10-24 UTC. The prior preflight arithmetic printed **100,000 estimated
writes remaining** by subtracting zero, but correctly refused canary staging
because no current-day records existed. An empty day does **not** establish
either unused capacity or exhausted capacity. The remote D1 mode introduced
in PR #217 was **not executed in that failed run**.

No scratch database was created in that run. No production correction was
applied.

## Code and reporting correction

`scripts/foundation_remote_account_preflight.py` now retains fail-closed
behavior while reporting a **three-state, read-only analytics status**:

| Safe status | Interpretation | Staging allowed? |
| --- | --- | --- |
| `usage_unverified` | No current UTC-day analytics groups | No |
| `reported_headroom_insufficient` | Cloudflare-reported daily counts below conservative canary reserve | No |
| `reported_headroom_sufficient` | Cloudflare-reported daily counts above canary reserve | Provisional prerequisite only |

- A missing daily-usage group yields **null**, not 100,000, for remaining
  write allowance, and **null**, not 0, for reported usage counters.
- A low positive balance is distinct from the actual daily limit having been
  reached; `reported_daily_write_limit_reached` distinguishes the two and
  is null when usage is unknown.
- A valid historical/previous UTC-day group is not silently treated as a
  current-day balance. Malformed, ambiguous or truncated analytics fail closed.
- GraphQL can lag; even `reported_headroom_sufficient` is **not**
  real-time proof or authorization for full remote staging/production.
- The manual synthetic canary presents the exact reason in its job summary
  and aborts **before scratch database creation** if usage is unverified.

All checks remain isolated from the real production D1. This PR makes
**no change that bypasses the approval or quota gate**.

## Automated workflow inventory

Credential-free CI on
[run 40061692161](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40061692161)
enumerated **106 files in `.github/workflows`** on its feature-branch
checkout, with:

- **18** workflows declaring `schedule:`.
- **3** declaring `workflow_run:`.
- **61** files referencing a Cloudflare API token.
- **13** scheduled workflow files referencing that token.
- **67** requiring follow-up manual source review by conservative static
  criteria.
- **0** unrecognized/inline trigger shapes in the current parser.

**Important:** these are code-presence counts, NOT counts of actually
running jobs or database writers. The inventory cannot prove the absence
of indirect writes via external scripts or workflow dispatch.

The CI artifact `foundation-v2-workflow-inventory-static` contains every
workflow filename, trigger, cron expression, direct Cloudflare credential
reference, explicit freeze-file reference and manual-review flag.

### Actual recent scheduled activity inspected

| Workflow | What the run actually reported |
| --- | --- |
| `catalogue-quality-post-write-watch.yml` | Recent scheduled runs reported no recent verified production enrichment write; did not dispatch another quality audit |
| `india-film-language-source-only.yml` | Collected/checkpointed source-language evidence; reported D1 reads 0 and writes 0 |
| `foundation-bulk-film-reconciliation.yml` | Workflow-chained, read-only archived-film evidence reconciliation; reported writes 0 |
| `india-catalogue-autopilot.yml` | Scheduled runs were skipped under the configured job-level freeze |

See [quality watch run 40052295686](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40052295686),
[source-only run 40027265241](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40027265241),
[reconciliation run 40027682051](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40027682051),
and [catalogue autopilot 40016189936](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40016189936).

### Source-code review of all 18 scheduled workflows

The 18 scheduled files are:

- Artwork: `artwork-bulk-500.yml`, `existing-title-artwork-100-pilot.yml`,
  `vrt-indian-poster-batch-02.yml`.
- Catalogue/import: `india-catalogue-autopilot.yml`,
  `series-catalogue.yml`, `wikidata-backfill.yml`, `wikidata-refresh.yml`,
  `wikipedia-year-catalogue.yml`, `p1-quota-safe-daily-resume.yml`,
  `p1-background-write-coordinator.yml`,
  `india-film-language-quota-reset-20261020.yml`.
- Observability/source: `catalogue-availability-check.yml`,
  `catalogue-quality-post-write-watch.yml`, `catalogue-quality-v1.yml`,
  `india-film-language-coverage-audit.yml`,
  `india-film-language-source-only.yml`, `website-monitor.yml`,
  `youtube-monitor.yml`.

High-risk historical import and monitor workflows frequently retain cron and
Cloudflare-token references **even though their execution jobs are currently
disabled by `if: ${{ false }}`** (job-level freeze). The dated
2026-10-20 film-language recovery workflow relies on a strict historical UTC
date gate instead. A later source change or explicit unfreeze could change
their behavior. Keep their guards in place and review their active job
conditions before any release.

At the code level, `catalogue-availability-check` polls the public app
API without Cloudflare credentials; the post-write watcher checks GitHub
history and may dispatch a **read-only** quality workflow when a verified
write exists; the Indian-language source collector works without production
D1 access. Scheduled jobs may consume GitHub Actions minutes or external
API quotas even with no D1 writes.

The static CI review marks scheduled jobs referencing Cloudflare credentials
but lacking a direct freeze-file reference for extra human review. This does
**not** imply such jobs actually write or lack other safety gates; several
have explicit `if: false` job-level controls.

## Still pending before Phase 2

1. Confirm GraphQL analytics freshness and account scope against another
   Cloudflare account-facing source when possible. Do not infer today's
   usage is zero from an empty result.
2. Check and document the actual live D1 Free-plan quota counters and any
   relevant reset/analytics lag. If the evidence remains absent, keep the
   scratch canary blocked.
3. Reconcile the 67 conservative static review candidates into an explicit
   approved set of allowed schedules (source-only, public health, read-only)
   and a set held behind the freeze. This inventory is a starting point,
   not automatic permission to alter jobs.
4. After an independent credible quota readiness check, manually run the
   disposable D1 canary on the current `main` branch once; require
   positive remote binding/rollback result **and** exact scratch deletion.
5. Keep the 70,175-title production freeze, backup custody work and
   explicit owner approval requirements unchanged. The historical encrypted
   candidate backup artifact expires 2026-11-22.

**No production writes, imports, posters, or UI changes are authorized by
completing this audit.**


## Phase 1.4 — Freshness diagnostics for historical Cloudflare D1 analytics

Cloudflare documents the D1 dashboard's charts as being sourced from its
**GraphQL Analytics API**. Thus, a dashboard screenshot and the GraphQL
daily-account query are not fully independent sources of quota evidence.

The credential-scoped, **read-only** account-preflight workflow now makes
one additional GraphQL request covering exactly three UTC calendar days
(today and the two preceding days), using the account-wide
\`d1AnalyticsAdaptiveGroups\` dataset. It aggregates reported row reads,
row writes, read queries and write queries by day into a safe summary;
database UUIDs, account identifiers and API tokens never enter artifacts.
The diagnostic compares its current-day aggregate with the existing
single-day report, with any discrepancy marked inconsistent. Neither
two matching reports nor a valid historical report proves real-time quota
headroom: both requests share the same delayed analytics source.

Possible safe statuses:

- \`today_missing_historical_visible\` — prior-day GraphQL records exist;
  today's metrics have not appeared. **Not evidence of quota exhaustion.**
- \`all_three_days_missing\` — no records in the three-day window; could
  indicate idle databases, delayed analytics, dataset visibility or other
  causes. It does not mean zero usage.
- \`same_day_snapshots_inconsistent\` — current-day group presence or row
  totals disagree across two GraphQL requests. Evidence is provisional.
- \`today_present_same_source_counts_agree\` — current-day totals agree across
  two GraphQL requests, but **not** an independent quota/billing validation.

The output explicitly says
\`independent_realtime_quota_verified: false\` and
\`canary_or_production_write_authorized: false\`. The existing
\`usage_unverified\` admission block remains unchanged and cannot be bypassed
by historical data. No D1 SQL is issued.

The follow-up for an independently verified current allowance is to inspect
Cloudflare's account billing usage together with operational evidence
(e.g., per-query D1 row counts) and confirm an adequate reserve before
the owner starts any temporary D1 staging. Billing dashboard counters are
still not guaranteed real time. No automatic scratch canary or production
write is triggered here.

Cloudflare references:
- https://developers.cloudflare.com/d1/observability/billing/
- https://developers.cloudflare.com/d1/observability/metrics-analytics/
- https://developers.cloudflare.com/d1/platform/pricing/


## Phase 1.5 — Manual one-query runtime health check (not quota certification)

On 2026-10-24, the read-only account D1 GraphQL diagnostics still returned
\`usage_unverified\` for today, but historical days were visible. Cloudflare's
September 2026 D1 Free-tier enforcement explicitly returns a dedicated error
when daily read or write limits have actually been reached. A **direct query
with its own \`meta.rows_read\` and \`meta.rows_written\`** can provide a
different type of operational evidence — whether one tiny query is currently
accepted, not what account-wide capacity remains.

A new workflow \`.github/workflows/foundation-d1-runtime-readonly-probe.yml\`
is **strictly workflow_dispatch-only** with an explicit
\`YES_ONE_READ_ONLY_D1_QUERY\` choice. It:

1. Verifies the existing 70,175-title production freeze and source script.
2. Lists account D1 databases via the control plane, requires **exactly one**
   named production DB with a valid UUID and **no orphaned QA databases**.
3. Sends **exactly one** Cloudflare REST D1 query:
   \`SELECT 1 AS probe_ok\` against the UUID-verified existing database.
   This may consume a small amount of the D1 query allowance, but it is a
   constant expression with **no table reads, mutations, schema changes,
   database creation/deletion, or retry**.
4. Verifies the one-row result and \`meta.rows_written=0\`,
   \`meta.changes=0\`, \`meta.changed_db=false\`. Any deviation produces
   \`query_unverified\`, not a pass.
5. Classifies documented Cloudflare daily read/write-limit errors into
   \`cloudflare_reported_daily_read_limit\` or
   \`cloudflare_reported_daily_write_limit\` without printing error bodies,
   tokens, database/account IDs, URLs or SQL contents. Other errors are
   \`query_unverified\`.
6. Uploads **only** bounded safe status fields, query-local row counts and
   the explicit statement that available account-wide row headroom remains
   **unknown**.

If successful, this **only** proves a tiny read-only D1 query was permitted at
that moment; it **cannot** establish sufficient remaining reads/writes for a
synthetic staging canary, especially alongside other account traffic. It does
NOT bypass the independent Cloudflare GraphQL headroom gate, authorize any
scratch D1 creation, or prove that the account has no future quota risk.

Cloudflare docs:
- https://developers.cloudflare.com/changelog/post/2026-09-01-d1-free-tier-limit-enforcement/
- https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/
- https://developers.cloudflare.com/d1/observability/metrics-analytics/

The next operational decision remains a separate explicitly authorized
scratch-only staging request *after* adequate credible quota headroom is
established. This diagnostic is not automatically dispatched by a PR merge,
on a schedule, or as a condition watcher. No catalogue mutation is performed.


## Phase 1.6 — Account billing-usage source cross-check (manual, no D1)

Cloudflare introduced the account-level **Billable Usage API** in August
2026. It comes from Cloudflare's billing/charge-period usage system, unlike
D1's per-query GraphQL charts. The official documentation explicitly notes
the API **updates daily**, not in real time; it therefore cannot prove
current free-tier remaining allowances or authorize a remote canary.
It also requires account **Billing Read** permission and may lack coverage
on unsupported billing account types or on a Free account with no reported
usage rows.

The opt-in manual workflow
\`.github/workflows/foundation-d1-billing-usage-diagnostic.yml\` calls
**only** \`GET /client/v4/accounts/{account}/billable-usage\` with a bounded
recent 7-day date range, using a **dedicated**
\`CLOUDFLARE_BILLING_READ_TOKEN\` secret, not the D1 API token. On first use
the owner may create an Account > Billing > Read API token and save it as
that GitHub Actions secret. A missing or restricted token reports
\`billing_token_not_configured\` / \`billing_permission_unavailable\`
without exposing any token, URL, response body, billing account, prices,
costs, subscription names or raw usage records.

The safe aggregate only reports whether *historical* D1 billing rows exist,
their count, and the most recent charge-day start. The signal is not an
accurate row-read/write total unless the units, metric scopes and period
semantics are independently proved. Empty billing records do **not** mean
zero D1 usage, zero cost, or exhausted quota.

The workflow requires explicit choice \`YES_BILLING_READ_ONLY\` and has
**no push, schedule, workflow-run chain, D1 SQL or scratch creation**.
It always emits:
\`current_quota_headroom_verified=false\`,
\`scratch_staging_authorized=false\`,
\`production_corrections_authorized=false\`.

Evidence limitations:
- Direct D1 \`SELECT 1\` live query succeeded in
  [#40063535530](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40063535530),
  with query-local **zero writes**. That proves a tiny read is permitted,
  **not** available daily write headroom.
- D1 GraphQL showed historical days but no records for today's UTC day,
  as of [#40062945995](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/40062945995).
- Even when historical billing rows appear, they may lag. The canary
  preflight remains fail-closed until current account-wide quota evidence
  and a separately reviewed safe admission procedure are available.

Cloudflare sources:
- https://blog.cloudflare.com/billable-usage-api
- https://developers.cloudflare.com/api/resources/billing/subresources/usage/
- https://developers.cloudflare.com/billing/understand/billing-permissions/
