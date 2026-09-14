# Consumer V1 Scope Decisions

**Status: LOCKED**  
**Date: 2026-09-14**

## Product goal

V1 consumer product proves the Cinema and Series database is useful, trustworthy, searchable and explorable. It is not yet a social/watch-tracking super-app.

# Navigation

Primary consumer navigation:
- `Home`
- `Explore`
- `Search`
- `Calendar`

Entity/detail pages are reached through these surfaces.

No mandatory `Library` tab in V1 because personal accounts/watchlists are deferred.

# Accounts / library

**Deferred beyond V1:**
- user login for ordinary consumers;
- personal watchlist/library;
- watch history;
- ratings/reviews;
- follows/social graph;
- personalized recommendations.

Control Room authentication is separate and remains required.

# Streaming availability

Schema/domain support remains, but consumer V1 makes **no promise** to show current streaming availability unless a licensed sustainable provider is approved before launch.

Absence of availability data must not look like `not streaming anywhere`; it means `availability not currently verified`.

# Public provenance

Consumer detail pages expose a readable evidence model:
- simple evidence/state badge near important volatile facts (`Official`, `Confirmed`, `Conflicting`, etc.);
- expandable `Sources & history` section;
- release-date history where relevant;
- conflict/dispute presentation when unresolved.

The consumer view does not expose every internal parser/debug field. Control Room retains full claim-level detail.

# CAS Coverage

The numeric/dimensional CAS Coverage dashboard is **internal-only in V1**.

Consumers may see qualitative indicators such as:
- data incomplete;
- source conflict;
- verification state;
- last verified date for volatile facts.

Do not present a misleading single public completeness score before the metric has enough historical calibration.

# Artwork-less titles

A title with no publishable artwork remains fully visible using the locked premium placeholder system in `ARTWORK_PUBLICATION_BASELINE_V1.md`.

Search ranking or entity visibility must not be reduced simply because artwork rights are unavailable.

# Home

V1 Home uses database-derived modules such as:
- Releasing Soon;
- This Week;
- Recently Released;
- Upcoming Productions;
- Recently Added / Improved Records;
- Indian Cinema language entry points;
- World Cinema entry points;
- Series premieres/returns where modeled.

Avoid fake personalization.

# Explore

Explore supports structured browsing/filtering by:
- Work type;
- language;
- country/territory;
- year/date range;
- genre;
- production/release status;
- director/principal credits where indexed;
- relationship/franchise where useful.

# Search

Search is the primary power feature and must support:
- title/original title;
- aliases;
- native script;
- transliterations;
- people;
- organizations;
- selected credits;
- year/language/type disambiguation.

# Calendar

Calendar is database-derived, not a manually curated news feed.

It can display verified/sourced:
- theatrical releases;
- premieres;
- streaming releases only where licensed/verified data exists;
- series/episode dates where supported;
- re-releases/restorations.

Past superseded dates remain in history, not in the active calendar.

# Not V1

Explicitly not consumer V1:
- social feed;
- reviews/ratings;
- news feed;
- personalized recommendation engine;
- ticket purchasing;
- direct streaming playback;
- box-office charts unless separately approved later;
- full developer API product.

These decisions keep V1 centered on the database itself.