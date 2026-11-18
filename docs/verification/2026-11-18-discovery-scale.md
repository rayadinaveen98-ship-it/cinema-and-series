# Cinema & Series — SQL discovery scale evidence, 2026-11-18

**Status:** implemented and tested in the draft PR. Not a deployed Worker, network benchmark, physical Android test or commercial latency guarantee.

## Setup

PostgreSQL 17 in GitHub Actions, migrations 0001–0005, existing 13 curated titles, then 10,000 synthetic movies/TV records created in a single test transaction and rolled back. The generated data includes 8,000 film original-premiere events and 2,000 series-debut events. SQL benchmarks use EXPLAIN ANALYZE with buffers and timing overhead disabled; each row below is one observed server execution, not an aggregate.

| Query | Original SQL | Optimized SQL |
|---|---:|---:|
| English alias/canonical search | 9.393 ms | 4.706 ms |
| Guest language/genre recommendations | 65.582 ms | 12.824 ms |
| Original-language browse | 0.147 ms | 0.079 ms |
| Film-only original premiere anniversary | 0.154 ms | 0.171 ms |

The optimization uses a canonical+localization UNION for search and grouped language/genre matches rather than a per-title correlated genre count. The full synthetic catalogue is compared against the prior SQL for language/genre hit counts, score, same-type bonus and source exclusion; differences fail CI. Additional checks ensure matching the Spirited Away English alias reaches its original Japanese-title record, RRR appears once, and percent/underscore queries stay literal. All generated records disappear on ROLLBACK.

## Direct Neon read-only evidence

Using an isolated pilot of 13 published titles, direct SQL returned the Japanese original through the Spirited Away alias, Korean thriller matches for Parasite and Squid Game, the November 2 Intouchables anniversary, and the correctly separated first-season dates for Dark and Squid Game. Current hosted catalogue counts remained unchanged. These are NOT executed via a deployed Hono/Cloudflare Worker.

## Source evidence and boundary

Final implementation commit 92ef512fd87e3813b9b8278ce0d05b2e4ef172be; runs 44267226381 and 44267236149 passed all four GitHub Actions jobs. No Neon writes, migrations, new paid services, public deployments, APKs, merges or actual-device certifications.

Stage 01 remains open for approximately 47 more source-verified titles, direct authenticated Worker-to-Neon request smoke checks, representative larger-catalogue p50/p95 and regional latency, approved operator roles and source-terms checks.
