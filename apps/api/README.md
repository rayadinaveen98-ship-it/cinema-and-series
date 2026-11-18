# Read-only pilot API

Hono + TypeScript + Drizzle Neon HTTP backend. Implemented and CI-verified, but not deployed to Cloudflare. The existing Neon Free pilot is separate.

## Available paths

- GET /v1/health: liveness only; catalogueReady is deliberately false until full readiness certification.
- GET /v1/titles: paginated published catalogue, limit 1-50, optional UUID cursor, type, original language and genre.
- GET /v1/titles/:id: published title, original languages, genres, localized titles, source-linked release events and streaming-offer verification state.
- GET /v1/search?q=RRR: exact/substring title and alias lookup, limit 1-30. Fuzzy spelling ranking remains future work.
- GET /v1/releases/on-this-day?month=3&day=25: verified original premieres only, not OTT/regional events.
- GET /v1/languages and /v1/genres: reference directories.
- POST /v1/recommendations: validated guest language/genre preferences; max 4 KB JSON, max 8 languages/12 genres, ranked and explainable results; no-store caching.
- GET /v1/titles/:id/similar: similar published titles by original language and genres; excludes the source title and returns 404 for unknown canonical IDs.

Every data endpoint returns controlled 503 when the DATABASE_URL secret is absent; no dummy results. Bad queries yield 400, unrecognized routes 404, unexpected errors 500 with credential-safe messages.

## Run checks in the repository

    pnpm install --no-frozen-lockfile
    pnpm --filter @cinema/api run typecheck
    pnpm --filter @cinema/api run test
    pnpm --filter @cinema/api run build:check

Test data is synthetic and no Neon password is needed. All three have passed in GitHub Actions.

## Security boundary

Never embed DATABASE_URL in the Android app or version control. For a future hosted Cloudflare Worker, configure this via encrypted Worker secrets. The free pilot database is not yet connected to a deployed Worker.

## Incomplete

Verified live OTT checks, scheduled/automatic ingestion, authenticated staging/review endpoints, request rate limiting, hosted Worker-to-Neon integration, load benchmarks and Android app remain unimplemented. No APK exists.


## Film vs series chronology

Title detail reads combine the original `release_events` movie timeline and the new additive `series_debuts` table, returning first-season launches with `kind: "series_debut"`. Movie On This Day continues to require a verified `original_premiere` on a movie, excludes streaming/series launch events and future/current-year events. Historical Netflix series provider names are provenance only, not current OTT offers. This code is typechecked, bundled and contract tested; no public Worker is deployed.

## Stage 01 indexed search and ranking

Search now unions source canonical-title and localization-title matches, de-duplicating a title with several matching aliases and using the existing lowercase trigram indexes for substring matching. User-supplied percent, underscore and backslash characters are escaped as literals. Guest recommendations and More Like This now group matched languages and genres before scoring, preserving language +5, genre +3 per match, same type +2 for related titles, source exclusion and stable ID tie-breaks. Synthetic database SQL parity checks passed against the previous algorithm across 10,000 generated records.

This is database SQL verification, NOT an end-to-end Cloudflare Worker connected to hosted Neon; encrypted connection setup, operational latency and Android testing remain open gates.

## Secure real Neon HTTP smoke (not yet run)

A new **opt-in** command exercises the actual Hono API, Drizzle/Neon HTTP adapter and the isolated Neon pilot without deploying a Worker:

    pnpm --filter @cinema/api run smoke:neon

It requires `CINEMA_SMOKE_DATABASE_URL` in the executing process environment, using the dedicated `cinema_api_reader` role on `cinema_pilot`, TLS, and a `*.neon.tech` hostname. The command fails closed without it, validates database read-only permissions, refuses owner credentials, and prints only pass/fail test labels. **Do not paste the URL into chat, PR descriptions, logs, or source files.**

This is not run in automatic PR CI because unreviewed PR code must not be given an authenticated database credential. Tests of the URL/permission guards use synthetic inputs and run automatically as part of `pnpm test`; the real smoke command stays separately authorized. Setup and acceptance criteria are in `docs/security/READONLY_NEON_API_SMOKE.md`. Even a passing smoke would test local/in-process Hono-to-Neon HTTP, not a deployed Cloudflare Worker or physical Android device.
