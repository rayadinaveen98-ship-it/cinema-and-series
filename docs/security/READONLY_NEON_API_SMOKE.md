# Stage 01: credential-gated Hono/Neon HTTP smoke

Status: RUNNER IMPLEMENTED and guard-tested. Dedicated reader CREATED and permission-verified, but PASSWORD ACTIVATION MANUAL and REAL HTTP SMOKE NOT EXECUTED.

The existing cinema_owner Neon login has administrative privileges and MUST NEVER be used for this app's read-only API or smoke. The isolated cinema_pilot database currently has 13 sourced titles, 11 films and two series; direct SQL results do not certify real Hono-Neon HTTP requests.

## Least-privilege role (CREATED, password activation pending)

The cinema_api_reader role now exists on the Neon pilot's main branch in cinema_pilot. It was created using SQL with LOGIN but no initial password, without neon_superuser membership. The account is not usable for the smoke until its password is generated privately by Neon Console. Do not share or commit a database URL/password.

Required: CONNECT to cinema_pilot, USAGE on public, SELECT only on:
titles, title_languages, title_genres, title_localizations,
genres, languages, release_events, series_debuts,
source_records, streaming_offers, providers.

Never grant INSERT/UPDATE/DELETE/TRUNCATE, CREATE, or SELECT on private ingestion_runs, staging_records, review_queue, catalogue_audit_log. Do not grant SELECT on all public tables. The following permissions-only SQL was applied and its effective privileges independently verified:

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

This PR contains documentation only; the grants were applied directly to isolated Neon. Verification confirmed: the role has CONNECT, public USAGE, SELECT only on 11 specified catalogue relations, zero INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER, zero CREATE on public, zero role memberships or admin flags, and no SELECT on staging, review, audit or any other non-allowlisted table. The smoke runner re-checks those privileges before issuing catalogue requests.

## Mandatory manual password activation (NOT YET DONE)

1. Open https://console.neon.tech and select Cinema & Series pilot project (project ID plain-violet-46536395), branch main.
2. Under Postgres database, open Roles and find cinema_api_reader, then use Reset password and confirm Reset. This makes Neon generate a new secret privately. The role was deliberately created without a password.
3. Store the generated password in a password manager. Do not paste the password, full connection string, or a screenshot revealing them into ChatGPT or GitHub. Choose role cinema_api_reader and database cinema_pilot in the Connect dialog; ensure the resulting connection string has sslmode=require.
4. Tell us only: 'Reader password activated'. We can then help you run the opt-in smoke on a trusted local environment; do not enable GitHub PR secrets or public Worker deployment.

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

The reader permission setup is now verified. To certify the next step, privately activate its password and execute the runner in a trusted private environment, record passing case names and commit SHA without secrets, and re-check hosted title counts. A successful in-process test would establish Hono/Neon HTTP integration, NOT public Cloudflare runtime, realistic p95, physical Android, or release readiness. Those require separately approved tests.

Current state: 13-title direct Neon SQL VERIFIED; reader created with correct grants, but login password not activated. Real Hono -> Neon HTTP run BLOCKED; deployment, GitHub secret provisioning, and APK have NOT occurred.
