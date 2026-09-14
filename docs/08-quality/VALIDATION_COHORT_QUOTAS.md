# Validation Corpus — Stratified Quotas

**Status: WORKING**  
**Target:** ~1,000 gold/adjudicated hard cases before V1 freeze

## Purpose
The number `1,000` has no value if the corpus is padded with easy duplicate examples. This document defines a stratified benchmark so Cinema and Series is tested across the domains most likely to break a worldwide, India-deep cinema/series database.

Each case receives exactly one **primary cohort** for quota accounting and any number of secondary tags. This prevents double-counting the same case toward the 1,000 total while still acknowledging that one case can stress several systems.

# Primary cohort quotas — total 1,000

| Primary cohort | Target | Focus |
|---|---:|---|
| India identity + multilingual/localization | 180 | original/dub/remake, multilingual shoots, scripts, regional title identity |
| Global film Work/Version/relationship | 100 | remake/adaptation/reboot/cuts/combined/split/compilation |
| Release/territory/certification/availability | 120 | premieres, theatrical, OTT, re-release, postponements, certifications, territories |
| Series/season/episode/special structure | 140 | revivals, seasons, parts/volumes, episode orders, remixes, specials |
| People/credits/roles/music identity | 100 | same-name people, pseudonyms, credited-as, craft/music role semantics |
| Organizations/companies/platform/rightsholders | 60 | mergers, acquisitions, renames, subsidiaries, distributors/platforms |
| Historical/archive/preservation/restoration | 100 | lost/fragmentary works, uncertain years, restoration/reconstruction/source elements |
| Upcoming/unreleased/production lifecycle | 70 | announced, working titles, filming, delayed, shelved, cancelled, revived projects |
| Source conflict/canonicalization/provenance | 60 | competent-source disagreement, supersession, evidence authority, review routing |
| Search/transliteration/disambiguation | 70 | native scripts, Romanization, aliases, collisions, fuzzy/phonetic discovery |
| **Total** | **1,000** | |

A case may have secondary tags spanning multiple cohorts, but only its primary cohort counts toward the total.

# India minimums

At least **350 of 1,000** cases must materially test Indian cinema/series data rather than merely use an Indian title as decoration.

Within the India subset, minimum representation:

| Dimension | Minimum |
|---|---:|
| Telugu | 55 |
| Tamil | 55 |
| Malayalam | 45 |
| Kannada | 35 |
| Hindi | 55 |
| Bengali | 25 |
| Marathi | 20 |
| Other Indian languages combined | 60 |

`Other Indian languages` should include meaningful samples from languages/cinemas such as Assamese, Odia, Punjabi, Gujarati, Bhojpuri, Manipuri, Konkani, Tulu and others where evidence is available. These are minima, not a claim that all industries are equally sized.

At least:
- 90 India cases must involve pre-2000 works;
- 35 must involve pre-1980 works;
- 20 must involve silent/early-sound/archival edge cases;
- 80 must stress native-script/transliteration/title localization;
- 70 must stress dub/remake/multilingual identity;
- 50 must stress Indian music/craft credits or culturally important crew roles.

# Global breadth minimums

Beyond India, include at least:
- 120 US/Canada cases;
- 80 European cases across multiple countries;
- 70 East Asian cases, including Japan/Korea/China-related cinema/series identity;
- 40 Southeast Asian cases;
- 35 Latin American cases;
- 30 African cases;
- 25 Middle Eastern cases;
- 30 Australia/New Zealand/Oceania cases;
- multinational/co-production cases may count toward a dedicated cross-region tag but not erase regional breadth.

These are diversity floors, not population/industry rankings.

# Era quotas

The corpus must not become a 2015–2026 streaming-app test set.

Minimums:
- before 1930: 35
- 1930–1949: 55
- 1950–1969: 85
- 1970–1989: 120
- 1990–2009: 180
- 2010–2019: 220
- 2020 onward: 220
- upcoming/unreleased without release year: at least 70 lifecycle cases across the corpus

Cases can be tagged by multiple relevant years when they test long histories, but each case gets a primary era for quota accounting.

# Format/type breadth

Minimum cases materially involving:
- feature films: 500
- short films: 50
- series: 160
- seasons/episodes/specials: 120
- anthology components: 30
- documentaries/nonfiction: 45
- animation: 60, of which anime <= 40 so anime does not stand in for all animation
- television films/direct-to-video/web specials: 25
- unreleased/unfinished/cancelled works: 35
- restored/reconstructed/lost/fragmentary works: 70

These tags overlap primary cohort counts.

# Risk quotas

At least:
- 150 `critical` cases — identity merge/split decisions with cascading consequences;
- 300 `high` cases — Work/Version/relationship/release decisions;
- remaining cases may be medium/low but must still test a meaningful rule.

A trivial title spelling variant does not qualify as a hard case unless it creates a real collision or script/transliteration ambiguity.

# Evidence quotas

Before final gold freeze:
- 100% cases have at least one competent source;
- 100% critical cases have authoritative or independently corroborated evidence suitable for the decision;
- >= 85% of all gold cases include at least one A or B evidence item;
- no critical case remains gold solely on an uncorroborated generic reference page;
- known source disagreement is represented, not hidden to improve benchmark scores.

# Adjudication quotas

Before V1 freeze:
- 100% critical cases adjudicated;
- 100% OPEN Work-vs-Version / remake-vs-adaptation / merge-vs-split decisions adjudicated or explicitly deferred outside V1 scope;
- >= 95% of all corpus cases gold; remaining <= 5% may be `gold_candidate` only if they do not block a frozen V1 behavior;
- zero unresolved model defect may invalidate a critical V1 entity relationship.

# Anti-padding rules

The following do **not** count as independent hard cases merely to increase volume:
- ten language dubs of one film testing the identical already-covered rule;
- dozens of normal sequels with no ambiguity;
- random popular titles whose metadata is straightforward;
- title spelling variants with no collision/search challenge;
- repeated provider records that exercise the same exact identity outcome without a new edge condition.

A repeated pattern counts only when it tests a new language/script/era/source/provider/rule interaction or provides statistically useful false-merge/false-split coverage.

# First-100 audit
The existing VC-0001..VC-0100 corpus is a **research seed**, not yet quota-compliant gold. Its purpose was to expose model defects. From VC-0101 onward, expansion should follow this stratification, while earlier cases are reclassified into primary cohorts and upgraded to the same standard.

# Freeze gate
Reaching 1,000 rows is not sufficient. V1 freezes only when:
1. primary quotas are met;
2. geography/era/type floors are met;
3. evidence rules are met;
4. critical cases are adjudicated;
5. machine-readable assertions exist;
6. benchmark execution meets the QA pass thresholds;
7. defects discovered by the corpus are resolved in specs/ADRs or explicitly deferred outside V1.
