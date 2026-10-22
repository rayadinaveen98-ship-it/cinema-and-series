# Cinema & Series — Data Foundation V2 (2026-10-22)

## Freeze scope

No catalogue growth, poster work, UI changes or unrelated D1 writes until the
baseline has been audited and the owner approves a repair plan. Fourteen jobs
are explicitly paused at their job-level entrypoint. This stops both scheduled
and manually dispatched executions. Paused workflows are not considered
evidence of executed work.

The public app, its API, source-only film-language evidence collector,
read-only metrics and CI remain available.

## Verified starting baseline

From [read-only production language report](https://github.com/rayadinaveen98-ship-it/cinema-and-series/actions/runs/39755977413):
- Deduplicated films: 51,872; series: 18,303; total: 70,175
- Unknown language: 50,380; known: 19,795
- Two movie tables: 6,335 exact-date movie records + 45,537 year-only unique movie records; series: 18,303
- Indian (country_code IN): 32,739 films, 1,473 series

Do not assert that all current unknown languages can be filled from source
evidence. Language claims must preserve provenance and multilingual ambiguity.

## Phase 1 — Integrity baseline, no production writes

Trigger `Catalogue Quality V1` once from this freeze marker change:
- full identity, title, Wikidata QID, country, language, date precision, source and media type audit
- duplicate and cross-type identity flag list; annotate severity
- full raw D1 snapshots of all three catalogue tables preserved as a restricted,
  30-day GitHub Actions artifact for reproducibility and rollback assessment
- compare live quality counts with the separately audited 70,175 snapshot
- do not treat the archived copy as an independently tested Cloudflare D1
  backup until a tested restore path has been established

## Phase 2 — Determine repair precedence

1. S0: same QID on movie and series / irreconcilable identity, invalid chronology
2. S1: wrong type, malformed title, invalid release date/year, source mismatches
3. S2: duplicate title-year alternatives, unknown language/country, absent source
4. S3: native title, lifecycle, aliases, season detail and formatting

Review QID and article identity first. Do not delete duplicates or overwrite
values without verifying provenance and preserving original records.

## Language normalization

Canonical display mapping is not a change to source language. Preserve the
raw value and add canonical mapping only when unambiguous. Do not infer
language from film country, title, actors or category alone; prefer explicit
original-language P364, preserve multiple claims and mark ambiguity.

## Recovery and controlled unfreeze

- The static pauses are in `.github/workflows/`; restore one workflow at
  a time through reviewed PRs, not by toggling a background coordinator.
- `ops/data-foundation-v2-freeze.json` is the owner-reviewed source of truth.
- When a workflow is restored, remove its freeze assertion from the verification
  test *in the same review*, so a partial resumption is intentional.
- Never automatically resume the P1 background coordinator merely because its
  previous completion artifact exists.
- Read-only quality audits and public serving must remain functional throughout.
- First real correction wave must be small, evidence-backed, idempotent,
  independently re-counted, and reversible. No automatic mass corrections.
