# Competitor Audit — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**  
**Scope:** consumer databases, tracking/discovery products, India-focused services, and archival/scholarly resources relevant to Cinema and Series.

## Executive conclusion

No audited product should be dismissed as simply "bad" or "incomplete". Each is optimized for a different job:

- IMDb optimizes for broad global entertainment metadata and audience utility.
- TMDB optimizes for community-maintained metadata, localization, images, and developer access.
- TheTVDB optimizes for structured TV/movie metadata and integration.
- Letterboxd optimizes for film culture, diary, reviews, lists, and social discovery.
- Trakt optimizes for watch history, tracking, scrobbling, lists, and calendars.
- JustWatch optimizes for current streaming availability and discovery.
- BookMyShow optimizes for Indian theatrical discovery, showtimes, and ticketing.
- OTTplay optimizes for Indian OTT discovery, recommendations, and subscriptions.
- Moviebuff provides unexpectedly deep India-oriented film metadata, craft credits, certifications, technical details, releases, and version relationships.
- NFDC-NFAI, Indiancine.ma, Cinemaazi, AFI, BFI, and FIAF are archival/scholarly resources rather than general consumer databases.
- Rotten Tomatoes and Metacritic optimize for critical/audience evaluation rather than archival completeness.
- Plex Discover optimizes for universal discovery/watchlisting across services and personal media.

The opportunity for Cinema and Series is therefore **not** "make IMDb for India" or "make Netflix-looking TMDB". The opportunity is to build a source-transparent, provenance-preserving, multilingual, lifecycle-aware cinema knowledge system that is global while being unusually strong on Indian cinema.

## Evaluation dimensions

Products were evaluated against the dimensions that matter to our mission:

1. Global movie coverage
2. Series/season/episode coverage
3. Historical depth
4. Upcoming/development coverage
5. Indian regional-cinema depth
6. Native-script/localized titles
7. Dub/remake/version modeling
8. Territory-specific release history
9. Cast/crew/craft depth
10. Certification data
11. Streaming availability
12. User tracking/social features
13. Public/developer data access
14. Provenance/source transparency
15. Change-history transparency
16. Sustainable commercial reuse path

## Competitor profiles

### IMDb

**Primary job:** broad global entertainment information, ratings, reviews, filmographies, lists, watchlist, search, and industry metadata.

**Strengths**
- Exceptional catalogue scale. IMDb reported 30,380,243 titles as of June 2026, including 750,723 movies, 301,531 TV series, and 9,742,757 TV episodes.
- Strong people/credit graph, alternate titles, release dates, certificates, keywords, ratings, box office, and production status.
- Commercial GraphQL and bulk-data products are available and updated frequently.
- Mature entity identity and duplicate/remap handling.

**Limits for our vision**
- Free contributor datasets are explicitly unsuitable for republishing/repurposing into another movie database.
- Commercial reuse requires a licensing relationship.
- Consumer-facing provenance is not the core product experience.
- India is represented within a global schema rather than with an India-specific release/version/craft philosophy.

**What to learn**
- Durable external identifiers.
- Duplicate/remap semantics.
- Rich credit model.
- Broad title-type taxonomy.
- Production-status handling.

### TMDB

**Primary job:** community-driven movie/TV/people metadata, localization, images, and developer API.

**Strengths**
- First-class movies, television, people, images, translations, companies, collections, keywords, and external IDs.
- Strong developer ergonomics.
- Change tracking and daily valid-ID exports are useful for synchronization.
- Language/localization support is broadly integrated.

**Limits for our vision**
- Developer API is free only for non-commercial use with attribution; commercial use requires licensing.
- Community data quality varies by field/title/region.
- ISO 639-1 language dependence leaves gaps for languages without two-letter codes.
- A product built around TMDB IDs inherits provider dependence.
- Images and metadata must be treated under the provider's applicable commercial terms rather than as assets we automatically own.

**What to learn**
- Localization and translation architecture.
- External-ID mapping.
- Change feeds.
- Developer-friendly resource separation.

### TheTVDB

**Primary job:** structured entertainment metadata for TV and movies, with API licensing.

**Strengths**
- Deep series/season/episode structure.
- Cast, crew, characters, translations, companies, releases, artwork, trailers, statuses, franchises, awards, and taxonomy.
- Clear commercial tiering; the current published API page states free access with attribution below a specified revenue threshold and paid tiers above it.
- Dedicated editorial moderation around community data.

**Limits for our vision**
- Provider dependency remains if made foundational.
- Artwork availability does not automatically settle downstream copyright/rights questions.
- India-specific film release/version semantics are not the defining purpose.

**What to learn**
- TV hierarchy.
- Commercial provider abstraction.
- Editorial moderation workflows.

### Letterboxd

**Primary job:** cinephile social network, diary, reviews, ratings, lists, discovery.

**Strengths**
- Excellent film-centric community experience.
- Diary/list/review interactions create cultural value beyond raw metadata.
- Strong taste/discovery identity.

**Limits for our vision**
- As of the research date, Letterboxd's FAQ says returning TV series are not supported; only a limited set of TV/miniseries/exception content is present.
- Its API is request-only and explicitly recommends TMDB for non-Letterboxd movie/TV metadata.
- It is not a source-transparent archival database.

**What to learn**
- Film-first interaction design.
- Lists/diary as later product layers, not V1 database requirements.

### Trakt

**Primary job:** watch history, scrobbling/check-ins, collections, watchlists, lists, favorites, calendars, and cross-app tracking.

**Strengths**
- Excellent personal viewing-state model.
- API exposes history, collections, lists, watchlist and related behaviors.
- Calendar/release tracking is strong for personal usage.

**Limits for our vision**
- Tracking is the core value, not canonical metadata scholarship.
- A tracking product does not solve our source/provenance problem.

**What to learn**
- Personal-state separation from title metadata.
- Calendar/release UX for a later phase.

### JustWatch

**Primary job:** where-to-watch discovery and streaming availability.

**Strengths**
- Strong provider/territory availability data.
- Partner program explicitly offers data/API/widget access.
- Useful current availability timestamps and provider comparisons.

**Limits for our vision**
- Availability is highly time-sensitive and territory-specific.
- Partner/licensed integration is the appropriate path; it should not be assumed to be free infrastructure.
- It is not primarily an archival cinema-history database.

**What to learn**
- Availability as a separate temporal domain.
- Provider abstraction by territory and monetization type.

### BookMyShow

**Primary job:** theatrical discovery, cinemas, showtimes, tickets, events, and streaming commerce in India.

**Strengths**
- Extremely useful signal for what is actually bookable/currently playing in Indian markets.
- Rich language and genre navigation, including many regional Indian languages.
- City/theatre/showtime context that global databases usually lack.

**Limits for our vision**
- Commerce/showtimes are the product purpose, not archival completeness.
- Site footer/terms state content and images are copyright protected and unauthorized use is prohibited.
- No production-grade bulk metadata API was identified in this audit.

**What to learn**
- India language navigation.
- The difference between announced release and actually bookable theatrical release.

### OTTplay

**Primary job:** Indian OTT search/recommendation/subscription aggregation.

**Strengths**
- India-centric language/taste recommendations and OTT discovery.
- Large streaming catalogue orientation.

**Limits for our vision**
- Terms prohibit page scraping/automated acquisition and restrict copying/republication.
- Primary objective is what/where/how to watch, not permanent cinema identity/history.

**What to learn**
- India-specific OTT preferences.
- Recommendation UX belongs after the database foundation.

### Moviebuff

**Primary job:** India-heavy movie information, release discovery, social features, and industry-linked metadata.

**Strengths observed in current title pages**
- Native-script title names.
- Indian certification.
- India and international release dates.
- Detailed department credits: direction, production, camera, writers, music, art, editorial, etc.
- Technical metadata such as film type, frame rate, aspect ratio, colour and stereoscopy on some titles.
- Track-level music metadata on some historical titles, including lyricists and playback singers.
- Dub relationships on some current titles.
- Censor-certificate sections on some pages.

**Limits for our vision**
- Terms explicitly prohibit data mining, robots, screen scraping, and similar extraction without written consent.
- Non-personal/commercial content use requires express permission.
- The core public product is film-centric and India-release-centric rather than a global source-transparent knowledge graph.

**Strategic consequence**
Moviebuff materially raises our quality bar. Cinema and Series cannot differentiate merely by "having Telugu/Tamil/Malayalam films" or "showing craft credits". Our differentiator must be stronger identity/reconciliation, transparent evidence, production lifecycle, historical + future coverage, global relationships, and measurable quality.

### NFDC — National Film Archive of India (NFAI)

**Primary job:** preservation, archival holdings, research access, film search, restoration, and Indian film heritage.

**Strengths**
- Official archival institution.
- Film Search and collection-oriented records.
- High potential authority for Indian historical holdings and preservation context.

**Limits for our vision**
- No public bulk API/licence suitable for automatic production ingestion was identified in this audit.
- Archive holdings are not equivalent to a complete consumer metadata database.

**What to learn**
- Historical authority must come from archival/scholarly institutions, not only crowd databases.

### Indiancine.ma

**Primary job:** annotated online archive of Indian film for research, criticism, education and scholarship.

**Strengths**
- More than 80,000 unique film links according to its About page.
- Strong focus on early/pre-1960 Indian cinema.
- Dense annotations and research utility.
- Rich filmographic records for historical Indian cinema.

**Limits for our vision**
- Site states it is intended for non-commercial purposes.
- Copyrighted films are access-restricted; annotations/user-generated materials have separate licensing.
- Not a straightforward commercial bulk-ingestion source.

**What to learn**
- Historical Indian cinema requires archive-specific sourcing and uncertainty handling.
- Film scholarship can contain metadata dimensions missing from consumer databases.

### Cinemaazi

**Primary job:** Indian film-history/heritage documentation and encyclopedia.

**Strengths**
- Explicit multi-regional mission across Hindi and many regional cinemas.
- Film, people, songs, memorabilia and scholarly editorial content.
- Targets historical Indian cinema through 1999.

**Limits for our vision**
- Disclaimer states images/text cannot be reused without permission.
- The project itself notes that records may be incomplete or contain errors where credible sources are scarce.
- Not an unrestricted ingestion source.

**What to learn**
- Build uncertainty into historical records.
- Preserve source notes rather than pretending all vintage metadata is exact.

### Rotten Tomatoes / Metacritic

**Primary job:** review aggregation and evaluation.

**Strengths**
- Rotten Tomatoes exposes critic consensus through Tomatometer and audience-oriented measures.
- Metacritic produces weighted Metascores across movies/TV and other media.

**Limits for our vision**
- Neither is designed as a complete archival title/credit authority.
- Review/score data has distinct licensing and editorial semantics.

**What to learn**
- Ratings/review aggregation is a separate product domain and should not contaminate V1 metadata priorities.

### Plex Discover

**Primary job:** universal discovery and watchlisting across Plex and external streaming services.

**Strengths**
- Consolidated watchlist independent of where content is available.
- Discovery across personal media and streaming providers.

**Limits for our vision**
- Consumer consumption layer, not an archival metadata authority.

**What to learn**
- A later Cinema and Series library/watchlist can sit above the database without changing canonical metadata.

### AFI Catalog / BFI / FIAF

**Primary job:** scholarly/archival film documentation and holdings/research.

**Strengths**
- AFI is exceptionally authoritative for historical American feature films and documents the first century of American cinema.
- BFI National Archive has international holdings with a strong British collecting mission.
- FIAF connects film archives worldwide; its Treasures from the Film Archives dataset covers silent-film holdings across many archives.

**Limits for our vision**
- Coverage is mission-specific rather than a single worldwide consumer catalogue.
- Access/licensing varies; FIAF databases may require institutional/vendor access.

**What to learn**
- Global historical coverage must federate national archives and scholarly catalogues.

## Cross-product gap matrix

| Capability | Broad global DBs | Social/tracking | India commerce/discovery | India archives | Cinema and Series target |
|---|---|---|---|---|---|
| Global movies | Strong | Medium | Low/Medium | Low | Strong |
| Full TV hierarchy | Strong in IMDb/TMDB/TVDB | Strong in Trakt | Low | Low | Strong |
| Indian regional depth | Variable | Variable | Strong current | Strong historical slices | Strong current + historical |
| Native script | Variable/Strong | Variable | Strong | Strong | First-class |
| Dub/remake semantics | Inconsistent | Limited | Moviebuff has useful cases | Historical context | Explicit graph |
| Release history by territory/version | Variable | Calendar-oriented | Strong current India | Historical slices | First-class event model |
| Production lifecycle | Partial | Weak | Upcoming lists | Weak | First-class state machine |
| Evidence/provenance visible | Generally weak consumer UX | Weak | Weak | Often scholarly/manual | Core product property |
| Conflict preservation | Mostly hidden | No | No | Notes/manual | Core data model |
| Change history | Provider-specific | User history, not data history | Weak | Manual | Field-level audit trail |
| Measurable coverage | Rarely user-facing | No | No | Project-specific | Core quality metric |

## Product gap we will pursue

**Cinema and Series = a living global cinema/series knowledge base with India-deep multilingual modeling, explicit work/version/release relationships, production lifecycle history, field-level provenance, conflict preservation, and measurable coverage.**

This is intentionally different from:
- a streaming guide;
- a ticket app;
- a ratings site;
- a social diary;
- an API wrapper;
- an archive-only catalogue.

## Rejected differentiation claims

The following claims are too weak or false as primary differentiation:

- "We include regional Indian movies." — Existing services already do.
- "We show cast and crew." — Commodity feature.
- "We show native-language titles." — Already present in several products.
- "We show OTT links." — JustWatch/OTTplay/Plex and others specialize here.
- "We show detailed Indian craft credits." — Moviebuff already demonstrates meaningful depth.
- "We look like Netflix." — UI style is not defensible product value.

## Durable differentiation candidates

1. Field-level provenance and source transparency.
2. Claims/conflicts instead of silent overwrites.
3. Durable independent Cinema and Series identifiers.
4. Production lifecycle from discovery/announcement through release/cancellation.
5. Release-event history rather than one release-date field.
6. Explicit remake/dub/adaptation/cut/franchise relationships.
7. India-deep language/version/territory semantics inside a global schema.
8. Historical archive federation plus modern/future source monitoring.
9. Measured coverage and data-quality scores.
10. Source independence with adapters and fallbacks.

## Evidence reviewed

Primary/official pages reviewed during this audit include IMDb statistics/licensing/developer documentation; TMDB API documentation; TheTVDB About/API Licensing; Letterboxd FAQ/API; Trakt API documentation; JustWatch partner pages; BookMyShow current site/terms footer; OTTplay About/Terms; Moviebuff About/Terms/current film pages; NFDC-NFAI Film Search; Indiancine.ma About/Copyright; Cinemaazi Project/Disclaimer; Rotten Tomatoes About; Metacritic About; Plex Discover/Universal Watchlist; AFI Catalog; BFI National Archive; and FIAF databases/resources.

Detailed URLs and licensing conclusions are recorded in `docs/02-sources/SOURCE_REGISTRY.md` and `SOURCE_LICENSING_MATRIX.md`.
