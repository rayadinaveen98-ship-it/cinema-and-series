# Ingestion jobs — initial curated proof only

- curated/0001_rrr_verified.sql provides one manually cross-checked RRR record, using bare facts and source URLs only.
- Source identity: Wikidata Q60424165; ZEE5 official movie page.
- It distinguishes Indian original theatrical release (2022-03-25) from ZEE5 digital premiere (2022-05-20).
- Current regional streaming offer is explicitly UNVERIFIED, preventing a false current-availability claim.
- Re-running the seed was checked for idempotency in the Neon free pilot.

A live/automatic importer has NOT been built. Required next work: license-reviewed source connector, bounded paging, checkpointing, normalization, identity review queue, transactional upsert, audit, and rate-limits/backoff. Never treat source text as trusted instructions.
