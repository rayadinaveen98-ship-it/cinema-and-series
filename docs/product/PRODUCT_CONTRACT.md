# Product contract — approved 2026-11-18

Goal: a premium Android-first, worldwide cinema-and-series discovery database.

## In scope for the first product foundation

1. Regional, national and international movie/series records with stable title identity.
2. Original language, original/localized names, release information, genre and verified OTT details.
3. First-launch language and genre selection; guest-first personalized recommendations.
4. On This Day: films and series with a verified original premiere on a given month/day in past years, not mixed with OTT or regional-release events.
5. Netflix-inspired but visually original browsing. Beautiful typography-based title holders and no poster artwork.
6. Interactive, responsive Android phone/tablet UI with accessible motion.
7. Search by canonical and alternative names with language-aware ranking.

## Proposed small additions accepted in previous architecture discussion

- Similar titles and discovery filters are foundational recommendation/discovery functions.
- Watchlist/Watched: planned optional feature, must not prevent the core launch.
- Optional account and cross-device sync: NOT in first foundation; explicit new authorization required.
- iOS and web user experiences: future options, not part of the current build.

## Constraints

- Zero-rupee pilot: no upgrades, payment methods or paid APIs without further approval.
- Only licensed, permitted source integrations. Preserve attribution where required.
- No fabrication of release dates, languages, streaming offers, or duplicate movie identities.
- The first milestone proves data correctness with synthetic tests, then a separately verified real-title pilot of approximately 60 records.
- Current repository contains architecture and early engineering scaffolding, not a working production app.

## Operational acceptance

A release cannot be called stable without tested APIs, database migrations, verified real catalogue samples, responsive UI, a physical Android APK test, and documented source/usage compliance.
