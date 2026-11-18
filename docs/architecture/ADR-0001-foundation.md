# ADR-0001 — Cinema & Series foundation

Date: 2026-11-18
Status: APPROVED for foundation implementation; production readiness NOT established.

Decision:
- Use a TypeScript monorepo and modular API rather than paid microservices.
- Android-first with React Native and Expo SDK 58, with responsive phone/tablet experiences.
- Choose PostgreSQL as canonical relational database. A Neon free-tier project is a candidate, not yet provisioned.
- Hono/Cloudflare Workers are the preferred API runtime, not yet deployed.
- No persistent identity account in the initial guest-first product.
- No posters or asset-download pipeline in v1.
- Start data correctness with reusable domain rules and synthetic fixtures; source verified real records separately.

Reasons: region/language-aware catalogue, historically accurate release events, operational simplicity, cost discipline, and ability to expand without rewriting title identity.

Alternatives:
- Cloudflare D1: simpler Worker integration but less suitable for the desired relational multilingual and fuzzy-search roadmap.
- Native Kotlin: high-quality Android UI, but less direct cross-platform code sharing.
- Flutter: strong visual customization, but current choice favors shared TypeScript/domain contracts.
- External AI and search SaaS: not justified for the pilot.

Risks: free-tier caps, importer licensing, stale provider data, remote startup/cold connections, Android animation cost.

Revisit when real-device benchmarks or catalogue-size measurements contradict the assumptions.
