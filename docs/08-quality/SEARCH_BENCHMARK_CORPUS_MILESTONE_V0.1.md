# Search Benchmark Corpus Milestone v0.1 — Pre-Freeze S0 Corpus Ready

Status: **ACCEPTED**  
Date: **2026-09-16**  
Accepted revision: `2ea65a48426e8e624fb7de542f0a02d3263b4fe7`  
Accepted CI run: `35072010769`

## Purpose

Record completion of the Research Foundation / pre-freeze Search Gate S0 corpus-size and breadth requirements defined by:

- `SEARCH_QUALITY_BENCHMARK_V1.md`;
- `SEARCH_QUALITY_GATE_RECONCILIATION_V1.md`.

This milestone concerns the **labeled benchmark corpus and expected search behavior**. It does not claim that a production search engine has passed ranking, recall, latency or rebuild tests.

## Accepted corpus

GitHub Actions run `35072010769` completed successfully against revision `2ea65a48426e8e624fb7de542f0a02d3263b4fe7`.

Search manifest summary:

- manifests: **20**
- labeled queries: **543**
- minimum required before V1 freeze: **500**

Query classes:

- native exact: **107**
- sourced alias: **218**
- qualified query: **116**
- Latin exact: **63**
- same-title collision: **19**
- generated spelling variant: **11**
- person alias: **5**
- minor typo: **3**
- generated transliteration: **1**

## Locked Indic floors

All explicit pre-freeze language/script floors are satisfied:

| Floor | Accepted | Required | Status |
|---|---:|---:|---|
| Telugu | 60 | 60 | PASS |
| Tamil | 60 | 60 | PASS |
| Malayalam | 50 | 50 | PASS |
| Kannada | 50 | 50 | PASS |
| Bengali | 41 | 40 | PASS |
| Gujarati | 20 | 20 | PASS |
| Punjabi/Gurmukhi | 23 | 20 | PASS |
| Devanagari combined | 80 | 80 | PASS |

Script distribution at acceptance:

- Bengali: **41**
- Devanagari: **80**
- Gujarati: **20**
- Gurmukhi: **23**
- Kannada: **50**
- Latin: **161**
- Malayalam: **50**
- Tamil: **58** script-tagged queries
- Telugu: **60**

The language-level Tamil count is **60**; two Tamil-language queries are not counted under the Tamil script because their query text is primarily numeric/Latin-contextual.

## Mixed/global/Latin collision-fuzzy breadth

The previously narrative-only Section 8 floor is now machine-audited by `validation/search/run_search_floor_audit.py`.

Accepted result:

- qualifying union: **182 / 120**
- remaining: **0**

A query qualifies for this breadth floor when it materially exercises at least one of:

- Latin-script discovery;
- same-title collision;
- generated spelling/transliteration behavior;
- minor typo/fuzzy behavior;
- person alias behavior;
- explicit global/collision/transliteration/romanized tags.

The union is counted once per `query_id`; overlapping reasons do not inflate the floor count.

## Freeze-floor result

`run_search_floor_audit.py` now emits:

```text
freeze_floor_status=READY
```

Therefore the **Search Gate S0 corpus-size and explicit breadth floors are satisfied**.

## Semantic safety checkpoint

The same accepted CI run preserved the existing semantic guarantees:

- hard cases: **204**
- hard-case assertions: **481**
- runtime-ready assertions: **477**
- manual/specialized assertions: **4**
- semantic debt cases: **0**
- semantic debt assertions: **0**
- reference cases: **139**
- reference assertions: **339 / 339 PASS**

## What this does not mean

This milestone does **not** mean:

- Postgres FTS/`pg_trgm` has passed the 543 queries;
- transliteration/ranking quality thresholds have passed against a real engine;
- latency targets have passed;
- SearchDocument rebuild/merge redirect behavior has passed;
- the public-launch S2 >=2,000-query benchmark has been completed.

Those are implementation/public-launch gates defined separately in `SEARCH_QUALITY_GATE_RECONCILIATION_V1.md` and `SEARCH_QUALITY_THRESHOLDS_V1.md`.

## Next priority

With the Search S0 corpus floor closed, the largest remaining Research Foundation blocker is the stratified hard-case corpus:

- current hard cases: **204 / ~1,000**;
- remaining: **796**;
- new growth must follow `VALIDATION_COHORT_QUOTAS.md` and the anti-padding rules;
- every new assertion should receive semantic bindings as it is added so zero binding debt is preserved.
