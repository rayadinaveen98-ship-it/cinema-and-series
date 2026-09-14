# Semantic Binding Migration 06 v0.1

## Accepted CI
GitHub Actions run `34849577693` is GREEN.

## Scope
`validation/semantic/bindings-015.jsonl` migrates **17 cases / 34 assertions** spanning series specials, person-name/pseudonym identity, production-country semantics, provider structure editions and continuation lineage.

Gold/reference-enabled cases:
- VC-0084 Alan Smithee credited-string identity rule
- VC-0085 Roderick Jaynes pseudonym -> Joel and Ethan Coen
- VC-0090 The Lunchbox production countries
- VC-0091 Gandhi production countries
- VC-0092 The Namesake production countries
- VC-0093 All We Imagine as Light source-backed country claims
- VC-0095 Money Heist provider structure editions
- VC-0097 Twin Peaks original vs 2017 continuation

Binding-only evidence-upgrade cases:
- VC-0081 Doctor Who holiday specials
- VC-0082 The Abominable Bride
- VC-0083 Euphoria bridge specials
- VC-0086 Michael Keaton / Michael Douglas name collision
- VC-0087 Emma Stone / Emily Stone
- VC-0088 Rajinikanth / Shivaji Rao Gaekwad
- VC-0089 Mammootty legal/professional names
- VC-0094 Monsoon Wedding country-attribution conflict
- VC-0096 Arrested Development Season 4 remix

## Metrics
Before:
- runtime-ready: 303
- needs binding: 174
- reference cases: 88
- reference assertions: 227 PASS

After:
- runtime-ready: **337 / 481**
- needs binding: **140**
- manual/specialized: **4**
- reference cases: **96**
- reference assertions: **243 / 243 PASS**

## Major milestone
The original semantic-binding debt was 280 assertions. It is now **140**: exactly half of the original debt has been converted into explicit, machine-executable bindings.

Cumulative movement from the starting semantic baseline:
- runtime-ready: **197 -> 337** (+140)
- binding debt: **280 -> 140** (-140)
- reference cases: **56 -> 96** (+40)
- reference assertions: **154 -> 243 PASS** (+89)

No corpus assertions, source evidence, risk levels or case statuses were removed or weakened to reach this milestone.
