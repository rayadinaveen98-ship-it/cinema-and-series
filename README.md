# Cinema and Series

**Cinema and Series** is now building a deliberately focused first product: an India-first movie release experience centered on **movie names, release dates, and premium cinematic presentation**.

The repository also preserves a much deeper long-term research foundation for a future world-cinema knowledge platform. That research remains valuable reference material, but it no longer blocks the active V1.

## Active V1

The current implementation contract is:

1. movie names;
2. reliable release dates;
3. premium cinematic UI and release-calendar experience.

See [`docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md`](docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md) for the authoritative active V1 scope, stack and implementation sequence.

## Locked active stack

- React Router v8 + React + TypeScript
- Tailwind CSS + shadcn/ui + Motion
- Cloudflare Workers for full-stack hosting/runtime
- Cloudflare D1 for the V1 catalogue
- GitHub Actions for scheduled Wikidata/official-source ingestion
- Wikidata as the open catalogue seed
- first-party/official evidence for release-date verification
- YouTube Data API for approved official-channel monitoring once credentials are available
- Cloudflare R2 only later for rights-safe media if needed

## V1 data principle

Production pages read our own database. They do not depend on live Wikidata, YouTube or other upstream providers.

Wikidata provides discovery/base data; official production houses, studios, distributors, movie sites and approved official channels provide higher-authority release-date evidence. External-source failures may delay refreshes but must not break the public product.

## Future platform research

The existing source, domain, identity, provenance, canonicalization, multilingual, release-history and validation research is retained for future expansion toward a substantially deeper cinema/television database.

The previous ~1,000-case research/validation program is **not an implementation prerequisite for the active fast-track V1**.

## Repository navigation

For active implementation, start with:

1. [`docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md`](docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md)
2. [`docs/02-sources/INITIAL_PRODUCTION_SOURCE_BASELINE.md`](docs/02-sources/INITIAL_PRODUCTION_SOURCE_BASELINE.md)

Use [`START_HERE.md`](START_HERE.md) when working on the preserved long-term research platform.

## Product status

Fast-track V1: **ACTIVE / IMPLEMENTATION AUTHORIZED**  
Long-term research foundation: **PRESERVED**  
Target initial platform cost: **₹0 / $0 while within free-tier limits**
