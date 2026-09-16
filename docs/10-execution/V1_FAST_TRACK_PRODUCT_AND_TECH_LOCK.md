# Cinema and Series — Fast-Track V1 Product & Tech Lock

**Status:** LOCKED FOR ACTIVE IMPLEMENTATION  
**Date:** 2026-09-16

## Why this exists

The earlier research foundation intentionally explored an IMDb/TMDB-scale, provenance-heavy cinema knowledge platform. That work remains valuable future-platform research, but it is no longer allowed to block the first useful product.

The active V1 is deliberately narrow.

## V1 product contract

V1 must do three things exceptionally well:

1. Show movie names.
2. Show release dates, with India-first verification.
3. Present them through a premium cinematic web experience.

Everything else is deferred unless it is required to make those three capabilities reliable.

### Explicitly deferred from active V1

- 1,000-case validation corpus as an implementation prerequisite
- universal Work/Version/Release ontology
- generalized claims/canonicalization engine
- complex identity merge/split workflows
- IMDb-scale people/credits database
- streaming availability
- box office
- ratings/reviews
- recommendation engine
- user accounts/watchlists
- dedicated search engine
- native Android app
- exhaustive poster/still ingestion without a rights-safe source

The existing research/specification files are preserved as future architecture reference. They do not block this V1.

# Locked technical stack

## Application

- **React Router v8** full-stack framework
- **React + TypeScript**
- **Vite** toolchain through Cloudflare's first-class React Router integration
- **Tailwind CSS** for styling
- **shadcn/ui** for accessible, editable primitives
- **Motion for React** for premium transitions, gestures and scroll animation

Reason: Cloudflare documents React Router as a first-class full-stack Workers framework. This avoids depending on the newer beta `vinext` compatibility layer required for Next.js on Cloudflare while retaining full React flexibility and SSR.

## Hosting / compute

- **Cloudflare Workers**
- custom domain later through Cloudflare DNS
- Worker serves SSR routes/API and static assets

Cloudflare becomes the primary runtime so V1 does not require Vercel.

## Database

- **Cloudflare D1**
- SQLite-compatible relational schema
- D1 Worker binding for server-side queries
- Time Travel / point-in-time recovery

D1 is sufficient for the deliberately small V1 domain and removes the need for Supabase in the active architecture.

## Scheduled ingestion / ETL

- **GitHub Actions** in the existing public repository
- Python for source retrieval, normalization and verification jobs where useful
- TypeScript only where it materially simplifies sharing code
- Actions write/upsert into D1 using Cloudflare/Wrangler/API credentials stored as GitHub Actions secrets

Reason: standard GitHub-hosted runners are free for public repositories and are better suited than the Workers Free CPU budget for longer ingestion/ETL jobs.

## Optional future media storage

- **Cloudflare R2**, but only when a rights-safe artwork source is approved.
- V1 UI must remain premium even when artwork is missing.

# V1 source strategy

## 1. Wikidata — catalogue seed/discovery

Wikidata structured data is the primary open catalogue seed.

Use it for:
- movie QID
- title / multilingual labels
- aliases when helpful
- known release/publication date statements
- language/country signals needed for discovery

### Access rule

Do **not** make live page rendering depend on Wikidata SPARQL.

The public Wikidata Query Service is used only by scheduled ingestion/research jobs, with narrow queries, caching and retries. Targeted entity/API retrieval may be used when a QID is already known.

All user-facing pages read our own D1 database.

## 2. Official sources — release-date authority

For active/upcoming Indian titles, prefer direct official evidence from:

1. official production-house/studio site or announcement
2. official distributor site or announcement
3. official movie site
4. official YouTube studio/distributor/movie channel and video description
5. official certification/authority source where it actually states the relevant fact

CBFC certification dates must never be silently treated as theatrical release dates.

Official social posts may be stored as manual evidence links initially; platform-specific automation is deferred unless an approved API path is available.

## 3. YouTube Data API — first automated official-source monitor

Maintain a registry of known official production/distribution channels.

Prefer polling known channel upload playlists rather than broad search wherever possible. New uploads are scanned for movie titles and explicit date announcements; candidates enter verification/upsert logic.

A Google Cloud / YouTube Data API key is required before this adapter can run in production.

# Release-date policy

V1 uses a simple status model rather than a generalized claims engine.

- `verified` — explicit official source supports the displayed release date
- `supported` — Wikidata plus another competent source agree, but no first-party confirmation has been captured
- `unconfirmed` — only open-source/discovery evidence exists or sources conflict

Display priority:

1. manually/officially verified India theatrical date
2. other verified relevant release event
3. supported Wikidata date
4. unconfirmed Wikidata date with appropriate UI treatment

Conflicts are preserved in a small evidence table; they do not require a generalized canonicalization engine in V1.

# Minimal database model

## movies

- `id` INTEGER PRIMARY KEY
- `wikidata_qid` TEXT UNIQUE
- `title` TEXT NOT NULL
- `native_title` TEXT NULL
- `language_code` TEXT NULL
- `country_code` TEXT NULL
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

## releases

- `id` INTEGER PRIMARY KEY
- `movie_id` INTEGER NOT NULL
- `release_date` TEXT NOT NULL
- `country_code` TEXT NULL
- `release_kind` TEXT NOT NULL DEFAULT 'theatrical'
- `verification_status` TEXT NOT NULL
- `is_display_release` INTEGER NOT NULL DEFAULT 0
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

## release_evidence

- `id` INTEGER PRIMARY KEY
- `release_id` INTEGER NOT NULL
- `source_type` TEXT NOT NULL
- `source_name` TEXT NOT NULL
- `source_url` TEXT NOT NULL
- `source_date` TEXT NULL
- `supports_date` TEXT NULL
- `captured_at` TEXT NOT NULL
- `notes` TEXT NULL

## source_channels

- `id` INTEGER PRIMARY KEY
- `source_name` TEXT NOT NULL
- `source_type` TEXT NOT NULL
- `youtube_channel_id` TEXT NULL
- `website_url` TEXT NULL
- `active` INTEGER NOT NULL DEFAULT 1
- `last_checked_at` TEXT NULL

# Initial ingestion workflow

```text
GitHub Actions schedule/manual dispatch
        |
        +--> narrow Wikidata discovery queries
        |       -> normalize title/date/QID
        |       -> upsert D1 movie/release candidates
        |
        +--> official-source monitors
                -> known YouTube upload playlists
                -> approved official web endpoints where permitted
                -> detect explicit release-date evidence
                -> upgrade release status / preserve evidence

Cloudflare Worker + React Router
        -> read D1 only
        -> server-render premium pages
```

# Premium UI direction

Design target: cinematic editorial product, not database admin UI.

Core surfaces for V1:

1. **Home** — hero + releasing this week + coming soon + Indian-language rails
2. **Release Calendar** — day/month exploration focused on release dates
3. **Movie detail** — title, release date, language/context and verification state
4. **Search** — simple title lookup from D1

Visual principles:
- dark cinematic foundation with high-contrast typography
- editorial spacing and large type
- subtle glass/blur only when useful
- restrained glow/grain
- high-quality motion, never excessive motion
- premium empty/artwork-less states so UI quality does not depend on poster availability
- mobile-first responsiveness
- WCAG-conscious contrast and motion reduction

# Reliability rules

- production pages never call Wikidata/YouTube directly from the browser
- all external-source failures degrade ingestion, not the user-facing catalogue
- last known records remain readable if an upstream source is down
- ingestion must be idempotent
- every displayed release row records verification status
- official corrections can override a Wikidata candidate without deleting historical evidence
- schema migrations are committed to Git
- D1 Time Travel is the first-line accidental-change recovery mechanism

# Cost target

Initial target: **₹0 / $0 recurring platform cost** while within free-tier limits.

Expected initial services:
- GitHub public-repo Actions: free standard hosted-runner usage
- Cloudflare Workers Free
- Cloudflare D1 Free
- optional Cloudflare R2 Free allocation later
- YouTube Data API default quota
- Wikidata/Wikimedia public APIs and dumps within policy

Upgrade only after measured need. Cloudflare Workers Paid is the preferred first infrastructure upgrade before adding more vendors.

# Required external access before production deployment

## Required

1. **Cloudflare account access**
   - Account ID
   - API token usable by CI for Workers deployment and D1 management
   - preferably a narrowly scoped token rather than a global API key

2. **Google Cloud / YouTube Data API key**
   - required only when official YouTube monitoring is enabled

## Optional later

- custom domain / Cloudflare DNS zone
- Wikimedia Enterprise free account/token if we need more predictable Wikimedia API access
- R2 bucket when rights-safe media ingestion begins

# Implementation sequence

1. Scaffold React Router v8 + TypeScript + Cloudflare Workers project.
2. Add Tailwind, shadcn/ui and Motion.
3. Create D1 database and migrations for the minimal schema.
4. Build Wikidata bootstrap importer against local/remote D1.
5. Build Home / Calendar / Movie / Search using seeded data.
6. Establish the cinematic visual system and responsive motion.
7. Deploy preview to Cloudflare.
8. Add YouTube official-channel monitoring after API key is available.
9. Add small manual verification/admin path for corrections.
10. Only then expand catalogue/source coverage.

# Rule for future scope requests

A feature may enter V1 only if it directly improves one of:

- movie-name coverage
- release-date correctness/freshness
- premium user experience

Everything else remains post-V1 by default.
