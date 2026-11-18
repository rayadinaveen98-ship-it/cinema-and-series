# Cinema & Series roadmap

## Stage 00 — APPROVED / repository documentation in progress

Product contract, ADR, architecture flowcharts, data policy, free-tier guardrails and acceptance checklist.

## Stage 01 — FOUNDATION IMPLEMENTATION IN PROGRESS

Repository conventions, dependency-free domain engine rules, initial PostgreSQL schema and synthetic automated tests. API and mobile are scaffolds only.

Stage 01 EXIT requires:
- all foundation CI passing and versioned tests;
- dependency/TypeScript and API builds verified after real package installation;
- reproducible database migration and rollback checked against disposable PostgreSQL;
- approximately 60 manually/source-verified films/series across language groups;
- duplicate and incorrect-date protection demonstrated;
- provider terms audited.

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
