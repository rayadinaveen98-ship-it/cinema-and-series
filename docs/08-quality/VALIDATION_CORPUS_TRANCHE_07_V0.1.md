# Validation Corpus Tranche 07 — Bengali/Marathi Identity, Source Works & Chronology

**Status: RESEARCH / GOLD-CANDIDATE MIX**  
**Date: 2026-09-14**  
**Cases:** VC-0136..VC-0144

## Purpose

This tranche targets underweighted Bengali/Marathi, historical, search/identity, source-work and release/certification rules. It deliberately favors cases that can expose schema/rule defects instead of straightforward popular-title metadata.

## Cases

### VC-0136 — Pather Panchali film and novel are distinct entities
Wikidata models the 1955 Satyajit Ray film separately from Bibhutibhushan Bandyopadhyay's 1929 literary work of the same Bangla title. The film is explicitly based on the literary work. CAS must create an audiovisual Work and an `ExternalCreativeWork`, linked by adaptation/source relationship rather than merging by title.

Evidence:
- https://www.wikidata.org/wiki/Q622380
- https://www.wikidata.org/wiki/Q2948187

### VC-0137 — Aparajito 1956 and Aparajito 2022 are separate Bengali Works
Two Bengali films share the English title `Aparajito`: Satyajit Ray's 1956 film and Anik Dutta's 2022 film. Same title + same original language is not identity evidence strong enough to merge; year/director/external IDs must disambiguate.

Evidence:
- https://www.wikidata.org/wiki/Q622382
- https://www.wikidata.org/wiki/Q112054511

### VC-0138 — Shwaas certification chronology is distinct from film publication chronology
Wikidata records `Shwaas` as a 2004 Marathi film while also carrying a CBFC U certificate ID with point-in-time 26 December 2003. CAS must represent certification separately from release/publication; an earlier certificate date must not rewrite film year to 2003.

Evidence:
- https://www.wikidata.org/wiki/Q7505812

### VC-0139 — Killa conflicting original-language signals require review
Wikidata records Marathi as an original language for the 2015 film `Killa`, while also carrying a Hindi original-language statement sourced from a different imported dataset. CAS must preserve the competing claims and avoid silently treating the film as a simultaneous Marathi/Hindi production without stronger evidence.

Evidence:
- https://www.wikidata.org/wiki/Q19824745

### VC-0140 — Nayak / The Hero / Nayak: The Hero are Name forms of one Work
The 1966 Satyajit Ray film has Bangla title `নায়ক` and English aliases `The Hero` and `Nayak: The Hero`. These are searchable/localized/alternate Name forms of one audiovisual Work, not separate films.

Evidence:
- https://www.wikidata.org/wiki/Q639604

### VC-0141 — Meghe Dhaka Tara alias and trilogy membership are independent semantics
The 1960 film has Bangla title `মেঘে ঢাকা তারা`, English alias `The Cloud-Capped Star`, and membership in Ritwik Ghatak's `Partition Trilogy`. Alias identity and collection/trilogy relationship must coexist without creating duplicate Works or turning the trilogy into the film's identity.

Evidence:
- https://www.wikidata.org/wiki/Q1199763

### VC-0142 — Charulata and Nastanirh are distinct source/film entities
The 1964 film `Charulata` (`চারুলতা`) is modeled as based on `Nastanirh`, a separate creative source work. CAS must preserve source-work identity separately and link the film through adaptation/source semantics.

Evidence:
- https://www.wikidata.org/wiki/Q639597

### VC-0143 — Mahanagar Bangla/localized names resolve one Work
The 1963 Satyajit Ray film appears as English `Mahanagar` and Bangla sitelink `মহানগর (চলচ্চিত্র)`. Search/localization layers may index both, while the canonical audiovisual Work remains one identity.

Evidence:
- https://www.wikidata.org/wiki/Q177438

### VC-0144 — Harishchandrachi Factory performer and depicted historical person remain distinct identities
Wikidata records Nandu Madhav as cast, with character role Dadasaheb Phalke. CAS credit modeling must keep the performer Person identity separate from the represented historical Person/role target; role text/character mapping must never merge the actor with the person portrayed.

Evidence:
- https://www.wikidata.org/wiki/Q5657943

## Model implications

This tranche reinforces:
- same title and language are not sufficient for Work identity;
- literary/source creative works are distinct from audiovisual Works;
- certification chronology is separate from release chronology;
- conflicting source claims remain explicit until adjudicated;
- alternate/localized titles remain Names, not Works;
- franchise/trilogy/collection membership is a relationship, not identity;
- performer identity and portrayed historical-person/role identity are separate.
