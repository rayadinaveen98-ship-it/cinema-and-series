# Global Database Analysis — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

This document defines what a serious worldwide movie-and-series database must solve beyond simply collecting rows from one API.

## Core conclusion

The world cinema/television data problem is fundamentally a **federated identity and evidence problem**.

No single audited source is sufficient across:

- modern commercial cinema;
- television/streaming series;
- historical film;
- silent film;
- lost films;
- festival-only works;
- short films;
- future productions;
- alternate cuts;
- dubbed/localized versions;
- national certification systems;
- current streaming availability;
- complete people/credits;
- artwork rights.

The correct system architecture is therefore not `one provider -> our UI`. It is:

`many sources -> observations/claims -> identity resolution -> canonicalization -> evidence-backed catalogue`.

## 1. Catalogue scale is larger than "movies and TV shows"

IMDb reported more than 30 million title records as of June 2026 because entertainment catalogues include many title types: movies, shorts, television movies, series, miniseries, episodes, specials, music videos, podcasts and more.

Cinema and Series should deliberately define which title types belong to V1 instead of ingesting everything that any provider calls a title.

### V1 target media classes

Recommended core:

- feature film;
- short film;
- TV/streaming movie;
- series;
- miniseries/limited series;
- season;
- episode;
- special;
- anthology work/segment where source evidence requires it.

Potential later classes:

- music videos;
- web originals not structured as conventional series;
- concert films;
- interactive titles;
- episodic podcasts;
- video games.

## 2. Work, expression/version, and release must not be conflated

A global database has to distinguish at least three layers:

### Work
The underlying creative audiovisual work/production identity.

### Version / manifestation
A meaningful edit/language/cut/restoration/format expression of that work where separate metadata is required.

### Release event
A specific release or availability occurrence in a territory/platform/date context.

This prevents common errors such as treating:

- a dubbed release as an unrelated movie;
- a director's cut as automatically identical in runtime/certification;
- a restoration screening as the original theatrical release;
- a platform premiere as the film's only release date.

## 3. Canonical identity must be ours

External IDs are mappings, not primary keys.

Cinema and Series should maintain permanent identifiers such as:

- `cas_work_*`
- `cas_series_*`
- `cas_season_*`
- `cas_episode_*`
- `cas_person_*`
- `cas_company_*`
- `cas_version_*`
- `cas_release_*`
- `cas_asset_*`

External identities may include:

- IMDb
- TMDB
- TheTVDB
- Wikidata
- EIDR
- ISAN
- MusicBrainz
- provider/platform IDs
- archive catalogue IDs

External-ID redirects/merges must be preserved rather than destructively replaced.

## 4. Industry identifiers are strategically useful

### EIDR
EIDR describes itself as an industry global standard for persistent identification of film, TV and digital media and reports millions of records plus many alternate IDs. It is valuable for cross-catalogue reconciliation and media-supply-chain identity.

### ISAN
ISAN is an ISO-standard persistent identifier for audiovisual works and versions. Its model explicitly distinguishes work identity from publication/rights-holder concepts.

### Decision
Neither EIDR nor ISAN should replace Cinema and Series IDs. They should be high-value external mappings and potential identity-resolution signals, subject to access/terms.

## 5. Open data is essential, but not sufficient

### Wikidata
Wikidata is strategically important because structured data in its core namespaces is CC0. It can supply broad cross-domain identity, multilingual labels, external IDs, dates, countries, occupations, relationships and references.

However:

- field completeness varies greatly;
- community mistakes/vandalism are possible;
- references are inconsistent;
- its ontology is broader than entertainment-specific needs;
- SPARQL/public query infrastructure is not a production SLA.

Therefore Wikidata is a strong seed/corroboration source, not self-validating truth.

### Wikimedia Commons
Useful for openly licensed/public-domain media, but every file has its own license/provenance requirements and Wikimedia warns reusers to verify rights independently.

## 6. Commercial metadata providers are optional accelerators, not architecture

### IMDb commercial data
Strongest value: global scale, rich credits, ratings, release data, certificates, plots, box office, entity maturity.

Architectural stance: future licensed adapter.

### TMDB commercial license
Strongest value: developer ergonomics, localization, movies/TV/people/images, changes and broad community coverage.

Architectural stance: test/adapter candidate; never canonical identity foundation.

### TheTVDB
Strongest value: TV hierarchy plus rich metadata, translations and commercial API path.

Architectural stance: possible production adapter if terms/cost fit.

### JustWatch
Strongest value: time-sensitive streaming availability by provider/territory.

Architectural stance: availability provider abstraction/partner candidate.

## 7. Historical film requires archival federation

Consumer databases cannot be our sole historical evidence layer.

Important source classes include:

- national film archives;
- cinematheques;
- scholarly catalogues;
- preservation organizations;
- festival records;
- library collections;
- restoration-program records.

Examples identified in research:

### AFI Catalog
Highly authoritative for American feature-film history, especially the first century of American cinema.

### BFI National Archive
Major British/international film and television archive with searchable holdings.

### FIAF
Connects film archives internationally. Its Treasures from the Film Archives resource covers tens of thousands of silent-film holdings across many archives.

### NFDC-NFAI
Key Indian archival institution.

### Consequence
An archive record may prove **existence/holding/version** even where modern consumer metadata is incomplete.

## 8. Television has structural complexity beyond "movie vs show"

Required concepts include:

- series;
- season;
- episode;
- specials;
- absolute episode numbering;
- aired order;
- production order;
- streaming batch releases;
- split seasons/parts;
- anthology episodes;
- miniseries;
- revived series;
- same-name reboots;
- regional broadcast dates;
- platform migration.

TheTVDB/TMDB/IMDb/Trakt all illustrate why TV cannot be squeezed into a flat title table.

## 9. Localized names are identity signals, not merely display strings

A title may have:

- original title;
- transliteration;
- translated release title;
- marketing title;
- working title;
- festival title;
- television retitle;
- censored/local-market title.

Every alias should have metadata such as:

- language;
- script;
- territory;
- usage type;
- validity dates if relevant;
- source;
- preferred/display status.

## 10. Date precision and uncertainty are global requirements

Historical records may know only:

- year;
- month/year;
- date range;
- circa date;
- first known screening rather than true premiere.

Future records may contain:

- announced year;
- announced season/quarter;
- exact tentative date;
- repeatedly postponed dates.

Never invent precision.

## 11. Credits require role normalization without destroying source wording

A robust credit should contain:

- person/company identity;
- department;
- normalized role/job;
- source role wording;
- character(s) where applicable;
- `credited_as` name;
- billing/order if known;
- uncredited flag;
- episode scope for series;
- source/evidence.

This permits both normalized search and faithful preservation of original credit wording.

## 12. Relationships should form a graph

Needed relationship families:

### Narrative/franchise
- sequel_of
- prequel_of
- spin_off_of
- part_of_franchise
- crossover_with

### Adaptation
- adaptation_of
- remake_of
- reboot_of
- based_on_work

### Version
- alternate_cut_of
- restoration_of
- dubbed_version_of
- censored_version_of
- extended_version_of

### Structural
- episode_of
- season_of
- segment_of
- compilation_contains

Relationships must be provenance-backed and may carry certainty/status.

## 13. Production lifecycle needs temporal history

A future work can transition:

`LEAD -> ANNOUNCED -> PRE_PRODUCTION -> FILMING -> POST_PRODUCTION -> COMPLETED -> SCHEDULED -> RELEASED`

with branches:

`ON_HOLD`, `SHELVED`, `CANCELLED`, `UNKNOWN`.

The lifecycle should store events rather than only current state so users can later understand delays, cancellations, title changes and production history.

## 14. Streaming availability is not title metadata

Availability is a fast-changing market observation:

`Title/Version + Territory + Provider + Offer Type + Start/End Observation + Quality/Language where known`.

It needs short freshness windows, provider attribution, and independent update machinery.

Do not encode `available_on = Netflix` permanently inside the title record.

## 15. Certification is jurisdiction-specific

Each certification system has its own:

- authority;
- rating vocabulary;
- date;
- version/cut scope;
- reason/advisory;
- territory;
- regulatory status.

A generic string such as `rating = UA` loses too much information.

## 16. Artwork/media rights are structurally separate

Metadata permission does not automatically grant artwork permission.

Asset records should include:

- asset type;
- source;
- creator/rightsholder;
- original URL/reference;
- license;
- attribution text;
- commercial-use permission;
- modification permission;
- territory/expiry if applicable;
- approval status;
- hash/checksum;
- takedown status.

A poster should not be publishable merely because a metadata provider returns an image URL.

## 17. Source snapshots must be immutable

Each acquisition should record:

- source ID;
- retrieval timestamp;
- request/reference URL or provider key;
- response/raw payload reference;
- HTTP/provider metadata where allowed;
- content hash;
- parser version;
- terms/policy version where operationally useful.

This allows reprocessing when parsers or normalization rules change.

## 18. Claims are the correct primitive

Instead of storing only:

`release_date = 2027-08-14`

store claims such as:

- Source A claims 2027-08-14.
- Source B claims 2027-08-14.
- Older Source C claimed 2027-08-07.

Canonicalization then decides the current presentation value without deleting historical disagreement.

## 19. Canonicalization should be field-specific

A source can be excellent for one field and poor for another.

Examples:

- certification board -> certification: very high authority;
- streaming aggregator -> current OTT availability: high if licensed/current;
- ticketing platform -> live theatrical showtimes: strong near-release evidence;
- community DB -> broad cast/crew coverage: useful but corroboration may be needed;
- official studio -> announced date/status: strong for its own project;
- historical archive -> preservation/history: strong for its holdings/domain.

There should be no single global `source_rank` that blindly wins all fields.

## 20. Search is a separate derived system

Authoritative storage should remain relational/normalized. Search indexes are rebuildable projections.

Search must eventually handle:

- exact titles;
- aliases;
- native scripts;
- transliterations;
- fuzzy spelling;
- people;
- companies;
- characters;
- franchises;
- years;
- languages;
- countries;
- structured filters.

PostgreSQL FTS/`pg_trgm` is adequate for early proof; a dedicated search engine can come later behind an abstraction if scale/quality demands it.

## 21. Coverage must be measurable by slice

"We have every movie" is not a valid engineering metric.

Coverage should be measured by dimensions such as:

- country;
- language;
- era;
- title type;
- release status;
- core identity completeness;
- credits completeness;
- release-history completeness;
- localization completeness;
- evidence/provenance completeness;
- artwork availability.

Example internal statement:

`Telugu feature films, 2010-2026: 96% identity coverage, 91% director coverage, 83% full crew coverage, 94% India release-date evidence coverage.`

## 22. Data quality is multidimensional

Recommended quality dimensions:

1. Identity confidence
2. Core metadata completeness
3. Credit completeness
4. Release-history completeness
5. Localization completeness
6. Provenance completeness
7. Freshness
8. Conflict status
9. Asset-rights status
10. Relationship completeness

This becomes the basis of the future CAS Coverage score.

## 23. Human review is not failure

Some cases cannot safely be automated:

- same title/year/language with overlapping cast;
- unclear bilingual vs dub status;
- disputed historical credits;
- unofficial remake allegations;
- person-name collisions;
- conflicting production-company aliases;
- ambiguous festival vs theatrical premiere.

The architecture must include queues for:

- merge review;
- split review;
- conflict review;
- source-policy review;
- asset-rights review.

## 24. AI can assist but cannot become evidence

Allowed AI uses:

- suggest identity matches;
- classify likely source fields;
- transliteration suggestions;
- anomaly detection;
- candidate relationship extraction;
- summarizing source differences for reviewers.

Disallowed without supporting source evidence:

- inventing dates;
- inventing cast/crew;
- asserting remake relationships;
- generating canonical synopsis as if sourced;
- fabricating production status.

AI output is a hypothesis, not a source.

## 25. Recommended global source layers

### Layer 1 — Open foundation
- Wikidata
- carefully selected Wikimedia Commons assets
- MusicBrainz core data for future soundtrack/music identity where useful

### Layer 2 — Official/public authority sources
- national certification boards;
- national archives;
- film institutes;
- festivals;
- studios/streamers/distributors;
- official trailers/channels;
- public film commissions/registries where applicable.

### Layer 3 — Licensed metadata providers
- IMDb commercial;
- TMDB commercial;
- TheTVDB;
- JustWatch;
- other regional/industry providers.

### Layer 4 — Specialist scholarly/reference sources
- AFI;
- BFI;
- FIAF resources;
- NFDC-NFAI;
- Indiancine.ma;
- Cinemaazi;
- other national/regional archives.

### Layer 5 — Discovery-only/reference sources
Sources whose terms do not permit automatic reuse may still help human researchers find evidence, provided we do not ingest prohibited content.

## 26. Architecture consequence

The canonical data platform should use:

- PostgreSQL as source of truth;
- append-only source snapshots/observations;
- normalized claims;
- canonical projections;
- independent external-ID mappings;
- immutable history/audit records;
- rebuildable search indexes;
- adapter-specific ingestion workers;
- human-review queues;
- explicit source policy registry.

## 27. V1 success criterion

V1 is successful when it can represent and reconcile difficult real-world cases correctly, not when it has the highest raw title count.

The first ingestion benchmark should therefore prioritize a deliberately adversarial corpus of approximately 1,000 titles spanning countries, eras, languages, title types and identity edge cases.

Only after the schema and engines survive that corpus should we attempt large-scale ingestion.
