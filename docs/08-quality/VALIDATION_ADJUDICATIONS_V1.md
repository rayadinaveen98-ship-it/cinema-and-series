# Validation Adjudications — V1

**Status: ACTIVE / AUTHORITATIVE OVERRIDES**  
**Date: 2026-09-14**

This file records decisions for validation cases that were originally seeded as OPEN or under-specified. The original tranche files remain historical research records; these adjudications supersede their old expected outcome/status where listed.

## VC-0010 — Doctor Who classic run vs 2005 revival

**Decision:** `GOLD_CANDIDATE / MODEL LOCKED`

Expected CAS result:
- classic run = separate Series Work;
- 2005 revival = separate Series Work;
- one shared Doctor Who program/franchise lineage;
- revival Series `REVIVAL_OF` / `CONTINUES` classic Series.

Evidence basis:
- official DoctorWho.tv history records original 1963 start and 2005 return/revival;
- official material distinguishes the Classic Era/new era.

Controlling spec: `docs/03-data/DOMAIN_ADJUDICATIONS_V1.md` Rule D.

---

## VC-0061 — Kill Bill Vol. 1 / Vol. 2 / The Whole Bloody Affair

**Decision:** `GOLD_CANDIDATE / MODEL LOCKED`

Expected CAS result:
- Volume 1 = independent Work;
- Volume 2 = independent Work;
- The Whole Bloody Affair = distinct `COMBINED_PRESENTATION` / `COMPILATION_DERIVATIVE` Work;
- combined Work links to both volumes with `COMPILATION_CONTAINS` / `DERIVED_FROM`-class relationships;
- no destructive merge.

Evidence upgrade:
- Lionsgate official materials describe The Whole Bloody Affair as uniting Volume 1 and Volume 2 into one unrated epic and include additional/new anime material;
- Lionsgate home-media release independently describes it as one complete director's cut.

Controlling spec: `DOMAIN_ADJUDICATIONS_V1.md` Rule B.

---

## VC-0064 — The Disappearance of Eleanor Rigby: Him / Her / Them

**Decision:** `GOLD_CANDIDATE / MODEL LOCKED`

Expected CAS result:
- Him = Work;
- Her = Work;
- Them = separate derived/re-edited Work;
- Him and Her linked as alternate-perspective Works;
- Them linked as derived/combined from material in Him + Her;
- one project/collection groups all three.

Evidence upgrade:
- Dreambridge Films describes the project as two movies, HIM and HER, told from different perspectives, and separately says audiences can experience three versions: HER, HIM and THEM.

Controlling spec: `DOMAIN_ADJUDICATIONS_V1.md` Rule C.

---

## VC-0095 — Money Heist original broadcaster vs Netflix structure

**Decision:** `GOLD_CANDIDATE / MODEL LOCKED; RECUT EVIDENCE STILL SUBJECT TO SOURCE UPGRADE`

Expected CAS result:
- one Series Work;
- original Antena 3 broadcast StructureEdition;
- Netflix international Part/re-edit StructureEdition;
- provider-specific episode content units map through explicit `ContentUnitMapping`;
- later Netflix-produced continuation stays under same Series Work;
- no duplicate Series created because episode boundaries changed.

Evidence:
- Antena 3 documents the original run and its 15 broadcast episodes;
- Netflix currently presents one Money Heist Series in five Parts;
- reputable/reference material documents the initial 15 episodes being recut into 22 shorter Netflix episodes.

Controlling spec: `DOMAIN_ADJUDICATIONS_V1.md` Rule F.

---

## VC-0097 — Twin Peaks original vs 2017 limited event series

**Decision:** `GOLD_CANDIDATE / MODEL LOCKED`

Expected CAS result:
- original Twin Peaks = Series Work A;
- 2017 SHOWTIME limited event series = Series Work B;
- Series B `CONTINUES` Series A;
- shared Twin Peaks franchise/program lineage;
- the consumer UI may group them, but season numbering does not force one Series ID.

Evidence upgrade:
- SHOWTIME/Paramount official press materials call the 2017 production a `new` 18-part limited event series, explicitly separate the original two seasons, and state that the new series picks up twenty-five years later.

Controlling spec: `DOMAIN_ADJUDICATIONS_V1.md` Rule E.

# Adjudication rule

When an old tranche file and this file conflict, this file controls unless a later superseding adjudication/ADR is recorded.

These cases must also be represented in the machine-readable validation manifests before final V1 freeze.