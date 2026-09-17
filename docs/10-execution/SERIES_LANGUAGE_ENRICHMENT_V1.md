# Series Language Enrichment V1

**Status: COMPLETE — PRODUCTION VERIFIED**  
**Started: 2026-09-16**  
**Completed: 2026-09-17**

## Why this slice was prioritized

The first Catalogue Quality V1 production baseline measured:

- total SeriesRun records: **8,034**;
- explicit language known: **245 / 8,034 (3.05%)**;
- explicit language unknown: **7,789**;
- Wikidata identity mapped: **7,921 / 8,034 (98.59%)**.

This made SeriesRun language the highest-impact metadata remediation target that could be improved from an already-attached stable identity source.

## Source contract

V1 enrichment uses only explicit Wikidata **P364 — original language of film or TV show** claims.

It does **not** infer language from:

- country;
- title spelling or script;
- cast/crew nationality;
- Wikipedia category unless that category already supplied the existing value;
- popularity or market assumptions.

## Resolution policy

A production row is eligible only when:

1. current `language_name` is missing or `Unknown`;
2. the row has a valid Wikidata QID;
3. Wikidata exposes at least one non-deprecated P364 claim.

Resolution behavior:

- one unique usable P364 value → resolve;
- one unique preferred-rank P364 value → resolve to the preferred value;
- multiple preferred values → ambiguous, no write;
- multiple normal-rank values with no unique preferred value → ambiguous, no write;
- missing P364 → no write;
- unresolved language-item label → no write.

The scalar V1 field does not silently collapse genuinely multilingual works.

## Provenance

Migration `0019_series_language_provenance.sql` adds:

- `language_source`;
- `language_source_url`.

Existing explicit languages are backfilled as `wikipedia_category` with their existing source URL. New P364 resolutions are stored as `wikidata:P364` with the SeriesRun Wikidata entity URL.

## Write safety

Generated SQL updates include both canonical row ID and Wikidata QID and only execute while the production value is still unresolved. A language resolved after snapshot capture is therefore not overwritten by a stale enrichment artifact.

The production path is additionally gated through `series-language-enrichment-write-request.yml`, which verifies the successful analysis run, exact aggregate evidence, commit ancestry, and enrichment-critical code immutability before dispatching `apply_writes=true`.

## Hardened execution model

The initial monolithic resolver was replaced with eight deterministic QID shards after live testing exposed two infrastructure risks:

1. long-running Wikimedia requests can be rate-limited;
2. MediaWiki can return transient `maxlag` errors inside HTTP-200 JSON responses.

The hardened implementation:

- captures one stable production snapshot;
- partitions candidates into deterministic, disjoint QID shards;
- runs shards serially to avoid hammering Wikimedia;
- retries HTTP 429 and MediaWiki transient API errors;
- never converts API failures into fake “metadata missing” findings;
- aggregates all shard artifacts and rejects duplicate cross-shard updates;
- applies production writes only through explicit guarded dispatch;
- verifies final production coverage after all shard writes.

## Production results

### Pre-write baseline

- total series: **8,034**
- language known: **245 / 8,034 (3.05%)**
- language unknown: **7,789**

### Verified analysis run

Analysis run `35138082917` at commit `0521583de2083286cc303d7058643ffca0be0270` completed successfully across all eight shards:

- QID-backed unresolved candidates: **7,676**
- safe explicit P364 updates: **3,807**
- ambiguous: **107**
- missing P364: **3,762**
- missing language label: **0**
- unknown-language rows without usable Wikidata QID: **113**

### Guarded production write

Production write run `35175342182` completed successfully on 2026-09-17:

- migration `0019_series_language_provenance.sql`: **applied successfully**
- production snapshot: **7,676** QID-backed unresolved candidates
- all **8 / 8** write shards: **successful**
- live explicit P364 updates: **3,808**
- ambiguous: **107**
- missing P364: **3,761**
- missing label: **0**
- final `verify-write` job: **successful**

The live write resolved one more title than the earlier analysis because Wikidata gained or changed one explicit P364 claim between the two runs. The production resolver re-evaluates the current explicit source and still applies the same no-inference rule.

### Post-write production coverage

- total series: **8,034**
- language known: **4,053 / 8,034 (50.45%)**
- language still unknown: **3,981**
- language rows with recorded provenance: **4,053 / 4,053 known rows (100%)**
- net increase in known series language: **+3,808 rows**
- coverage improvement: **3.05% → 50.45%**

Selected verified post-write language counts include:

- English: **1,966**
- Korean: **516**
- Hindi: **350**
- Spanish: **313**
- Japanese: **235**
- Malayalam: **30**
- Marathi: **14**
- Telugu: **7**
- Kannada: **4**
- Punjabi: **3**
- Gujarati: **1**

These counts reflect explicit stored labels and should not be interpreted as complete market coverage for each language.

## Acceptance

- enrichment unit tests pass: **YES**
- migration applies cleanly: **YES**
- production run completes without overwriting known language values: **YES**
- every known production language has explicit provenance after migration/write: **YES — 4,053 / 4,053**
- post-run language coverage measured and documented: **YES — 50.45%**
- all eight production write shards complete: **YES**
- post-write production verification succeeds: **YES**
- Catalogue Quality V1 post-write S0 regression check: **triggered by the closeout workflow change and required before final quality closeout**

## Remaining language backlog

The remaining **3,981** unresolved series are intentionally not guessed. They include:

- titles with no explicit P364 claim;
- ambiguous multilingual claims that cannot fit safely into the current scalar representation;
- titles without usable Wikidata identity.

Any future language-enrichment source must preserve the same provenance and non-inference standard.

## Next quality priority

With SeriesRun language coverage raised above 50%, the next Catalogue Quality V1 remediation target is the **223 series missing first-air year**, followed by native/original titles, movie language enrichment, lifecycle status, artwork, and multilingual search benchmarks.
