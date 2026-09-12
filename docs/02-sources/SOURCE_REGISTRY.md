# Source Registry — Research Foundation v0.1

**Status: WORKING**  
**Policy review date: 2026-09-12**

This registry records candidate sources and their role in Cinema and Series. Inclusion here does **not** automatically authorize production ingestion. `SOURCE_LICENSING_MATRIX.md` and the source lifecycle status must also permit the intended use.

## Status vocabulary

- `DISCOVERED`
- `RESEARCHED`
- `LEGAL_TERMS_REVIEWED`
- `TECHNICALLY_VALIDATED`
- `APPROVED_FOR_TEST`
- `APPROVED_FOR_PRODUCTION`
- `REFERENCE_ONLY`
- `PARTNER_REQUIRED`
- `REJECTED`
- `SUSPENDED`
- `DEPRECATED`

## Core registry

| ID | Source | Class | Primary value | Access | Current status |
|---|---|---|---|---|---|
| SRC-WIKIDATA | Wikidata | B Open structured | IDs, labels, aliases, people, companies, dates, countries, relationships, external IDs | SPARQL/API/dumps | APPROVED_FOR_TEST |
| SRC-WIKIPEDIA | Wikipedia | D Reference/open text | narrative context, references, discovery | MediaWiki APIs/pages | REFERENCE_ONLY |
| SRC-COMMONS | Wikimedia Commons | B/D Open media | freely licensed/public-domain images/media | MediaWiki APIs/pages | APPROVED_FOR_TEST with per-file rights gate |
| SRC-IMDB-FREE | IMDb contributor datasets | D Restricted dataset | broad identity/credits/ratings subset | downloadable datasets | REJECTED for production database ingestion |
| SRC-IMDB-COMMERCIAL | IMDb licensed data/API | C Licensed | global titles, people, credits, releases, ratings, box office, certificates | AWS Data Exchange / GraphQL / bulk | PARTNER_REQUIRED |
| SRC-TMDB | TMDB | C/D Community/provider | movies, TV, people, translations, images, external IDs, changes | REST API / ID exports | APPROVED_FOR_TEST; commercial production requires license |
| SRC-TVDB | TheTVDB | C Community/licensed | deep TV structure, movies, credits, translations, images, releases | REST API | APPROVED_FOR_TEST; production tier/rights review required |
| SRC-TVMAZE | TVmaze | B/C Community API | TV shows, episodes, schedule, cast | REST API | LEGAL_TERMS_REVIEWED; ShareAlike architecture review required |
| SRC-JUSTWATCH | JustWatch | C Licensed/partner | territory/provider streaming availability | Partner API/data/widget | PARTNER_REQUIRED |
| SRC-EIDR | EIDR | C/Industry registry | persistent audiovisual IDs, alternate IDs, reconciliation | registry UI/API/member services | PARTNER_REQUIRED / identity research |
| SRC-ISAN | ISAN | C/Standards registry | persistent audiovisual work/version identifiers | API/lookup/member services | PARTNER_REQUIRED / identity research |
| SRC-CBFC | Central Board of Film Certification | A Government authority | Indian certification, certificate date/no., length, language, producer/applicant, credits when exposed | public CAPTCHA search / e-Cinepramaan context | REFERENCE_ONLY pending permitted bulk access |
| SRC-NFAI | NFDC — National Film Archive of India | A/D National archive | Indian historical holdings, preservation, film search | website/Film Search/research services | REFERENCE_ONLY; collaboration candidate |
| SRC-INDIANCINEMA | Indiancine.ma | D Scholarly archive | Indian historical film records, annotations, early cinema, preserved films | website | REFERENCE_ONLY for production until reuse/legal path defined |
| SRC-CINEMAAZI | Cinemaazi | D Heritage encyclopedia | regional Indian film/people/song history | website | REFERENCE_ONLY unless permission obtained |
| SRC-MOVIEBUFF | Moviebuff | D/C India metadata | Indian releases, native titles, craft credits, certifications, technical data, dub links, music details | website / potential partnership | PARTNER_REQUIRED |
| SRC-BOOKMYSHOW | BookMyShow | D/C Ticketing | current Indian theatrical listing/showtimes, language, cinema reality | website / potential partnership | REFERENCE_ONLY / PARTNER_REQUIRED |
| SRC-OTTPLAY | OTTplay | D/C India OTT | India streaming discovery/recommendation | website / potential partnership | REFERENCE_ONLY / PARTNER_REQUIRED |
| SRC-YOUTUBE | YouTube Data API | A/C Platform | official trailer/video/channel IDs and publication metadata | YouTube Data API | APPROVED_FOR_TEST with API policy constraints |
| SRC-MUSICBRAINZ | MusicBrainz | B Open structured | music identities, releases, recordings, artist relationships | API / dumps | APPROVED_FOR_TEST for CC0 core fields only |
| SRC-AFI | AFI Catalog | D Scholarly catalogue | historical American feature films | website/catalog | REFERENCE_ONLY; permission/licensing research required for bulk use |
| SRC-BFI | BFI National Archive | D National archive | British/international holdings and film/TV archival context | collection search | REFERENCE_ONLY |
| SRC-FIAF | FIAF databases/resources | D Archive federation | silent-film holdings, international archive references, film-periodical indexing | vendor/institutional access/web resources | REFERENCE_ONLY / licensed institutional access |
| SRC-STUDIO-OFFICIAL | Studios/producers/distributors | A First-party | title announcements, production status, release dates, official credits/media | press sites, releases, social/official channels | SOURCE-BY-SOURCE REVIEW |
| SRC-STREAMER-OFFICIAL | Netflix/Prime/JioHotstar/etc. official press/product pages | A First-party | upcoming slates, premiere dates, platform originals, official credits | press/editorial/product pages | SOURCE-BY-SOURCE REVIEW |
| SRC-FESTIVAL-OFFICIAL | Film festivals | A First-party | premiere status, selection, screening date, festival credits | official programme/catalog pages | SOURCE-BY-SOURCE REVIEW |
| SRC-NATIONAL-ARCHIVE-* | Other national film archives | A/D Archive | national/historical film evidence | source-specific | DISCOVERED; country-by-country registry expansion required |
| SRC-CERTIFICATION-* | Other national ratings/certification authorities | A Government/industry authority | territory ratings/certifications | source-specific | DISCOVERED; country-by-country expansion required |

## Detailed source notes

### SRC-WIKIDATA — Wikidata

**Canonical source URL:** https://www.wikidata.org/  
**Terms/licensing evidence:** https://www.wikidata.org/wiki/Wikidata:Licensing

**Useful fields**
- multilingual labels/aliases;
- instance/type;
- release/publication dates;
- countries;
- languages;
- cast/crew where populated;
- people/company identity;
- relationships;
- external identifiers including IMDb/TMDB and many archive IDs;
- references/qualifiers.

**Strengths**
- CC0 structured data;
- global scope;
- excellent cross-ID graph;
- dumps available independently of live query service.

**Weaknesses**
- uneven completeness;
- inconsistent sourcing;
- community errors possible;
- ontology does not map one-to-one to our entertainment domain.

**Planned role:** primary open seed/corroboration and identity graph; never accepted without quality rules.

### SRC-WIKIPEDIA — Wikipedia

**Useful role:** human/reference discovery, summaries for researchers, citations to stronger underlying sources.

**Constraint:** article text generally uses CC BY-SA and should not be silently copied into our proprietary canonical database. Generated/public copy must comply with attribution/share-alike where used.

**Planned role:** reference, not default structured ingestion.

### SRC-COMMONS — Wikimedia Commons

**Useful fields/assets:** photos, logos, posters only where hosted under a reusable license/public-domain claim, historic scans.

**Constraint:** every media file has its own rights/license requirements; Wikimedia explicitly advises independent verification.

**Planned role:** rights-qualified asset source through the Asset Engine only. Never bulk-publish simply because an image exists on Commons.

### SRC-IMDB-FREE — IMDb contributor datasets

**Evidence:** IMDb Help states free datasets are personal/non-commercial and may not be republished/resold/repurposed to create another movie-information database; scraping is prohibited.

**Decision:** REJECTED for building our production database.

**Allowed research role:** understand schema concepts and evaluate potential commercial product value, without importing restricted data into production.

### SRC-IMDB-COMMERCIAL — IMDb licensed products

**Capabilities observed:** titles, names, credits, plots, awards, ratings, releases, certificates, box office, alternate titles and more; GraphQL API and bulk products.

**Planned role:** future accelerator if commercial terms/cost justify it.

**Architecture rule:** IMDb IDs remain external IDs; our catalogue must survive removal of the provider.

### SRC-TMDB — TMDB

**Evidence:** developer API is non-commercial with attribution; commercial use/data/images require a commercial license. API supports movies, TV, people, images, translations and change tracking; daily ID exports are IDs/high-level fields rather than full data dumps.

**Planned role:** disposable research/test adapter now; potential licensed production adapter later.

**Architecture rule:** no `tmdb_id` primary-key dependency.

### SRC-TVDB — TheTVDB

**Current published capabilities:** titles, overviews, companies, runtime, genres, art, ratings, external IDs, characters, credits, translations, statuses, awards, franchises, TV seasons/episodes, international dates, countries, languages and more.

**Current published licensing:** commercial tiers based on revenue; lowest tier currently published as free with attribution under the stated revenue threshold.

**Planned role:** serious candidate for TV-depth benchmarking and potentially production integration.

**Open issue:** artwork/data rights must be interpreted carefully; provider states it does not claim ownership of all uploaded images/data, which is not equivalent to granting us universal downstream rights.

### SRC-TVMAZE — TVmaze

**Evidence:** public API is CC BY-SA; enterprise licensing is available for alternative license/SLA/support.

**Planned role:** TV research/test source.

**Open legal/architecture issue:** ShareAlike obligations could be incompatible with our intended proprietary canonical compilation depending on integration method. Do not production-ingest until reviewed.

### SRC-JUSTWATCH — JustWatch

**Evidence:** official partner site offers Data, API and Widget partnerships.

**Planned role:** preferred future availability-provider candidate.

**Architecture:** all availability sits behind a provider abstraction; no current availability becomes permanent title metadata.

### SRC-EIDR — EIDR

**Evidence:** industry persistent identifier registry for film/TV/digital media; public site reports millions of records and alternate IDs. Membership flow includes API/UI/sandbox access.

**Planned role:** identity-resolution signal and external identifier; potential partner/member integration.

### SRC-ISAN — ISAN

**Evidence:** ISO-standard persistent audiovisual work/version identifier; API/lookup services exist, with complete metadata requiring credentials/signature in documented flows.

**Planned role:** external ID and identity/version signal, subject to access terms.

### SRC-CBFC — CBFC

**Evidence:** public Search Film page can expose title, language, category, regional office, certificate number/date, certified length, producer/applicant, plot, cast/credits. Current ratings include U, UA 7+, UA 13+, UA 16+, A, S.

**Strength:** highest-authority source for Indian CBFC certification facts.

**Constraint:** search is CAPTCHA-gated; site states copyright/all rights reserved; no approved bulk API identified.

**Planned role:** manual/admin verification and provenance reference until a lawful scalable data-access path exists.

### SRC-NFAI — NFDC-NFAI

**Capabilities:** Film Search, collection/preservation context, restoration/digitization and research services.

**Planned role:** high-value historical authority and potential institutional collaboration.

**Constraint:** no production bulk API/reuse licence identified in this pass.

### SRC-INDIANCINEMA — Indiancine.ma

**About:** annotated Indian-film archive, 80,000+ unique film links claimed on its About page, early-cinema preservation focus.

**Policy evidence:** site describes itself as non-commercial; film access varies by copyright term; user annotations/materials have CC BY-SA terms.

**Planned role:** scholarly/historical reference and possible future collaboration, not assumed commercial ingestion.

### SRC-CINEMAAZI — Cinemaazi

**Capabilities:** regional Indian cinema encyclopedia, people, songs, heritage material.

**Policy evidence:** disclaimer states text/images cannot be reused without permission; project itself acknowledges possible incompleteness/errors due scarce historical evidence.

**Planned role:** reference/corroboration; permission/partnership needed for reuse.

### SRC-MOVIEBUFF — Moviebuff

**Observed fields:** title/native name, runtime, cast, department-level crew, rating, genres, India/international release events, technical details, censor-certificate section, posters/trailers, some dub relationships, track/music credits.

**Policy evidence:** terms prohibit data mining/robots/screen scraping without express consent and require permission for non-personal/commercial content use.

**Planned role:** high-value India metadata benchmark and partnership candidate; no unauthorized scraping.

### SRC-BOOKMYSHOW — BookMyShow

**Observed value:** India theatrical listing, language/genre navigation, cinemas/showtimes, upcoming/current titles.

**Policy evidence:** current site states content/images are copyright protected and unauthorized use is prohibited; no production bulk API identified.

**Planned role:** near-release/current-theatrical corroboration only via permitted/licensed route.

### SRC-OTTPLAY — OTTplay

**Observed value:** Indian OTT catalogue/discovery/recommendations.

**Policy evidence:** terms restrict copying/republication and explicitly prohibit scraping/robots/automatic acquisition.

**Planned role:** market benchmark/reference; potential partner only.

### SRC-YOUTUBE — YouTube Data API

**Useful fields:** video ID, channel ID, title, publication timestamp, duration, embeddability/status and thumbnails/other metadata under API rules.

**Constraints:** quota; policy compliance; stored resource metadata generally needs deletion/refresh after 30 days under YouTube developer policies; derived-data rules are restrictive.

**Planned role:** identify/link official trailers and first-party videos, not archive/download video media.

### SRC-MUSICBRAINZ — MusicBrainz

**Evidence:** core database is CC0; supplementary data uses a different non-commercial share-alike license; database dumps are published regularly.

**Planned role:** future soundtrack/artist/release identity for fields that are in CC0 core data. Do not ingest supplementary fields into commercial production without compatible licensing.

### SRC-AFI — AFI Catalog

**Value:** scholarly American film history; roughly first century of American features plus later basic records.

**Planned role:** historical reference; bulk reuse requires separate permission/licensing analysis.

### SRC-BFI — BFI National Archive

**Value:** British and international moving-image archive/collections.

**Planned role:** archival reference and potential institutional source.

### SRC-FIAF — FIAF

**Value:** international archive federation; Treasures from the Film Archives provides silent-film holdings data; periodical databases provide research context.

**Constraint:** major databases are accessed through institutional/vendor arrangements such as Ovid/ProQuest.

**Planned role:** historical validation/research; not assumed open bulk source.

## Mandatory expansion before V1 freeze

This registry is not globally complete. Before freeze we must add/research:

- certification/rating authorities for priority territories (US, UK, EU markets, Japan, South Korea, Australia, Canada and others);
- national film archives/film institutes for priority cinema territories;
- major festival catalogues (Cannes, Venice, Berlin, TIFF, Sundance, IFFI, major Indian regional festivals and others);
- studio/distributor/streamer source adapters and terms;
- box-office sources;
- public-domain/open poster/media collections;
- country-specific film registries where available.

## Production gate

A source can feed production only when all of the following are explicit:

1. lifecycle status permits production;
2. exact fields/use case are listed in the Data Field Source Matrix;
3. access method is permitted;
4. attribution/branding is implemented;
5. commercial-use status is compatible with intended deployment;
6. asset rights are separately approved when media is involved;
7. refresh/deletion requirements are implementable;
8. source-specific adapter tests pass;
9. failure/fallback behavior is documented.
