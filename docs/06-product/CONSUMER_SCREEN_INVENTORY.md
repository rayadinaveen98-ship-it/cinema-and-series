# Consumer Screen Inventory

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

Screen IDs are stable references for product, design and QA discussions. Exact platform layout may differ between web and Android while preserving information architecture and behavior.

## Core navigation

| ID | Screen | Purpose |
|---|---|---|
| CS-001 | Home | Data-driven entry point to releases, upcoming works, language cinemas and archive discovery. |
| CS-002 | Explore | Structured browsing by type, language, country, year, genre, people and relationships. |
| CS-003 | Search | Universal multilingual search. |
| CS-004 | Release Calendar | Territory/language/type-aware release-event calendar. |
| CS-005 | Library | Minimal personal saves/watchlist if retained in frozen V1. |

## Search / discovery

| ID | Screen | Purpose |
|---|---|---|
| CS-010 | Search Results | Mixed-entity results with strong disambiguation. |
| CS-011 | Search Filters | Work type, year, language, country/market, genre and credit filters. |
| CS-012 | Explore Movies | Browse film works. |
| CS-013 | Explore Series | Browse episodic works. |
| CS-014 | Explore Languages | Language-first discovery, especially Indian cinemas. |
| CS-015 | Explore Countries/Regions | Production-country/region browsing. |
| CS-016 | Explore Years/Eras | Historical timeline browsing. |
| CS-017 | Explore Genres | Genre browsing. |
| CS-018 | Explore People | People discovery. |
| CS-019 | Explore Companies | Studio/production/distribution/platform browsing. |
| CS-020 | Explore Franchises/Relationships | Connected work graphs. |
| CS-021 | Upcoming Productions | Announced/filming/post-production/scheduled works. |

## Work pages

| ID | Screen | Purpose |
|---|---|---|
| CS-100 | Movie / Work Detail | Canonical detail page for a film or other standalone work. |
| CS-101 | Work Overview | Overview, identity, status, synopsis, genres and companies. |
| CS-102 | Cast & Crew | Craft-forward credits with department/job grouping. |
| CS-103 | Release Timeline | Territory/version/format/platform-specific ReleaseEvents. |
| CS-104 | Languages & Versions | Original, simultaneous-language, dubbed and alternate versions. |
| CS-105 | Relationships | Sequels, remakes, adaptations, franchise/universe and anthology links. |
| CS-106 | Media | Approved posters/backdrops/logos/stills/trailers where permitted. |
| CS-107 | Sources / Data History | Public provenance and material change history. |

## Series pages

| ID | Screen | Purpose |
|---|---|---|
| CS-200 | Series Detail | Series-level identity, overview, status, credits, release context and seasons. |
| CS-201 | Seasons List | Season hierarchy. |
| CS-202 | Season Detail | Season identity, episode list, season release context and credits. |
| CS-203 | Episode Detail | Episode identity, release/premiere, runtime, synopsis and credits. |
| CS-204 | Episode Browser | Fast series/season episode navigation. |

## People / organizations

| ID | Screen | Purpose |
|---|---|---|
| CS-300 | Person Detail | Identity, aliases, filmography and department/job history. |
| CS-301 | Person Filmography | Filterable credits by year, type, language, department and role. |
| CS-302 | Company Detail | Company identity, aliases and credited works. |
| CS-303 | Company Filmography | Production/distribution/broadcast/streaming credits. |

## Relationship / franchise views

| ID | Screen | Purpose |
|---|---|---|
| CS-400 | Franchise Detail | Ordered/grouped franchise works with relationship labels. |
| CS-401 | Remake / Adaptation Graph | Origin and related remake/adaptation works. |
| CS-402 | Relationship Graph | Visual/list representation of typed work relationships. |

## Calendar

| ID | Screen | Purpose |
|---|---|---|
| CS-500 | Calendar Month | Monthly release events. |
| CS-501 | Calendar Week | Focused near-term releases. |
| CS-502 | Release Event Detail | Exact territory/version/type/platform/date context. |
| CS-503 | Release Filters | Territory, language, work type, theatrical/digital and status filters. |

## Transparency/status components

These may render as components/sheets rather than full pages, but behavior is required:

| ID | Surface | Purpose |
|---|---|---|
| CS-600 | Evidence Summary | Explain why a sensitive/upcoming fact is presented. |
| CS-601 | Date Changed Sheet | Show prior announced dates and current date. |
| CS-602 | Conflict Notice | Explain unresolved/conflicting public metadata. |
| CS-603 | Identity Clarifier | Explain dub/remake/version relationship when confusion is likely. |

## Required states

Every important screen must define:
- loading;
- empty;
- partial/missing data;
- unknown data;
- conflicting data;
- source unavailable;
- no approved artwork;
- error/retry;
- archived/shelved/cancelled work where applicable.

The UI must not fabricate placeholders that look like confirmed facts.

## Responsive/platform requirement

Web and Android may use different navigation patterns, but:
- stable CAS URLs/deep links should map to the same entities;
- information meaning must remain consistent;
- native/localized title handling must remain consistent;
- release and relationship semantics must not change by platform;
- accessibility is required, not deferred polish.

## Deferred consumer screens

Unless the frozen V1 contract changes them, these remain beyond V1:
- public user reviews;
- public star ratings;
- social profile/feed;
- comments/forums/chat;
- ticket checkout;
- streaming playback;
- recommendation feed;
- news feed.
