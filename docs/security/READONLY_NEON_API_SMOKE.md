# Stage 01: credential-gated Hono/Neon HTTP smoke

Status: RUNNER IMPLEMENTED; live connection BLOCKED pending security approval.

The existing cinema_owner Neon login has administrative privileges and MUST NEVER be used for this app's read-only API or smoke. The isolated cinema_pilot database currently has 13 sourced titles, 11 films and two series; direct SQL results do not certify real Hono-Neon HTTP requests.

## Least-privilege role (PROPOSED, not applied)

Create a separate cinema_api_reader LOGIN with a strong privately generated secret. Do not share or commit a database URL/password. It must NOT be a member of neon_superuser or any administrative role.

Required: CONNECT to cinema_pilot, USAGE on public, SELECT only on:
titles, title_languages, title_genres, title_localizations,
genres, languages, release_events, series_debuts,
source_records, streaming_offers, providers.

Never grant INSERT/UPDATE/DELETE/TRUNCATE, CREATE, or SELECT on private ingestion_runs, staging_records, review_queue, catalogue_audit_log. Do not grant SELECT on all public tables. A separately authorized operator can apply this permissions-only SQL AFTER creating a safe role:

```sql
GRANT CONNECT ON DATABASE cinema_pilot TO cinema_api_reader;
GRANT USAGE ON SCHEMA public TO cinema_api_reader;
GRANT SELECT ON TABLE
 public.titles, public.title_languages, public.title_genres,
 public.title_localizations, public.genres, public.languages,
 public.release_events, public.series_debuts, public.source_records,
 public.streaming_offers, public.providers
TO cinema_api_reader;
ALTER ROLE cinema_api_reader SET statement_timeout = '5s';
```

This PR does not execute these grants. The source API's connection guard also verifies the effective privileges before any catalogue request, and rejects owner credentials.

## Real HTTP-driver smoke (NOT YET RUN)

With the new role approved, an operator places the scoped read-only connection string in a trusted environment variable CINEMA_SMOKE_DATABASE_URL. No command-line password, chat message, environment file committed to Git, CI log, or public PR attachment may contain the secret.

```bash
pnpm install --no-frozen-lockfile
pnpm --filter @cinema/api run test
pnpm --filter @cinema/api run typecheck
# Configure CINEMA_SMOKE_DATABASE_URL privately (never paste or print it)
pnpm --filter @cinema/api run smoke:neon
```

The runner calls real Hono routes with the real Drizzle neon-http repository. It validates:
- read-only role identity and permission matrix BEFORE database queries
- browse pagination and Korean/series filters
- original-script Japanese alias search
- November 2 historical theatrical release
- Dark's historic series debut separate from current streaming offers
- guest recommendation/similar-title source exclusion
- language/genre directory and 400/404 response behavior

It performs no writes, creates no listener, and does not deploy a Cloudflare Worker. Standard PR CI runs only synthetic negative tests of the URL and access gate; PR code must never receive a live secret.

## Evidence and remaining gates

To certify the next step, obtain explicit approval for the separate read-only identity, execute the runner in a trusted private environment, record passing case names and commit SHA without secrets, and re-check hosted title counts. A successful in-process test would establish Hono/Neon HTTP integration, NOT public Cloudflare runtime, realistic p95, physical Android, or release readiness. Those require separately approved tests.

Current state: 13-title direct Neon SQL VERIFIED. Real Hono -> Neon HTTP run BLOCKED. Worker deployment, GitHub secret provisioning, and APK have NOT occurred.
