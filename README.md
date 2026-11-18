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
- jobs — curated RRR record, source-validation preflight, and **transactional stage-only PostgreSQL persistence** with review tickets and audit; no network importer or auto-publication.
- docs — product contract, architecture, decisions, roadmap, quality gates.

## Running the initial tests

Use Node 22.13 or newer:

    node --experimental-strip-types --test packages/domain/tests/*.test.mts

Tests use synthetic fixtures with no credentials. API, ingestion preflight and PostgreSQL integration are exercised by GitHub Actions; a real mobile build and public deployment are still pending.

## Current stage

Stage 00 documentation is recorded; Stage 01 is in progress. Neon Free pilot holds one curated RRR record, and staging schema migrations 0001–0004 are applied. Bulk ingestion, full catalogue certification, native app, public API deployment and APK builds remain gated. See docs/roadmap/ROADMAP.md.
