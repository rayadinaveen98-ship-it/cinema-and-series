# Change log

## 2026-11-18

- Approved ₹0 pilot architecture and original product foundation.
- Initialized repository (main branch).
- Started feature/foundation-architecture-domain-20261118 for Stage 00 documents and Stage 01 preliminary domain/schema work.
- Added synthetic domain tests, TypeScript compilation and isolated PostgreSQL migration/integrity CI; passed on PR branch.
- Provisioned separate Neon Free pilot (plain-violet-46536395 / cinema_pilot, PostgreSQL 17) without touching existing projects.
- Applied 0001/0002 schema migrations: 18 tables, pg_trgm present.
- Added 1 curated source-traceable RRR film with 2 release events, 2 source records and 6 field-evidence links. Duplicate seed rerun verified idempotent.
- Historical query returns original premiere 2022-03-25 and excludes OTT premiere 2022-05-20 from that calendar.
- No Cloudflare Worker deployed, no app UI/APK built and no paid services provisioned.

- Implemented Hono/Drizzle read-only API: title listing, details, search, verified original-release history, language and genre directories. API request tests, typecheck and Worker dry-run passed.
- Fixed pnpm CI workspace setup and Node 22 TypeScript strip-mode compatibility; all latest jobs passed.
- No Cloudflare Worker deployment, no Android UI/APK, no paid services.

- Added guest-first POST recommendation ranking and GET similar-title API, with input caps, error cases and deterministic tests.
- Added stage-only Wikidata source preflight, 40-record safety limit, duplicate/alias/type conflict quarantine and its independent CI job.
- Latest four-job CI passed (run 44236729306); Neon remains one RRR record without bulk importer writes.

- Fixed On This Day to exclude same-year and future original-premiere dates; verified through domain and API tests.
- All four jobs green on historical-cutoff commit 5963287f9 (CI runs 44237255769, 44237261186). PR remains draft and no new movie records were published.
