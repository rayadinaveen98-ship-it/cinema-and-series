# Research Foundation v0.1

**Status: ACTIVE**  
**Started: 2026-09-12**

## Purpose

Research Foundation v0.1 exists to prevent Cinema and Series from repeating the failure pattern of building UI or ingestion around assumptions that later prove incorrect, incomplete, legally unusable, or too dependent on one provider.

No production implementation is authorized by this milestone.

## Primary research questions

### Market / product
1. What do IMDb, TMDB, Letterboxd, Trakt, JustWatch, OTTplay, BookMyShow, Rotten Tomatoes, Metacritic, Plex/Google discovery products, TheTVDB, Wikidata/Wikipedia, festival databases, certification bodies, and relevant regional products each solve well?
2. Where are their gaps specifically for Indian cinema and multilingual world cinema?
3. Which gaps are genuinely valuable versus merely different?
4. Which product capabilities depend on data we cannot legally or sustainably acquire?

### Coverage
1. How should "coverage" be measured by country, language, era, title type, and metadata dimension?
2. How do we represent lost films, uncertain dates, incomplete credits, unaired pilots, cancelled productions, shelved films, working titles, and partially documented historical works?
3. What benchmark corpora can reveal systematic gaps in India and globally?

### Sources
For every candidate source we must determine:
- exact fields available;
- historical depth;
- geographic/language coverage;
- upcoming-project coverage;
- access mechanism;
- update frequency;
- rate limits;
- attribution requirements;
- license/terms and commercial reuse constraints;
- artwork/media rights separately from metadata rights;
- reliability by field;
- failure modes;
- fallback/secondary sources.

### Identity and reconciliation
Research must challenge the model with:
- identical titles in different years/languages;
- spelling variants/transliterations;
- working titles that become final titles;
- remakes versus dubbed versions;
- alternate cuts versus separate works;
- anthology components;
- film-to-series adaptations;
- split/combined releases;
- regional/international naming differences;
- people sharing the same name;
- pseudonyms and stage names.

### Release modeling
We must validate the difference between:
- announcement date;
- scheduled release date;
- actual release date;
- festival premiere;
- world premiere;
- territory theatrical release;
- language-version release;
- digital/OTT release;
- physical release;
- re-release;
- restoration screening;
- cancellation/postponement.

### India-deep research
Priority topics:
- native script + romanization;
- language versus market versus production country;
- dubbing and multi-language simultaneous productions;
- remake graphs;
- CBFC certification structure and accessibility;
- theatrical schedules and regional distribution;
- OTT availability in India;
- historical regional cinema archives;
- music/lyricist/playback/choreography/action/craft credits;
- regional production-company identity;
- ambiguous marketing terms such as pan-India, bilingual, multilingual, and dubbed release.

## Validation corpus strategy

Before mass ingestion, create a deliberately difficult corpus of at least hundreds, later approximately 1,000, diverse records that stress the schema and reconciliation rules.

Candidate categories include:
- early silent films;
- lost/partially lost films;
- Satyajit Ray filmography;
- Telugu/Tamil/Malayalam/Kannada/Hindi historical and modern samples;
- Baahubali-like multi-language identity cases;
- Drishyam-like remake networks;
- RRR-like global release complexity;
- heavily dubbed commercial films;
- anime film/series relationships;
- long-running TV series;
- limited series;
- anthology series;
- streaming originals;
- cancelled/shelved/upcoming productions;
- festival-only titles;
- restorations/re-releases;
- alternate/director's cuts.

Exact titles and pass criteria remain OPEN until the research audit is complete.

## Required outputs before V1 freeze

1. `COMPETITOR_AUDIT.md`
2. `INDIA_GAP_ANALYSIS.md`
3. `GLOBAL_DATABASE_ANALYSIS.md`
4. `SOURCE_REGISTRY.md`
5. `SOURCE_LICENSING_MATRIX.md`
6. `SOURCE_TRUST_MODEL.md`
7. `DATA_FIELD_SOURCE_MATRIX.md`
8. complete domain/entity schema + ERD
9. claim/provenance model
10. identity and canonicalization specification
11. release and production lifecycle specifications
12. search/localization specification
13. architecture constitution + ADRs
14. information architecture + screen inventory
15. admin workflows
16. data-quality metrics and benchmark corpus
17. QA/acceptance matrix
18. master execution roadmap
19. frozen V1 contract

## Exit gate

Research Foundation v0.1 is complete only when the team can answer, with evidence:

- what data V1 will contain;
- where each class of data can come from;
- what reuse/licensing restrictions apply;
- how entities receive stable identity;
- how disagreements are preserved/resolved;
- how Indian-language/version/release complexity is represented;
- how source failure is tolerated;
- what V1 quality means quantitatively;
- exactly what will and will not be built.
