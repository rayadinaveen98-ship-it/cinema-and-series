# Cinema & Series roadmap

## Stage 00 — IMPLEMENTED (documents committed; awaiting PR integration)

Product contract, ADR, architecture flowcharts, data policy, free-tier guardrails and acceptance checklist.

## Stage 01 — FOUNDATION IMPLEMENTATION IN PROGRESS

Repository conventions, dependency-free domain tests, TypeScript typecheck, SQL migrations 0001/0002 and disposable PostgreSQL integration passed in CI. Neon Free pilot created in aws-ap-southeast-1 (project plain-violet-46536395; database cinema_pilot), with verified migration applied and 1 source-traced RRR sample. Reapplying curated seed created no duplicates. Read-only API is implemented, typechecked, request-tested and Worker bundle-checked, but is NOT DEPLOYED and has not performed a live Worker-to-Neon HTTP query. Mobile is not implemented. Personalized recommendations and similar-title reads have passed CI. The stage-only ingestion evaluator also passed strict TypeScript and quarantine tests; no import runs or published changes were made.

Stage 01 EXIT requires:
- all foundation CI passing and versioned tests;
- dependency/TypeScript and API builds verified after real package installation;
- reproducible database migration and rollback checked against disposable PostgreSQL;
- approximately 60 manually/source-verified films/series across language groups;
- duplicate and incorrect-date protection demonstrated;
- provider terms audited;
- stage-only ingestion upgraded to a reviewed, transactional, persisted importer with checkpoint/rollback certification and quotas;
- read-only discovery performance checked on multi-language catalogue, not just the single RRR record.

## Stage 02 — NOT STARTED

Design system: premium title holders, onboarding, home, discovery, search, historical releases, details; accessibility and performance specifications. Founder visual approval before full UI build.

## Stage 03 — NOT STARTED

Implement actual API, mobile views, preference persistence, language/genre recommendation, historical release queries, pagination and error states.

## Stage 04 — NOT STARTED

Batched imports and size/performance measurements with credible multilingual data and provider verification.

## Stage 05 — NOT STARTED

Build versioned APK; CI + real Android phone/tablet tests, visual QA, recovery testing and stable-candidate record.

## Stage 06 — NOT STARTED

Separate launch readiness/security/attribution/budget review and explicit release approval.

## Zero-rupee gate

No infrastructure provisioning or paid tier upgrade without a separate authorization. Free tier thresholds must be monitored rather than silently exceeded.

## Latest development checkpoint — 2026-11-18

Implemented and CI-verified: guest-first recommendation API, related-title API, original-premiere earlier-year cutoff and stage-only Wikidata source preflight. Four CI jobs green on commit 5963287f9. Neon read-only pilot confirms RRR relevance score 8 for original language Telugu + action genre; since the pilot contains only RRR, More Like This is honestly empty.

Still NOT implemented or approved for public launch: transactional persisted importer, human review workflow, approximately 59 more curated pilot titles, direct Hono-to-Neon live integration, large-dataset latency tests, a released Worker and any mobile APK. Do not count Stage 01 as complete or Stage 02 as started.
