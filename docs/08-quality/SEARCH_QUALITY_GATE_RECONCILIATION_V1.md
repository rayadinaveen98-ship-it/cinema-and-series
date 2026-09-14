# Search Quality Gate Reconciliation — V1

**Status: LOCKED**  
**Date: 2026-09-14**

## Purpose

Cinema and Series currently has two complementary search-quality documents:

- `SEARCH_QUALITY_BENCHMARK_V1.md` — minimum Research Foundation / pre-freeze benchmark design and implementation baseline;
- `SEARCH_QUALITY_THRESHOLDS_V1.md` — stricter public-launch quality and latency targets.

They are not competing specifications. This document defines precedence and phase gates.

# Gate S0 — Specification freeze

Before `FROZEN_V1_CONTRACT.md` can freeze:
- search normalization/transliteration behavior is defined;
- at least **500 labeled search assertions** exist across the required scripts/languages and adversarial classes described by `SEARCH_QUALITY_BENCHMARK_V1.md`;
- expected target entities/ranks are adjudicated;
- the public-launch thresholds are already frozen in `SEARCH_QUALITY_THRESHOLDS_V1.md`.

No working search engine is required merely to freeze the product contract, but the test corpus and expected behavior must exist.

# Gate S1 — Engine implementation acceptance

When the first Postgres FTS/`pg_trgm` search implementation exists:
- run the >=500 pre-freeze/core assertions plus all newly converted relevant gold cases;
- meet or exceed the correctness floors in `SEARCH_QUALITY_BENCHMARK_V1.md`;
- record failure taxonomy and language/script segmentation;
- prove SearchDocument rebuild/merge redirect behavior.

Failure here blocks declaring the Search Engine implementation complete.

# Gate S2 — Public V1 launch

Before public non-beta V1 launch:
- benchmark set expanded to at least **2,000 labeled queries** with the composition and per-language floors in `SEARCH_QUALITY_THRESHOLDS_V1.md`;
- stricter launch correctness targets in that document pass;
- ordinary-search server-side p95 <= **250 ms** and p99 <= **500 ms** on representative production-like data/load;
- priority script groups pass individually;
- search projection freshness/redirect targets pass.

A clearly limited beta may launch on a constrained catalogue only when the exposed slice still passes its applicable correctness/provenance requirements and is labelled beta.

# Threshold precedence

When the two search documents express different numeric targets:
- **pre-freeze / initial implementation gate:** `SEARCH_QUALITY_BENCHMARK_V1.md`;
- **public launch gate:** the stricter `SEARCH_QUALITY_THRESHOLDS_V1.md`.

A looser earlier threshold can never waive a stricter launch threshold.

# Dedicated-engine escalation

PostgreSQL remains the V1 baseline. Evaluate a dedicated search engine only after reasonable Postgres indexing/query/ranking work fails the applicable quality/latency gate at representative volume.

Changing search technology does not change canonical data, CAS IDs, validation queries or launch thresholds.
