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

- apps/api — planned Hono Cloudflare Worker; currently health-only scaffold.
- apps/mobile — planned Expo SDK 58 React Native Android application; no UI implementation yet.
- packages/domain — dependency-free TypeScript validation, identity, historical releases, and recommendation rules.
- packages/db — normalized PostgreSQL migrations 0001/0002, verified in disposable CI and applied to isolated Neon free pilot.
- jobs — curated source-traceable RRR pilot record; automated bounded ingestion still pending.
- docs — product contract, architecture, decisions, roadmap, quality gates.

## Running the initial tests

Use Node 22.13 or newer:

    node --experimental-strip-types --test packages/domain/tests/*.test.mts

These tests use **synthetic fixtures**, no real movie imports, accounts or cloud service credentials. A separate dependency-backed API/mobile build will be added and verified before any deployment.

## Current stage

Stage 00 documentation is recorded; Stage 01 is in progress. An isolated Neon Free pilot database exists with one curated RRR record. Bulk ingestion, full catalogue certification, native app, public API deployment and APK builds remain gated. See docs/roadmap/ROADMAP.md.
