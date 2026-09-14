# Validation Corpus Tranche 08 v0.1

**Status:** WORKING / CI-VALIDATED  
**Cases:** VC-0145..VC-0155  
**Search tranche:** SQ-0154..SQ-0183  
**Accepted CI state after tranche:** 155 cases / 351 hard-case assertions / 183 search queries

## Purpose

This tranche intentionally targets cohorts that remained underweight after the 144-case milestone: historical/archive/preservation, organizations/rightsholders, upcoming/unreleased lifecycle, India identity and South-Indian multilingual search.

It does not add routine title records merely to increase the corpus count.

## Cases added

### VC-0145 — Thampu restoration provenance
The 1978 Malayalam Work remains the same Work. The Film Heritage Foundation restoration is modeled as a distinct Version with source-element provenance, and its Cannes Classics 2022 screening is a ReleaseEvent of that restored Version rather than a replacement for the original release history.

### VC-0146 — Kummatty restoration provenance
The restored presentation is a Version of the 1979 Work. NFAI release prints are preserved as restoration source elements; the absence of surviving original camera negatives remains an archival fact. The 2021 Bologna screening does not rewrite the original release year.

### VC-0147 — Ghatashraddha restoration source element
The restoration is modeled separately from the 1977 Kannada Work. The original camera negative preserved at NFDC-NFAI is recorded as a source element/holding fact.

### VC-0148 — AVM company history vs studio milestones
AVM Productions company history and the establishment of studio grounds/facilities are separate organization-history facts. A studio milestone may not silently overwrite organization inception.

### VC-0149 — Ayan producer vs distributor roles
AVM Productions and Sun Pictures are distinct organizations with different role edges on the same film. `production_company` and `distributed_by` are never interchangeable.

### VC-0150 — YRF distribution does not imply production
YRF's first-party distribution catalogue lists *Jawan* as an outside-banner film it distributed internationally. A territory-scoped distributor relationship must never be promoted into a production-company claim.

### VC-0151 — YRF inception vs distribution-division launch
YRF's 1970 company formation and its 1997 distribution-division launch are distinct organization-history events.

### VC-0152 — Sivaji 3D 2012
AVM's own history states that the 2007 *Sivaji – The Boss* was remastered/post-converted for a 3D release in 2012. CAS therefore models one underlying Work, a distinct 3D Version, and a 2012 re-release event.

### VC-0153 — Takshakudu 2026 announcement
Netflix officially lists *Takshakudu* as coming in 2026 without an exact date in the cited slate. CAS may store a 2026 release window and announced/upcoming lifecycle state, but must not invent a day/month.

### VC-0154 — Legacy 2026 series announcement
Netflix officially lists *Legacy* as a Tamil series coming in 2026. It remains a Series entity and carries a year-level release window unless stronger dated evidence appears.

### VC-0155 — Manichitrathazhu / Chandramukhi
The 1993 Malayalam *Manichitrathazhu* and 2005 Tamil *Chandramukhi* are separate Works. The relationship is preserved as `based_on` from the available evidence; the cross-language relationship must not be collapsed into a dub identity.

## Search tranche SQ-0154..SQ-0183

Thirty search assertions were added across the four weakest South-Indian language floors:

- Telugu: Sankarabharanam, Rangasthalam;
- Tamil: Nayagan/Nayakan, Iruvar, Andha Naal, Chandramukhi;
- Malayalam: Elippathayam/Rat-Trap, Thampu/The Circus Tent, Kumbalangi Nights, Manichitrathazhu;
- Kannada: Mungaru Male, Om.

The queries deliberately mix native script, Latin labels, sourced aliases, qualified collisions and date/title ambiguity.

## Accepted CI result

The validation workflow passed all four gates:

1. hard-case manifest schema validation;
2. primary-cohort quota audit;
3. multilingual search-manifest validation;
4. search-floor progress audit.

Accepted state:

- **155** hard cases;
- **351** hard-case assertions;
- **107** gold candidates;
- **47** evidence-upgrade cases;
- **1** open adjudication;
- **64** critical-risk cases;
- **183 / 500** pre-freeze search queries.

Primary-cohort progress after this tranche:

- India identity + multilingual/localization: **16 / 180**
- Release/territory/certification: **13 / 120**
- Organizations/companies/platforms/rightsholders: **9 / 60**
- Historical/archive/preservation: **12 / 100**
- Upcoming/unreleased/lifecycle: **12 / 70**
- Search/transliteration/disambiguation: **6 / 70**

South-language search-floor progress after this tranche:

- Telugu: **11 / 60**
- Tamil: **11 / 60**
- Malayalam: **8 / 50**
- Kannada: **7 / 50**

## Research implication

The restoration cases reinforce a core CAS rule: **preservation state, source elements, restored Versions and restoration screenings are not substitutes for the original Work or its historical release events.**

The AVM/YRF cases reinforce another core rule: **organization identity, company history, production roles, distribution roles, territories, divisions and facilities are independent facts and relationships.**

The Netflix cases reinforce the lifecycle rule: **an official year-level announcement is evidence for an upcoming Work/Series and release window, not permission to fabricate an exact release date.**

## Next target

The next tranches should continue to prioritize:

1. India identity/localization;
2. release/certification/version history;
3. historical/archive/preservation;
4. organizations/rightsholders;
5. upcoming lifecycle;
6. Telugu/Tamil/Malayalam/Kannada and Devanagari search floors.
