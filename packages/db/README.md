# Database — Neon Free pilot deployed (not production)

Migrations 0001_catalogue.sql and 0002_provider_release_link.sql are additive and were verified with PostgreSQL 17 on GitHub Actions disposable service, then applied to the isolated Neon pilot.

## Verified evidence, 2026-11-18

- Neon project: plain-violet-46536395, database cinema_pilot, region aws-ap-southeast-1.
- PostgreSQL 17.12; 18 normalized tables exist and pg_trgm installed.
- One curated title RRR, two historical release events, one current-offer record marked UNVERIFIED, two source records, six provenance links.
- Running jobs/curated/0001_rrr_verified.sql a second time did not create duplicate records.
- Original release 2022-03-25 is returned by original-premiere query; ZEE5 OTT premiere 2022-05-20 is excluded from that historical original-premiere query.

## Boundaries

No public API or mobile consumer is deployed. The curated seed does not prove bulk source licensing or a full 60-title pilot. Drizzle ORM adapter, schema diff check, tested restore/rollback, and volume benchmarks remain pending. No production credentials are in GitHub. The pilot remains within the connected Neon Free organization; usage quotas still apply.

Never run destructive SQL against this pilot without explicit approval. Future migrations must be additive and separately checked against a disposable PostgreSQL instance first.

## Migrations 0003 / 0004 — applied to Neon Free pilot

0003 adds optional batch_key/payload_digest on ingestion_runs with unique source+key constraint; unique stage positions and unique review reason per staged row. It is additive and does not touch published titles.

0004 allows NULL source_records.retrieved_at so an unverified candidate reference is not falsely marked as fetched. The new stage writer explicitly stores NULL; existing RRR evidence timestamps were preserved. CI validates disposable PostgreSQL migration and staging transaction safety.

Manual Neon migration note: do not split SQL on semicolons without a SQL-aware parser; semicolons inside SQL quoted comments must remain intact. The first attempted 0004 transaction failed and rolled back; a correctly parsed two-statement transaction applied successfully. Verified counts: 1 title, 2 release events, 0 ingestion runs, 0 staged records, 0 review tickets.
