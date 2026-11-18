# Database migration v0001 — NOT APPLIED

0001_catalogue.sql defines initial normalized PostgreSQL tables.

## Provenance and scope

- A title has a canonical UUID and original language relations.
- Localized/alternative titles cannot create duplicate canonical films.
- Original premieres, regional theatrical releases, OTT premieres and rereleases are separate release events.
- Provider offers carry territory and time-stamped verification.
- External IDs are unique per source, with staging and review tables for conservative imports.
- Traceable source records and field provenance allow corrections.

## Migration safety gate

SQL has NOT been executed against Neon or disposable PostgreSQL. Before any hosted database migration:
1. Validate schema in isolated disposable PostgreSQL.
2. Confirm extension support and run application queries/explain plans.
3. Test idempotent imports, invalid data, uniqueness and transaction rollback.
4. Establish database backup/restore and non-destructive migration rules.
5. Write a reviewed upgrade/rollback playbook.

Planned Drizzle ORM integration follows this tested SQL foundation. Do not create manual divergent schemas without a migration review.

## Known future additions

Series seasons/episodes, verified dubbed audio tracks, editorial collection management and optional personal account tables are deferred until core catalogue certification.
