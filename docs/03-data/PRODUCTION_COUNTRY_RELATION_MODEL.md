# Production Country / Territory Relation Model

**Status: WORKING**  
**Derived from validation cases:** VC-0090..VC-0094

## Core rule
**Country is not one scalar field on a Work.**

A film or series may involve multiple production countries, co-production treaties, financing entities, broadcasters, shooting locations, story settings and release territories. These dimensions must remain distinct.

## Distinctions

### Production country
A country/territory associated with production under a competent source's cataloging or production evidence.

### Production-company jurisdiction
Country/jurisdiction of an Organization. It does not automatically define the Work's production country.

### Shooting location
Where photography/production occurred. Not automatically production country.

### Narrative setting
Where the story takes place. Never used to infer production country.

### Original language / audio language
Independent of country.

### Release territory
Where a ReleaseEvent occurred. Independent of production country.

## Representation
Use a many-to-many, provenance-backed relationship between Work and Country/Territory.

Suggested conceptual fields:
- work_id
- territory_id
- relation_kind (`production_country`, `co_production_country`, other future kinds)
- source/claim
- effective/context information where necessary
- canonical/dispute status

Do not assume the order of countries in a source expresses percentage ownership or creative priority unless the source explicitly defines that meaning.

## Source disagreement
Competent catalogs may list different country sets due to:
- financing definitions;
- co-production treaty interpretation;
- later catalog enrichment;
- distributor metadata simplification;
- festival submission metadata;
- database editorial policy.

CAS stores the source claims and may canonicalize a supported set, but does not erase alternative competent claims.

## Benchmark examples
- `The Lunchbox` — multinational country listing despite India-centered language/story context.
- `Gandhi` — multiple production countries despite Indian subject/setting.
- `The Namesake` — production-country relationships independent of diaspora setting and language.
- `All We Imagine as Light` — festival/catalog country sets can evolve or differ.
- `Monsoon Wedding` — deliberate conflict benchmark for catalog attribution.

## Quality rule
`country unknown` is different from `single-country production`.

A Work with no trustworthy country evidence should remain unknown rather than inherit:
- director nationality;
- primary language;
- shooting location;
- production company's headquarters;
- first release territory.

## V1 acceptance criteria
1. Work supports zero, one or many production countries;
2. each country association can have provenance;
3. conflicting source country sets remain explainable;
4. country does not derive automatically from language/setting/release;
5. search/filter can use canonical production-country projection without deleting underlying claims.
