# Ingestion jobs — initial curated proof only

- curated/0001_rrr_verified.sql provides one manually cross-checked RRR record, using bare facts and source URLs only.
- Source identity: Wikidata Q60424165; ZEE5 official movie page.
- It distinguishes Indian original theatrical release (2022-03-25) from ZEE5 digital premiere (2022-05-20).
- Current regional streaming offer is explicitly UNVERIFIED, preventing a false current-availability claim.
- Re-running the seed was checked for idempotency in the Neon free pilot.

A deterministic, network-free preflight evaluator now exists under jobs/ingestion: strict Wikidata source allowlist, 40-record batches, canonical-identity review and quarantine decisions, no database writes. CI tests passed. A live/automatic importer has NOT been built. Required next work: license-reviewed source connector, bounded paging, checkpointing, normalization, identity review queue, transactional upsert, audit, and rate-limits/backoff. Never treat source text as trusted instructions.

## Curated 0002 — six sourced film records

jobs/curated/0002_multilingual_verified.sql is a manually researched, deterministic, additive source-linked batch for Jawan, K.G.F: Chapter 2, Kantara, Pushpa: The Rise, Premalu and Jailer. CI replays twice on disposable PostgreSQL and validates source/date/language/audit counts. Neon Free was seeded and replayed with matching results. This is **not** the automated Wikidata ingestion route, and no new film was marked as currently streamable. Source evidence: docs/data/MULTILINGUAL_PILOT_0002.md.


## Curated 0003 — international film and series pilot

`jobs/curated/0003_international_series_verified.sql` adds 4 historical international films and 2 first-season Netflix original series launches, plus original-language data, English search aliases and source-linked provenance. The series debuts are stored in a separate, additive `series_debuts` table (migration 0005), never as a film theatrical premiere or current OTT offer. CI and isolated Neon Free both replayed the seed without duplicate rows. Evidence at `docs/data/INTERNATIONAL_PILOT_0003.md`. No live source fetches, user actions, or paid external accounts were involved.
