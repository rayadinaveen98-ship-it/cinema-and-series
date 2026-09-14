# Validation Corpus Tranche 11 v0.1

Status: ACCEPTED BY CI

This tranche adds:

- hard cases `VC-0173..VC-0183` in `validation/corpus-tranche-013.jsonl`;
- search assertions `SQ-0251..SQ-0275` in `validation/search/queries-009.jsonl`;
- primary-cohort assignments in `validation/corpus-primary-cohorts-002.csv`;
- semantic bindings in `validation/semantic/bindings-006.jsonl`;
- curated reference states in `validation/semantic/reference-state-004.jsonl`.

Latest accepted validation run: GitHub Actions `34843860186` (head `48f1ed9d79043cf9b2f764f00f7813709a09bc3c`).

## Purpose

Attack three measured deficits with authoritative evidence:

1. India release / territory / version history;
2. historical archive / preservation representation;
3. native-title and localized search around restored Indian classics.

The tranche deliberately models release history as multiple `ReleaseEvent` records and restorations as distinct `Version` entities. A restoration, festival screening, theatrical re-release or future festival date must never overwrite the original Work or its historical release record.

## Hard cases

### `VC-0173` — Manthan Work vs restored Version

The 1976 Work and the 2024 4K restoration are distinct CAS entities sharing one underlying Work lineage. Restoration source-element provenance is retained.

### `VC-0174` — Manthan Cannes vs India theatrical re-release

The restored Version's Cannes 2024 world premiere and June 1–2, 2024 India theatrical re-release are separate events. Festival and theatrical dates do not overwrite one another.

### `VC-0175` — Do Bigha Zamin cross-archive restoration provenance

The restored Version uses NFDC-NFAI picture/sound negatives plus missing material from a BFI combined dupe negative. Cross-archive source provenance remains explicit and does not change the 1953 Work identity.

### `VC-0176` — Do Bigha Zamin original festival history vs restoration premiere

The original film's Cannes 1954 history and restored-Version Venice 2025 world premiere coexist as separate historical events.

### `VC-0177` — Sholay restored Version with content differences

The 2025 restoration is a Version of the 1975 Work and preserves version-specific claims for the original ending and two deleted scenes. Bologna and Toronto 2025 screenings are distinct restoration events and do not replace the 1975 release.

### `VC-0178` — Ishanou Cannes history

The original Work's Cannes 1991 screening and the restored Version's Cannes Classics 2023 premiere remain separate ReleaseEvents.

### `VC-0179` — Aranyer Din Ratri source-element provenance

The 4K restoration retains provenance for original camera/sound negatives and a BFI magnetic track while remaining a Version of the 1970 Work.

### `VC-0180` — Amma Ariyan lost original camera negative

The original camera negative is recorded as not surviving. Restoration from surviving prints must not erase that preservation fact, and the Cannes 2026 restored-Version event remains separate from the 1986 Work history.

### `VC-0181` — In Which Annie Gives It Those Ones

Restoration provenance spans NFDC-NFAI 16mm picture/sound negatives and an FHF 35mm release print. The Berlinale 2026 restored-Version premiere does not become the Work's original release date.

### `VC-0182` — English, August multiple Venice screenings

The restored Version has separate September 9 and September 10, 2026 Venice screening events. Festival metadata also demonstrates multilingual-language metadata that must remain independent from release chronology.

### `VC-0183` — Pakeezah future restoration events

The 1972 Work remains separate from its 2026 restored Version. The original camera negative is recorded as not surviving. Festival Lumière dates and the BFI London Film Festival event are future restoration events and may never rewrite the 1972 release.

## Evidence profile

The tranche prioritizes grade-A archive and festival sources, including:

- Film Heritage Foundation;
- Festival de Cannes / Cannes Classics;
- La Biennale di Venezia / Venice Classics;
- Festival Lumière;
- BFI London Film Festival.

This is intentionally stronger than relying on general movie databases for restoration/version/release chronology.

## Validation failure caught by CI

The first manifest attempt used the non-schema source kind `archive_first_party` for Film Heritage Foundation evidence. CI correctly rejected 10 records because the locked evidence enum supports `archive` and `first_party` separately but not that compound value.

The corpus schema was **not weakened**. The records were corrected to `source_kind: archive` and the full pipeline reran successfully.

Failed run: `34843448153`.

Repair commit: `d86c5c4e3f6eeffde96f102a3da53495255917e1`.

First green post-repair run: `34843627709`.

This failure is useful validation evidence: schema strictness prevented ad hoc source taxonomy from leaking into the corpus.

## Primary-cohort mapping scalability

During this tranche, `validation/run_quota_audit.py` was upgraded from one monolithic mapping file to incremental files matching:

`validation/corpus-primary-cohorts-*.csv`

The audit still enforces global duplicate, stale, missing and invalid-assignment checks across all mapping files.

Current assignment files: **2**.

This removes a maintenance bottleneck as the corpus grows toward ~1,000 cases without weakening quota integrity.

## Search tranche

`SQ-0251..SQ-0275` adds 25 evidence-backed queries around Manthan, Do Bigha Zamin, Amma Ariyan, Aranyer Din Ratri and Pakeezah.

Coverage includes:

- Hindi Devanagari native titles;
- Malayalam native title and qualified queries;
- Bangla native title plus `Aranyer Din Ratri` / `Days and Nights in the Forest` retrieval;
- sourced Hindi spelling/sitelink differences for Pakeezah;
- Marathi, Punjabi and Telugu localized sitelinks where the source explicitly provides them;
- a cross-entity-kind `Pakeezah` collision between the 1972 film and a same-name television series.

Generated qualified queries remain search-only benchmark inputs and are not canonical title claims.

## Accepted state after tranche

### Corpus

- hard cases: **183/1000**;
- current machine-readable parity: **183/183**;
- hard-case assertions: **418**;
- gold candidates: **135**;
- evidence-upgrade needed: **47**;
- open adjudication: **1**;
- critical risk: **86**;
- high risk: **91**;
- medium risk: **6**.

### Primary quotas

- India identity / multilingual / localization: **23/180**;
- Global Work / Version / relationship: **26/100**;
- Release / territory / certification / availability: **22/120**;
- Series structure: **29/140**;
- People / credits / roles / music: **22/100**;
- Organizations / companies / platforms / rightsholders: **12/60**;
- Historical / archive / preservation: **16/100**;
- Upcoming / unreleased / lifecycle: **17/70**;
- Source conflict / canonicalization / provenance: **10/60**;
- Search / transliteration / disambiguation: **6/70**.

### Search

- pre-freeze assertions: **275/500**;
- Telugu: **19/60**;
- Tamil: **21/60**;
- Malayalam: **15/50**;
- Kannada: **9/50**;
- Bengali: **12/40**;
- Gujarati: **5/20**;
- Punjabi: **8/20**;
- Devanagari combined: **36/80**.

### Semantic execution

- runtime-ready assertions: **134/418**;
- assertions needing bindings: **280/418**;
- manual/specialized: **4/418**;
- semantic binding-overlay cases: **46**;
- explicit overlay bindings: **111**;
- reference cases: **35**;
- reference assertions: **91**;
- reference PASS: **91**;
- reference failures: **0**.

Reference PASS is still reference-oracle consistency only. Production-engine execution remains a future freeze requirement.

## Model lessons locked by this tranche

1. Original Work, restoration Version and screening/re-release events are different entity layers.
2. A restoration date may never replace an original release date.
3. Multiple festival screenings of one Version remain separate ReleaseEvents when event granularity matters.
4. Preservation facts such as missing original negatives survive independently of restored media availability.
5. Restoration source elements require provenance, including holding archive/institution where known.
6. Version-specific content differences must not be generalized onto every Version of a Work.
7. Future festival events can coexist with historical release records without changing Work identity.
8. Source taxonomy is schema-governed; new ad hoc source-kind strings require explicit model review rather than silent introduction.

## Next measured gaps

The corpus remains far below final freeze quotas. Highest-priority next work:

1. more India release/certification/territory cases, especially **actual certification and territory-specific release semantics**, not only restoration history;
2. historical/archive cases outside the currently strong restoration pattern, including lost/fragmentary/short/documentary/regional cinema;
3. Kannada and Malayalam search depth, then Telugu/Tamil/Bengali;
4. critical legacy assertion binding migration;
5. stronger organization/rightsholder and source-conflict coverage.
