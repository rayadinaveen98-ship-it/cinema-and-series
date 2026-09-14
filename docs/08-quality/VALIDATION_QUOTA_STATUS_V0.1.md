# Validation Quota Status v0.1

**Status: ACTIVE**  
**Corpus size:** 115 evidence-seeded cases  
**Gold status:** not yet claimed

This file measures the first 115 cases against `VALIDATION_COHORT_QUOTAS.md`. It is intentionally blunt: the initial research corpus was designed to discover model defects, so it is not yet balanced enough to freeze V1.

| Primary cohort | Current | Target | Remaining |
|---|---:|---:|---:|
| India identity + multilingual/localization | 9 | 180 | 171 |
| Global film Work/Version/relationship | 20 | 100 | 80 |
| Release/territory/certification/availability | 5 | 120 | 115 |
| Series/season/episode/special structure | 29 | 140 | 111 |
| People/credits/roles/music identity | 21 | 100 | 79 |
| Organizations/companies/platform/rightsholders | 5 | 60 | 55 |
| Historical/archive/preservation/restoration | 8 | 100 | 92 |
| Upcoming/unreleased/production lifecycle | 10 | 70 | 60 |
| Source conflict/canonicalization/provenance | 6 | 60 | 54 |
| Search/transliteration/disambiguation | 2 | 70 | 68 |
| **Total** | **115** | **1,000** | **885** |

## Interpretation
The first 115 did their job: they exposed structural defects. They were **not** selected to mirror final quotas.

The largest immediate weaknesses are:
1. release/certification/territory depth;
2. Indian-language identity/localization breadth;
3. historical/archive coverage;
4. search/transliteration/disambiguation;
5. organization/rightsholder history.

Series structure is relatively well represented already and should not dominate the next tranches.

## Next-tranche allocation rule
Until the corpus reaches roughly 300 cases, new cases should preferentially come from the five weak areas above, especially India and historical/release intersections.

Suggested VC-0116..VC-0200 emphasis:
- 30 India identity/native-script/transliteration cases;
- 20 release/certification/territory cases;
- 15 historical/archive cases;
- 10 search/disambiguation cases beyond those already overlapping India;
- 5 organization/rightsholder cases;
- 5 documentary/short/festival-only cases that may count in the appropriate primary cohorts.

This is guidance, not an excuse to add weak evidence. A strong hard case in another quota may still be added when discovered.

## Required secondary audits
Primary cohorts alone are insufficient. Before 300 cases, add secondary classification for:
- geography/cinema industry;
- language;
- script;
- era;
- work type;
- evidence grade;
- risk level;
- released/upcoming/unreleased status.

That will allow automated quota reporting rather than manual estimates.

## Freeze warning
Current corpus size **must not** be described as 11.5% complete in quality terms. It is 115/1,000 by count only. Evidence upgrading, adjudication and machine-readable conversion remain separate dimensions of completion.
