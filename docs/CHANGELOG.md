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
