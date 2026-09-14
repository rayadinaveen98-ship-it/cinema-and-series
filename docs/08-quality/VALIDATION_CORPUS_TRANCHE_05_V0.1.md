# Validation Corpus Tranche 05 — India Identity, Language, Release & Historical Versions

**Status: ACTIVE / EVIDENCE-SEEDED**  
**Cases:** VC-0116..VC-0125  
**Machine-readable mirror:** `validation/corpus-tranche-007.jsonl`

This tranche deliberately targets underweighted India-specific dimensions rather than adding more generic title records.

## VC-0116 — Mayabazar (1957) Telugu/Tamil simultaneous production
Tests whether one underlying film project with simultaneous Telugu/Tamil realizations is represented without misclassifying the Tamil realization as a remake or ordinary later dub.

Evidence includes Wikidata's 1957 Work record and Wikimedia's Tamil-version record/description noting simultaneous Telugu/Tamil shooting with cast differences. Final gold status still benefits from stronger archival/production-history corroboration.

## VC-0117 — Mayabazar language-version release chronology
Tests distinct release events for Telugu and Tamil language realizations rather than a single overwritten `release_date`.

The commonly documented dates are 27 March 1957 for Telugu and 12 April 1957 for Tamil. Because current direct evidence is mostly reference-level, this remains an evidence-upgrade case.

## VC-0118 — Sankarabharanam 1979/1980 year conflict
Wikidata currently exposes both 1979 and 1980 publication-date claims for the same Work. CAS must preserve the competing evidence/history and must never create two films merely because sources/year conventions disagree.

## VC-0119 — Parasakthi (1952) language-source conflict
Wikidata currently exposes Tamil and Telugu as original-language claims, while common film-reference evidence describes the 1952 release as Tamil-language. This is a canonicalization/review-routing test: do not silently promote every source language claim or infer a second Work/version without evidence.

## VC-0120 — Court (2014) multilingual dialogue within one Work
Official distributor/festival records list Marathi, Hindi, English and Gujarati. Multiple spoken/original-production languages must not become separate Works or dubbed Versions automatically.

## VC-0121 — Court festival year vs India theatrical year
The film belongs to the 2014 Venice festival cycle but reached Indian theatrical release in 2015. CAS needs multiple ReleaseEvents and must avoid a single date field that erases either history.

## VC-0122 — Chemmeen film vs Chemmeen novel
The 1965 Malayalam film and its literary source are distinct entities with the same name. Search/identity must distinguish audiovisual Work from `ExternalCreativeWork`, while the film can carry an adaptation/based-on relationship.

## VC-0123 — Sholay native Hindi title vs localized Bangla form
`शोले` is the Hindi title of the 1975 Work; a Bangla pronunciation/localized form also exists in structured source material. Localized/native search forms must not create another film or change original-language identity.

## VC-0124 — The Disciple multilingual festival metadata
La Biennale lists Marathi, Hindi, English and Bengali for the 2020 film. This reinforces that language is multi-valued/contextual and does not imply multiple Versions by itself.

## VC-0125 — Mughal-e-Azam 2004 colourised re-release
The 1960 classic was restored/colourised and theatrically re-released in 2004 with reworked sound and a different runtime. CAS should model the 2004 presentation as a materially distinct Version + ReleaseEvent of the existing Work, not as a new movie identity.

# Findings reinforced

1. **Language count does not determine Work count.** Simultaneously shot language realizations and multilingual dialogue need explicit semantics.
2. **Release year is a projection, not identity.** Festival, territory and language-version dates can legitimately differ.
3. **Historical disagreement is data.** 1979/1980-style year conflicts must remain explainable.
4. **Same title across media types needs WorkKind-aware identity/search.** A novel and film are not duplicates.
5. **Restoration/colourisation/re-editing usually belongs under Version + ReleaseEvent unless evidence establishes a new independent Work.**

These ten cases increase the evidence-seeded corpus from 115 to 125. They are not automatically `gold`; individual evidence grades/statuses remain explicit in the JSONL manifest.
