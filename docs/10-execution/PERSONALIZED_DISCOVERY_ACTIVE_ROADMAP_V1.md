# Cinema & Series — Personalized Discovery Active Roadmap V1

**Status:** LOCKED FOR ACTIVE IMPLEMENTATION  
**Date:** 2026-09-17  
**Supersedes:** conflicting active-scope decisions in `V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md` while preserving that document as historical context.

## Product direction

Cinema & Series is now an India-first cinema discovery and release-intelligence product with three core promises:

1. **Discover what to watch** through personalized recommendations.
2. **Know what is releasing and when** through evidence-backed release intelligence.
3. **Explore movies and series through a premium cinematic experience** on web first and Android alongside it.

The existing production catalogue remains the foundation. New product work must not sacrifice data provenance, source quality, or safe production-write discipline.

---

# Locked user journey

For a first-time user:

1. **Premium Welcome Screen**
   - cinematic logo animation
   - premium motion, lighting and depth effects
   - reduced-motion fallback
   - works on web and Android wrapper

2. **Identity Screen**
   - Continue with Google
   - Continue locally
   - local profile can later be upgraded/migrated to signed-in profile

3. **First-Time Taste Setup**
   - content preference: Movies / Series / Both
   - languages
   - genres / moods
   - mainstream vs hidden gems
   - classics vs newer titles
   - India / international / both
   - surprise level
   - pick at least 5–6 titles the user already likes

4. **Taste Profile Build**
   - selected titles contribute weighted signals from genre, director/creator, cast, language, country/industry and era
   - no unsupported AI inference becomes canonical metadata

5. **First-Time Welcome Transition**
   - 2–3 second “Welcome to Cinema & Series” cinematic animation
   - shown once after setup completes

6. **Personalized Home**
   - top personalized hero slideshow with smooth cinematic transitions
   - recommendation rails
   - release-intelligence rails
   - Today in Cinema / On This Day highlight
   - existing navigation evolves rather than being replaced arbitrarily

7. **Discover / Recommendation Screen**
   - personalized but randomized recommendations
   - randomization happens only inside a relevance-qualified candidate pool
   - actions: Another Pick, More Like This, Not for Me, Save, I Watched This

8. **Notifications**
   - in-app notification center
   - recommendation/release/on-this-day notification types
   - development-only 60-second test mode
   - production cadence is event/taste driven, not spammy

---

# Locked navigation target

Primary navigation:

- Home
- Movies
- Series
- Discover
- Calendar
- Search

Right-side utilities:

- Notifications
- Profile

The current navigation may remain visually recognizable but should be made more user-friendly, responsive and premium.

---

# Locked recommendation philosophy

Recommendations must be explainable and data-backed.

Core flow:

`Eligible catalogue -> taste score -> diversity filter -> weighted random selection`

The system must not use pure random selection across the entire catalogue.

Primary recommendation signals:

- genre
- director / creator
- cast
- language
- country / industry
- release era
- movie vs series preference
- explicit user interactions

Later optional signals may include writers, franchise/series relationships, themes/moods and collaborative behavior when reliable data exists.

Recommendation surfaces include:

- Top Picks for You
- Because You Like <genre/title>
- Hidden Gems for You
- From Directors/Creators You May Like
- Series You Might Love
- Outside Your Comfort Zone
- A Random Pick for Tonight

---

# Locked artwork policy

Current artwork priority remains:

1. first-party official evidence/page artwork
2. official YouTube artwork where suitable
3. Wikidata P18 -> Wikimedia Commons
4. premium Cinema & Series fallback artwork treatment

Artwork must keep source/provenance metadata. No title-based guessed image URLs.

Artwork must be generalized for both Movies and Series through a shared title-artwork model rather than remaining movie-only long term.

No guarantee is made that every title has a rights-safe real poster. Missing artwork receives a premium fallback rather than broken/low-quality media.

---

# Active implementation sequence

## Phase P1 — Recommendation Metadata Foundation — FIRST

**Goal:** make personalized recommendations possible with real metadata.

### P1.1 Schema
Create normalized metadata structures shared by Movies and Series:

- genres
- people
- title_genres
- title_credits

Credit roles for V1:

- director
- creator
- actor / cast

Do not model genre/cast as fixed columns such as `genre1` or `actor1`.

### P1.2 Source adapters
Initial explicit source strategy:

- Wikidata P136 — genre
- Wikidata P57 — director
- Wikidata P161 — cast member
- creator properties only when semantically explicit and validated for Series

Every imported relationship must retain source provenance or be traceable to its source snapshot.

### P1.3 Read-only coverage audit
Before production writes:

- measure Movies coverage
- measure Series coverage
- inspect India-language cohorts
- quantify people identity resolution
- detect ambiguous/conflicting metadata
- reject unsafe/unsupported rows

### P1.4 Production enrichment
Only after the audit proves useful yield:

- guarded migration
- bounded/resumable ingestion
- defensive writes
- post-write quality audit
- S0/S1 regression gate remains clean

### P1 exit gate
Do not begin personalized onboarding logic until a meaningful portion of catalogue candidates has usable recommendation metadata.

---

## Phase P2 — Artwork Foundation V2

- introduce shared title-artwork model for Movies + Series
- extend existing official/Wikimedia provenance-aware artwork pipeline
- run bounded coverage audit
- improve premium fallback artwork states
- expose poster/backdrop availability consistently through APIs

---

## Phase P3 — Identity & Profiles

- Google OAuth
- Continue locally
- local profile persistence
- local-to-account migration path
- profile/preferences schema
- session handling
- logout/delete-local-profile behavior

Preferred direction: stay inside the Cloudflare Workers + D1 architecture unless evidence requires another provider.

---

## Phase P4 — First-Time Onboarding

- Welcome screen
- Login/local identity screen
- taste questionnaire
- 5–6 title selection minimum
- setup progress
- preference summary
- first-time welcome transition

Onboarding title choices must preferentially use records with strong metadata/artwork coverage.

---

## Phase P5 — Recommendation Engine V1

- deterministic taste-profile builder
- weighted scoring
- diversity guard
- weighted random candidate selection
- explanation reason for each recommendation
- interaction feedback loop
- test corpus and recommendation sanity checks

No black-box ML is required for V1.

---

## Phase P6 — Discover Screen

- “What should I watch?” centerpiece
- random personalized recommendation
- Another Pick
- More Like This
- Not for Me
- Save
- I Watched This
- Movies / Series / Both filters
- optional mood/language/era controls

---

## Phase P7 — Personalized Home V2

Top hero:

- 5–7 taste-qualified Movies/Series
- cinematic crossfade / parallax / controlled zoom
- smooth independent metadata transition
- reduced-motion support

Rails:

- Top Picks for You
- Because You Like...
- Releasing This Week
- Coming Soon
- language-personalized picks
- Series You Might Love
- Hidden Gems
- Recently Added
- Today in Cinema

---

## Phase P8 — Today in Cinema

Movies:

- exact release-date matches for current month/day across previous years
- highlight one primary item plus additional historical releases
- never infer from year-only records

Series:

- join only after exact first-air-date coverage exists; `first_air_year` alone is insufficient

---

## Phase P9 — Notifications V1

- notification schema
- in-app notification center
- recommendation notifications
- release reminders/updates
- Today in Cinema notifications
- development-only 60-second test generator
- production frequency controls

Native Android system notifications may use a native bridge initially and move to proper native implementation in the full Android app.

---

## Phase P10 — Release Intelligence Expansion

Continue strengthening the original product differentiator:

- official-source registry expansion
- date announcement detection
- date change/postponement handling
- verified/supported/unconfirmed evidence states
- conflict history
- upcoming India-first release coverage
- admin verification path

---

## Phase P11 — Controlled Catalogue Growth

Resume growth only after personalization surfaces work:

- 25K
- 50K
- later 100K+

Every growth milestone retains quality gates and provenance discipline.

---

## Phase P12 — Native Android Evolution

Current Android wrapper may continue to expose the shared web experience during active development.

Later native Android milestone:

- Kotlin + Jetpack Compose
- same API/data contracts
- native transitions
- native auth/session integration
- Android notifications
- offline-friendly preferences/cache where useful

---

# Immediate next action

**Start Phase P1 — Recommendation Metadata Foundation.**

First execution slice:

1. inspect current Movie + Series identity coverage
2. design shared genre/person/credit schema
3. build read-only Wikidata genre/director/cast resolver
4. run bounded coverage analysis over the current production catalogue
5. review yield and data quality
6. only then authorize production migration/enrichment

No welcome/auth/onboarding UI implementation should begin before P1 has produced enough usable metadata for real recommendations.

---

# Non-negotiable product rules

- Recommendations are relevant-first, random-second.
- Do not fake personalization with hard-coded lists.
- Do not invent genre/credits metadata.
- Preserve provenance for imported metadata.
- Do not break existing release intelligence while adding personalization.
- Premium UI must work even when artwork is absent.
- First-time-only flows must not annoy returning users.
- Development notification spam must never ship as production behavior.
- Web remains the fastest visual-progress surface; Android shares the same product behavior until its native evolution phase.
