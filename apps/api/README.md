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
