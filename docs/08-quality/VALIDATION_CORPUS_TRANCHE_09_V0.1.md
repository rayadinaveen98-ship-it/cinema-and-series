# Validation Corpus Tranche 09 v0.1

Status: ACCEPTED BY CI

This tranche adds `VC-0156..VC-0165` and search queries `SQ-0184..SQ-0213`.

## Purpose

Attack three measured deficits from the quota/floor audits:

1. organizations / platforms / rightsholders;
2. upcoming / unreleased lifecycle and release precision;
3. Devanagari Hindi/Marathi search depth and same-title disambiguation.

## Hard cases

### Organization and role separation

- `VC-0156` — Dharma Productions can legitimately carry production and distribution roles while internal brands remain separately modeled identities.
- `VC-0157` — Dharmatic Entertainment and Dharma Productions are linked organizations, not aliases that should auto-merge.
- `VC-0158` — Nadaaniyan keeps Dharmatic production credit separate from Netflix release-platform semantics.
- `VC-0159` — Accused keeps Dharma Productions production credit separate from its exact Netflix release event.

### Upcoming lifecycle / type identity

- `VC-0160` — Musafir Cafe is a Series with a 2026 window; no exact date may be invented.
- `VC-0161` — Lust Stories 3 is an anthology Film with four chapters, not a television Series/Season.
- `VC-0162` — Hum Hindustani is an upcoming Film with only a 2026 window.
- `VC-0163` — Operation Safed Sagar is an upcoming Series with only a 2026 window.
- `VC-0164` — Family Business is an upcoming Series; director and creator credits remain distinct.
- `VC-0165` — Mitti De Putt has an exact 18 September 2026 release date while Dharma's catalogue supplies a distribution role; distribution must not be promoted to producer credit.

## Devanagari search tranche

`SQ-0184..SQ-0213` add Hindi/Marathi native-script, Latin and qualified searches for:

- Sholay / शोले;
- Dangal / दंगल;
- Mother India / मदर इण्डिया;
- Swades / स्वदेश;
- Anand / आनन्द;
- Masaan / मसान;
- Deewaar 1975 / दीवार;
- Deewaar 2004 / दीवार;
- Natsamrat / नटसम्राट;
- Harishchandrachi Factory / हरिश्चंद्राची फॅक्टरी.

The two Deewaar Works deliberately share the same Hindi query to ensure search returns/disambiguates both instead of corrupting identity.

## Evidence policy

Lifecycle/organization cases use first-party Netflix or Dharma evidence. Search labels use Wikidata as the open structured benchmark source. Generated qualified strings remain search-only truth.

## Accepted CI result

Workflow run `34839899006` passed all four validation gates.

Accepted counts after this tranche:

- hard cases: **165**;
- hard-case assertions: **371**;
- machine-readable parity: **165/165**;
- search queries: **213/500**;
- Devanagari script queries: **29/80**.

Primary quota improvements relative to the prior accepted state:

- organizations/rightsholders: **9 -> 12 / 60**;
- upcoming lifecycle: **12 -> 17 / 70**;
- release/certification/availability: **13 -> 15 / 120**.

## Model conclusions reinforced

- Organization role is temporal/contextual; organization identity is not role identity.
- Platform, producer and distributor are independent relationships.
- `Coming 2026` is a release window, not permission to synthesize a date.
- Consumer-friendly franchise/anthology branding does not override entity kind.
- Same native title never justifies identity merge without disambiguating evidence.
