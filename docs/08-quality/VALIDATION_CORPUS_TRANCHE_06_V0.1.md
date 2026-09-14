# Validation Corpus Tranche 06 — Gujarati/Punjabi Identity, Release & Certification

**Status: RESEARCH / GOLD-CANDIDATE MIX**  
**Date: 2026-09-14**  
**Cases:** VC-0126..VC-0135

## Purpose

This tranche deliberately targets weak V1 cohorts: Gujarati/Punjabi cinema, native-script identity, same-title collisions, release-vs-certification semantics, historical source conflict, adaptation identity and restoration/re-release behavior.

## Cases

### VC-0126 — Hellaro: award event must not overwrite film release identity
Wikidata models `Hellaro` as a 2018 Gujarati film with native title `હેલ્લારો`; PIB's 2019 National Film Awards announcement records it as the Best Feature Film winner. CAS must preserve film publication/release chronology independently from later award-event dates.

Evidence:
- https://www.wikidata.org/wiki/Q66385047
- https://www.pib.gov.in/PressReleasePage.aspx?PRID=1581667

### VC-0127 — Last Film Show / Chhello Show / છેલ્લો શો are one Work identity
Wikidata records English label `Last Film Show`, alias `Chhello Show`, Gujarati title `છેલ્લો શો`, Gujarati original language and a 10 June 2021 Tribeca publication event. Public references also record later India theatrical release in 2022. CAS must preserve one Work with multiple Names and release events rather than duplicate Works.

Evidence:
- https://www.wikidata.org/wiki/Q107259079
- https://www.pib.gov.in/PressReleasePage.aspx?PRID=1951758

### VC-0128 — Chann Pardesi contains competent source conflict on year/language
Wikidata currently carries publication-year statements for both 1981 and 1980 and language signals for Punjabi plus a Hindi statement imported from a different Wikimedia source. CAS must preserve the conflict and route high-risk canonicalization to review rather than invent exact certainty.

Evidence:
- https://www.wikidata.org/wiki/Q5072208

### VC-0129 — Nanak Naam Jahaz Hai 1969 and 2024 are different Works
The 1969 Punjabi film and a separately certified/released 2024 Punjabi film share effectively the same title. CBFC's 2024 list identifies the newer film separately, while the older film has distinct director/cast/history. Search may collocate them; identity must never auto-merge them.

Evidence:
- https://www.wikidata.org/wiki/Q6962384
- https://www.cbfcindia.gov.in/cbfcAdmin/assets/pdf/List_of_feature_films_certified_2024.pdf
- https://www.imdb.com/title/tt32400206/

### VC-0130 — Nanak Naam Jahaz Hai 2024 certification date is not theatrical release date
CBFC lists a 31 January 2024 certification record for the 2024 Punjabi film; a later theatrical-release source records 24 May 2024. CAS requires a Certification fact/event and a separate ReleaseEvent.

Evidence:
- https://www.cbfcindia.gov.in/cbfcAdmin/assets/pdf/List_of_feature_films_certified_2024.pdf
- https://www.rottentomatoes.com/m/nanak_naam_jahaz_hai_2024

### VC-0131 — Warning 2 certification/classification vs release chronology
CBFC lists `WARNING 2` with certification date 31 January 2024, A classification and certification runtime; Saregama's verified trailer states cinemas on 2 February 2024 and BBFC separately records its UK classification/release context. Certification dates must not populate theatrical release dates.

Evidence:
- https://www.cbfcindia.gov.in/cbfcAdmin/assets/pdf/List_of_feature_films_certified_2024.pdf
- https://www.youtube.com/watch?v=JKb-gu3J608
- https://www.bbfc.co.uk/release/warning-2-q29sbgvjdglvbjpwwc0xmde5mdey

### VC-0132 — Marhi Da Deeva novel and film are separate creative entities linked by adaptation
The 1964 Punjabi novel `ਮੜ੍ਹੀ ਦਾ ਦੀਵਾ` and the 1989 Punjabi film of the same title must not share one CAS audiovisual Work identity. The film adapts the literary source; CAS should preserve an `ExternalCreativeWork` source identity and an adaptation relationship.

Evidence:
- https://en.wikipedia.org/wiki/Marhi_Da_Deeva_(novel)
- https://en.wikipedia.org/wiki/Marhi_Da_Deeva_(film)

### VC-0133 — Bhavni Bhavai native title/alias remain one Work
Wikidata identifies one 1980 Gujarati film with English label `Bhavni Bhavai`, alias `Andher Nagari`, and Gujarati sitelink `ભવની ભવાઈ (ચલચિત્ર)`. These Name forms must resolve the same Work; aliases cannot create duplicate Works.

Evidence:
- https://www.wikidata.org/wiki/Q4901571

### VC-0134 — Carry On Jatta remake lineage must not collapse across languages
The 2012 Punjabi film is reported as having later remakes in Odia, Telugu and Bengali contexts. Even where titles or plot lineage are close, each remake is a separate Work connected by explicit remake/adaptation relationships; the Punjabi original's CAS identity remains distinct.

Evidence:
- https://www.wikidata.org/wiki/Q5046795
- https://en.wikipedia.org/wiki/Carry_On_Jatta

### VC-0135 — Nanak Naam Jahaz Hai 1969 restoration/re-release does not create a new historical film
Reference evidence records the original 1969 Punjabi film and a later digitally enhanced/restored presentation prepared for a 2015 re-release. CAS must preserve the original Work identity and model later restoration/version/re-release history separately.

Evidence:
- https://en.wikipedia.org/wiki/Nanak_Nam_Jahaz_Hai
- https://www.imdb.com/title/tt0142681/

## Model implications

This tranche reinforces:
- certificate/classification dates are not release dates;
- same title + language does not imply same Work;
- aliases/native-script forms do not create Works;
- later awards do not rewrite original publication chronology;
- competent source disagreement remains explicit;
- literary source works are not audiovisual Works;
- restoration/re-release history does not replace original film identity.

Cases relying mainly on general reference sources remain `evidence_upgrade_needed` until stronger institutional/first-party corroboration is added.