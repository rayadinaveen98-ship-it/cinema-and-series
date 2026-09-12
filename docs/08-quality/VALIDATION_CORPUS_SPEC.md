# Validation Corpus Specification — Research Foundation v0.1

**Status: WORKING — corpus design complete; title population/ground-truth labeling still in progress**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series will not validate its data model by importing millions of easy records. It will first prove the model against a deliberately adversarial corpus designed to break identity, release, localization, series, history, provenance and rights assumptions.

Target: **~1,000 labeled Works/entities/cases before V1 freeze.**

The corpus is a test suite, not a production catalogue seed.

## Principles

1. Difficult cases are over-sampled intentionally.
2. India receives deep coverage, but the corpus remains worldwide.
3. Historical and future productions both matter.
4. Correct identity boundaries matter more than title count.
5. Every benchmark case has expected outcomes, not merely a title list.
6. Source/legal constraints apply to corpus evidence too.
7. Corpus labels are reviewed when evidence is genuinely disputed; the expected result can be `CONFLICTING` rather than forcing one answer.

## Proposed allocation — 1,000 cases

### Geography/cinema tradition
- India: 350
- United States/Canada: 130
- UK/Ireland: 70
- Continental Europe: 100
- Japan: 70
- South Korea: 45
- Greater China/Hong Kong/Taiwan: 55
- Southeast Asia: 35
- Middle East/North Africa: 35
- Sub-Saharan Africa: 30
- Latin America/Caribbean: 45
- Australia/New Zealand/Oceania: 20
- Cross-national/co-productions/other targeted edge cases: 15

Allocation is deliberately not proportional to market size; it reflects product risk and India priority.

## India allocation — 350 cases

Target language/cinema slices, adjusted after source availability research:
- Hindi: 55
- Telugu: 55
- Tamil: 50
- Malayalam: 45
- Kannada: 35
- Bengali: 25
- Marathi: 20
- Punjabi: 12
- Gujarati: 10
- Odia: 8
- Assamese: 7
- Bhojpuri: 6
- Manipuri: 4
- Tulu/Konkani/other regional languages and multilingual edge cases: 18

### India era mix
- pre-1931/silent: 15
- 1931–1949: 30
- 1950–1969: 55
- 1970–1989: 60
- 1990–2009: 70
- 2010–2019: 65
- 2020–present released: 40
- active upcoming/shelved/cancelled: 15

Numbers can overlap with language categories and may be tuned to reach exact total.

## Global era mix

Across all territories, ensure meaningful representation of:
- silent era;
- early sound;
- wartime/post-war;
- 1950s–1970s national cinema movements;
- 1980s–1990s home-video era;
- 2000s digital transition;
- streaming era;
- currently announced/in-production projects.

## WorkKind mix

Target approximate cases:
- feature films: 550
- short films: 70
- TV/streaming series: 90
- seasons/parts requiring structure tests: 60
- individual episodes/specials with numbering/release complications: 100
- limited/miniseries: 35
- anthology works/segments: 25
- TV movies/special presentations: 25
- unfinished/lost/shelved/cancelled/future projects: 45

Some cases contribute to multiple categories; final corpus manifest will mark primary test purpose.

## Required edge-case buckets

### A. Identity collisions — minimum 75
- same title + different year;
- same title + same year + different country/language;
- translated/localized titles colliding;
- provider IDs merged/remapped;
- feature vs episode with same title;
- reboot vs revival ambiguity.

Expected assertions:
- distinct CAS IDs where appropriate;
- no false auto-merge;
- correct redirect if true duplicate.

### B. Dub vs remake vs multilingual production — minimum 80
- ordinary dub;
- cross-language remake;
- simultaneous language production;
- new adaptation from same literary source;
- localized voice cast;
- materially different language edit.

Expected assertions:
- correct Work/Version boundary;
- provenance-backed relationships;
- language/title/release contexts retained.

### C. Release complexity — minimum 100
- festival premiere then theatrical;
- overseas release before home territory;
- postponed dates;
- cancelled release;
- paid previews;
- re-release;
- restoration screening;
- streaming premiere;
- platform removal/re-addition;
- only year/month known historically.

### D. Alternate cuts/restorations — minimum 50
- director's cut;
- extended cut;
- censored cut;
- international cut;
- restoration/remaster;
- alternate runtime/certification.

### E. Historical scarcity/conflict — minimum 80
- lost/partially surviving film;
- uncertain premiere;
- incomplete credits;
- alternate historical spellings;
- archive holdings;
- conflicting scholarly sources.

Expected output can be UNKNOWN/CONFLICTING.

### F. Series structure — minimum 120
- standard seasons;
- streaming batch season;
- split season/Part 1 + Part 2;
- specials;
- absolute vs aired order;
- anthology series;
- limited series;
- revival/reboot;
- episode moved/re-numbered;
- platform-specific season grouping.

### G. People identity — minimum 75 person collision cases
- same names;
- mononyms;
- initials;
- stage-name change;
- credited-as spelling;
- multilingual names;
- mistaken duplicate across industries.

### H. Company identity — minimum 30
- production banner vs legal company;
- parent/subsidiary;
- company rename;
- distributor vs producer;
- streaming brand vs corporate owner.

### I. Upcoming lifecycle — minimum 50
- officially announced, no date;
- pre-production;
- filming;
- post-production;
- date changed;
- on hold;
- shelved;
- cancelled;
- revived;
- rumor that must remain Lead only.

These cases must be refreshed close to benchmark execution because future-production status changes.

### J. Localization/search — minimum 200 query/title cases
Scripts/queries must include:
- Telugu;
- Tamil;
- Devanagari;
- Malayalam;
- Kannada;
- Bengali;
- Gujarati/Gurmukhi/Odia and others;
- Japanese;
- Korean;
- Chinese scripts;
- Arabic;
- Cyrillic;
- Latin with diacritics.

Each Work can contribute multiple search queries.

### K. Artwork rights — minimum 50
- open-license image;
- public-domain historical image;
- provider-licensed image mock policy;
- no publishable artwork;
- expiring asset;
- localized poster;
- rejected scraped image;
- takedown case.

The expected result is rights state, not visual preference.

## Candidate anchor cases

The final corpus manifest will contain evidence-linked ground truth, but these are useful anchor candidates for stress testing.

### India
- `Raja Harishchandra` — early Indian cinema/history/naming.
- `Alam Ara` — early sound-era historical/survival metadata challenge.
- Satyajit Ray/Apu Trilogy titles — archival credits/releases/filmography.
- `Sholay` — long historical life, reissues/restoration/version context.
- `Roja` — multilingual/dubbed distribution and music metadata.
- `Baahubali: The Beginning` / `Baahubali 2` — multilingual production/release/franchise.
- `Eega` / localized language identity — multilingual/dub classification challenge.
- `Drishyam` and its Indian-language remake network — remake graph.
- `Vikram Vedha` Tamil/Hindi — remake identity.
- `Arjun Reddy` / `Kabir Singh` — cross-language remake.
- `Jersey` Telugu/Hindi — remake relationship.
- `KGF` films — original-language identity plus wide dubbed releases.
- `RRR` — global release/localization/awards-era metadata and multilingual distribution.
- modern Indian streaming series with split/season structures — final titles selected during refresh.
- current upcoming Telugu/Hindi/Tamil/Malayalam projects — select immediately before benchmark run using official evidence.

### Global
- `Seven Samurai` / `The Magnificent Seven` — remake relationship.
- `Infernal Affairs` / `The Departed` — adaptation/remake relationship.
- Korean `Oldboy` / US `Oldboy` — same title/remake collision.
- `Let the Right One In` / `Let Me In` — adaptation/remake.
- `Blade Runner` — multiple cuts.
- `Apocalypse Now` / `Redux` / later cut — version model.
- theatrical `Justice League` / `Zack Snyder's Justice League` — difficult version/work boundary benchmark.
- `Metropolis` — restoration/history.
- `Nosferatu` works across eras — same property/title/remake identity.
- `Doctor Who` — long-running series identity/revival/season numbering.
- `The Office` UK/US — related adaptation but distinct Series.
- `Money Heist / La casa de papel` — localized/international naming/platform structure.
- major anime properties with series/film/rebuild relationships — titles selected with source-backed expected relations.

Candidate anchors do not become benchmark ground truth until evidence is reviewed.

## Corpus manifest format

Create a machine-readable file later, e.g. `validation/corpus.yaml` or relational fixtures.

Each case should contain:

```yaml
case_id: CAS-VAL-0001
category:
  - identity
  - localization
entities:
  - label: source_record_a
  - label: source_record_b
expected:
  same_work: true
  work_kind: FEATURE_FILM
  relationship: null
  evidence_state: CONFIRMED
sources:
  - source_id: ...
notes: ...
```

For search cases:

```yaml
query: "..."
expected_entity: CAS-VAL-WORK-...
expected_top_k: 3
locale: te-IN
```

## Ground-truth review

Each identity-critical case should ideally be reviewed using:
- direct/official evidence where possible;
- at least one independent authoritative/curated source for difficult historical cases;
- human rationale for ambiguous version/work boundaries.

Ground truth may explicitly be:
- `UNRESOLVED`
- `CONFLICTING`

Such cases test that the engine refuses false certainty.

## Benchmark suites

### Identity suite
Measures auto-match precision/recall and false merges.

### Canonicalization suite
Feeds conflicting/superseding Claims and checks decisions.

### Release suite
Checks ReleaseEvent construction, projections and reschedules.

### Lifecycle suite
Checks production-event/current-state derivation.

### Localization/search suite
Checks title/name recall across scripts/transliterations.

### Provenance suite
Checks every expected canonical fact traces to eligible evidence.

### Rights suite
Checks unauthorized Assets never become publishable.

### Series suite
Checks hierarchy/order/reboot/special behavior.

## Pass metrics to define after baseline run

At minimum:
- auto-merge precision;
- auto-merge recall;
- false-merge count;
- canonical decision accuracy;
- release projection accuracy;
- lifecycle projection accuracy;
- search Top-1/Top-3 by script;
- P0 provenance coverage;
- asset rights-gate false-positive count;
- schema representation failures.

Policy direction: **zero known rights-gate false positives and near-zero/zero false automatic merges in the benchmark** are more important than maximum automation.

## Corpus versioning

The validation corpus is versioned and immutable by release:
- `v0.1-draft`
- `v0.2-labeled`
- `v1.0-freeze-baseline`

When real-world future projects change, create new expected-state snapshots rather than rewriting historical test evidence without history.

## Current completion state

Completed in this document:
- corpus architecture;
- target size;
- geographic/work-kind allocation;
- adversarial category requirements;
- expected manifest structure;
- anchor candidates;
- benchmark-suite design.

Still required before the Issue #1 `Validation corpus` item can be checked:
- populate the machine-readable ~1,000-case manifest;
- attach evidence/ground truth;
- execute baseline tests/prototypes;
- set numeric pass thresholds from measured results.
