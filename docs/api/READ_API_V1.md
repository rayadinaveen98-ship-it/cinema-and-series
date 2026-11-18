# API contract v1 — Stage 01 checkpoint

Status: implementation tested in CI; no hosted endpoint.

## Read endpoints

GET /v1/health — simple service liveness only.
GET /v1/titles — bounded cursor catalogue, original language/genre/type filters.
GET /v1/titles/:id — canonical title, localized names, source-linked release events and provider statuses.
GET /v1/search?q=RRR — exact and substring canonical/alias search.
GET /v1/releases/on-this-day?month=3&day=25 — verified original premieres; excludes OTT and territory-specific release types.
GET /v1/languages — language directory.
GET /v1/genres — genre directory.

Success envelope: JSON object with data; list additionally has page.nextCursor.
Error envelope: JSON object with error.code and error.message.

## Input and consistency rules

- All data endpoints require a secret injected through a Worker binding; no credential is committed.
- Only published titles are returned.
- Invalid inputs are rejected before database access; list limit <= 50, search limit <= 30, UUID cursor only.
- Production source provenance is preserved for release events.
- An unknown provider's present-day availability remains unverified, even if the historical digital premiere is confirmed.
- SQL is parameterized through Drizzle.
- Recommendations and user write endpoints are not exposed until verified; no dummy success responses.

## Evidence and limits

CI includes actual package install, TypeScript typecheck, Hono synthetic HTTP tests, Worker bundle dry-run, and disposable PostgreSQL migration tests.
No live Hono-to-Neon connection, rate-limit load test, cache invalidation, user account, Android build, or production deployment is certified.
