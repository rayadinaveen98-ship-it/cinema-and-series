# Cinema & Series

Android-first, multilingual cinema and series discovery database. **Foundation stage — not yet a released app.**

## Principles

- Accurate, traceable metadata before catalogue volume.
- Original-release dates stay separate from regional, rerelease, and OTT events.
- Original languages and localized titles are separate attributes.
- Guest-first language/genre preferences; no mandatory account.
- Text-based title holders instead of copyrighted poster artwork.
- A zero-rupee pilot budget; no paid resource may be provisioned or upgraded without explicit approval.
- No production movie/series records without verifiable permitted sources.

## Repository layout

- apps/api — Hono/Drizzle pilot API for browsing, search, details, historical releases, recommendations and related titles. Worker bundle tested, NOT deployed.
- apps/mobile — planned Expo SDK 58 React Native Android application; no UI implementation yet.
- packages/domain — dependency-free TypeScript validation, identity, historical releases, and recommendation rules.
- packages/db — normalized PostgreSQL migrations and Drizzle read-model mapping, checked with disposable CI and applied to isolated Neon Free pilot.
- jobs — curated RRR record, indexed identity lookup, bounded source fetch-only client, unverified field-evidence assessment, transactional staging and nonpublishing review audit; no scheduled import or publication.
- docs — product contract, architecture, decisions, roadmap, quality gates.

## Running the initial tests

Use Node 22.13 or newer:

    node --experimental-strip-types --test packages/domain/tests/*.test.mts

Tests use synthetic fixtures with no credentials. API, ingestion preflight and PostgreSQL integration are exercised by GitHub Actions; a real mobile build and public deployment are still pending.

## Current stage

Stage 00 documentation is recorded; Stage 01 is in progress. Neon Free pilot holds **13 source-reviewed titles (11 films, 2 series) across 10 original languages**, with migrations 0001–0005 applied. Bulk ingestion, remaining approximately 47 pilot titles, full catalogue certification, native app, public API deployment and APK builds remain gated. See docs/roadmap/ROADMAP.md.

## Stage 01 discovery scaling

The read-only Drizzle catalogue now uses a canonical/alias UNION for title search and grouped language/genre matches for recommendations. In rollback-only disposable PostgreSQL tests, 10,000 synthetic titles exercised these query shapes and a full result-parity regression. No Worker deployment or Android API integration has occurred. Details: docs/verification/2026-11-18-discovery-scale.md.

## Live API safety gate

The optional in-process Hono-to-Neon smoke runner is implemented and synthetically tested, but has **not yet connected** to the hosted database: a dedicated scoped read-only role now exists with verified grants, but its login password has not been activated and a live HTTP smoke has not run. Owner credentials are intentionally forbidden, and draft-PR CI receives no secrets. See docs/security/READONLY_NEON_API_SMOKE.md for the explicit permissions and approval gate.
