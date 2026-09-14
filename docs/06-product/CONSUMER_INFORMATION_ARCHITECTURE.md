# Cinema and Series — Consumer Information Architecture

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Product role

The consumer product is the public exploration layer over the Cinema and Series canonical database. It is not a Netflix clone and is not primarily a playback product.

The core promise is:

> **Explore, understand and track cinema and series through trustworthy, multilingual, source-aware data.**

## V1 navigation

### Home
A curated data-driven entry point, not an autoplay entertainment feed.

Recommended modules:
- Releasing This Week
- Coming Soon
- Recently Released
- Recently Added / Corrected in the Archive
- Telugu Cinema
- Tamil Cinema
- Malayalam Cinema
- Kannada Cinema
- Hindi Cinema
- Other Indian Cinemas
- World Cinema
- Series Premieres
- Classics / Archive Discoveries

Exact editorial ranking rules remain OPEN until product validation.

### Explore
Structured browsing across the database.

Entry dimensions:
- Movies
- Series
- Languages
- Countries / regions
- Years / eras
- Genres
- People
- Companies
- Franchises / universes
- Remakes / adaptations
- Upcoming productions
- Release calendar

Explore should support combinations rather than forcing users into only one hierarchy.

### Search
Universal multilingual search across:
- works;
- series/seasons/episodes;
- people;
- companies;
- native titles;
- alternate/localized titles;
- transliterations;
- external IDs where useful internally/deep-link contexts.

Search results must distinguish work type, year, language and identity clearly enough to avoid same-title confusion.

### Calendar
Release-oriented exploration.

Views:
- this week;
- month;
- upcoming;
- by language;
- by territory/market;
- theatrical;
- streaming/digital where licensed data permits;
- series premieres/seasons.

A calendar item represents a ReleaseEvent, not a single global title date.

### Library
User-personal features are intentionally minimal in V1. If V1 includes a personal layer, it should initially support only foundational actions such as saved/watchlist items; reviews/social features remain out of scope unless the frozen contract changes.

## Entity pages

### Work / Movie page
Must be capable of presenting:
- primary display title;
- native/original title;
- year/status/runtime where supported;
- original language(s), production countries;
- certification context;
- synopsis/overview with provenance policy;
- genres/keywords;
- production lifecycle status for upcoming works;
- cast;
- craft-forward crew;
- release timeline by territory/version/format;
- languages/versions;
- remake/adaptation/franchise relationships;
- production/distribution companies;
- external IDs where appropriate;
- approved media;
- data/source transparency layer;
- change/history notes for material public-facing changes where useful.

### Series page
Must additionally support:
- series status;
- season hierarchy;
- episode counts;
- season pages;
- episode browser;
- network/platform/company context;
- premiere/release events by territory;
- series-level and episode-level credits where known.

### Season page
- season identity/number/title;
- episodes;
- release window/events;
- season-specific cast/crew where supported;
- artwork;
- source transparency.

### Episode page
- episode title/native/localized names;
- series/season context;
- episode number where applicable;
- release/premiere event;
- runtime;
- synopsis;
- credits;
- source transparency.

### Person page
- canonical name;
- native/alternate/stage names;
- identity disambiguation context;
- filmography by department/job;
- known career timeline information allowed by V1 source policy;
- frequent collaborators/relationships only if derived transparently and useful;
- approved portrait/media;
- source transparency.

### Company page
- canonical company name and aliases;
- country/territory context;
- type/roles where modeled;
- credited works;
- production/distribution/streaming/broadcast relationships;
- source transparency.

### Franchise / relationship page
Graph-oriented view of:
- sequels/prequels;
- remakes;
- adaptations;
- reboots;
- spin-offs;
- franchise/universe membership;
- anthology structures.

The UI must explain relationship types instead of visually implying every related title is a sequel.

## Source transparency UX

Public UI should expose provenance without overwhelming normal users.

Recommended levels:
1. normal view shows canonical data;
2. compact status/evidence affordance for sensitive/upcoming facts;
3. expandable `Sources / Data history` section;
4. full internal claims remain Control Room-only where necessary.

Useful public labels include:
- Official
- Confirmed
- Multiple sources
- Unverified
- Conflicting
- Date changed

Avoid arbitrary percentage confidence displays.

## India-first UX requirements

- Native-script title must be first-class and never discarded in favor of Romanization.
- Romanized spelling must remain searchable.
- Language and production country must not be conflated.
- Dubs, simultaneous-language versions and remakes must be visually distinguishable.
- Craft credits important to Indian cinema should be easy to reach: writing/dialogue, cinematography, editing, music/background score, lyrics, playback singing, choreography, action/stunts, production design/art, costume, sound and VFX where available.
- Release events should support Indian language/territory complexity.

## Design philosophy

Working direction: **Premium Cinematic Archive**.

- editorial rather than streaming-app mimicry;
- dark/ink cinematic surfaces may be the primary direction, but accessibility and light-mode strategy remain a design-system decision;
- excellent typography and hierarchy;
- poster/media used as context, not as a substitute for information;
- high information density on detail pages with progressive disclosure;
- no decorative UI that obscures source/status distinctions;
- layouts must remain production-realistic across web and Android.

## V1 product boundaries

Consumer V1 is a trustworthy discovery/reference experience. It does not need to prove social networking, reviews, ratings, recommendations, ticket commerce or playback.

## Success condition

A user should be able to answer questions such as:
- What exactly is this film/show?
- Is it released, upcoming, delayed or cancelled?
- What is its native/original title?
- Is this another version, a dub or a remake?
- When and where did/will it release?
- Who actually worked on it beyond headline cast?
- How is it related to other works?
- How confident/source-backed is a changing fact?

without needing to reconcile multiple movie databases manually.
