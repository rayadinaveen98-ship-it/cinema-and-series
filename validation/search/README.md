# Cinema and Series Search Validation

This directory contains the machine-readable multilingual search benchmark used by Research Foundation v0.1 and later search-engine regression testing.

## Files

- `search-query.schema.json` — versioned record contract.
- `queries-*.jsonl` — labeled search queries.
- `run_search_manifest_validation.py` — schema/invariant validator.

## Evidence discipline

Every query points to a benchmark target backed by evidence.

Query text is classified by derivation:
- `source_statement` — exact title/name statement from an approved benchmark source;
- `source_label` — source label;
- `source_alias` — explicit source alias;
- `source_sitelink` — native/localized form evidenced through a source sitelink when no stronger title statement is available;
- `generated_search_only` — deliberately generated spelling/romanization/typo used only to test recall;
- `generated_qualified_query` — benchmark-created query combining sourced facts such as title + year + language.

A generated query is **never** evidence that its spelling is an official CAS Name.

## Ranking semantics

`expected.max_rank` expresses the maximum acceptable rank for the labeled target under the benchmark phase.

Ambiguous same-title queries may have multiple records sharing the same query text, each requiring a different target to remain visible within Top-N. This tests recall without pretending the ambiguous text has one correct entity.

Qualified queries may legitimately require rank #1 when year/language/type disambiguates the target.

## Phase gates

See:
- `docs/08-quality/SEARCH_QUALITY_BENCHMARK_V1.md` — >=500-query pre-freeze/initial implementation gate;
- `docs/08-quality/SEARCH_QUALITY_THRESHOLDS_V1.md` — >=2,000-query public V1 launch gate;
- `docs/08-quality/SEARCH_QUALITY_GATE_RECONCILIATION_V1.md` — phase precedence.

## Anti-gaming

Do not:
- invent an official title to create an easy query;
- duplicate trivial spelling variants merely to meet language quotas;
- delete a hard query because the engine ranks it poorly;
- use popularity to excuse failure on exact obscure/historical titles;
- feed search scores directly into CAS automatic identity merges.

Failures must be classified and fixed in data, normalization, transliteration, ranking or the model as appropriate.
