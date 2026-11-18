# Architecture v1.0 — proposed stack, approved for foundation

## Stack

- Mobile: Expo SDK 58, React Native 0.88, TypeScript, Expo Router, Reanimated, FlashList, Zustand, TanStack Query; Skia only where justified.
- Backend: modular Hono API on Cloudflare Workers.
- Database: PostgreSQL (proposed Neon free-tier pilot), versioned SQL foundation and Drizzle integration after installing/verifying dependencies.
- Read access: indexed SQL, paginated endpoints and explicit cache invalidation.
- Imports: bounded Node.js jobs, no blind bulk import.
- Quality: Node tests, type checks, API/database integration checks, Android build and physical acceptance before release.
- Source of truth: backend canonical title IDs and field-level provenance; the mobile app never connects directly to the database.

## End-to-end backend flow

~~~mermaid
flowchart TD
  U["Client"] --> A["Cloudflare Worker / Hono"]
  A --> V["Request validation + limits"]
  V --> C{"Public read cache hit?"}
  C -->|yes| R["Typed JSON response"]
  C -->|no| D{"Domain route"}
  D --> T["Catalogue/Identity/Language"]
  D --> S["Search/Discovery/Recommendations"]
  D --> H["Historical release engine"]
  D --> O["Provider availability engine"]
  T --> DB["PostgreSQL repository layer"]
  S --> DB
  H --> DB
  O --> DB
  DB --> P[("PostgreSQL: normalized catalogue")]
  P --> Q["Validate fields + provenance"]
  Q --> R
  R --> U
~~~

## End-to-end frontend flow

~~~mermaid
flowchart TD
  S["App launch"] --> L["Read locally saved preferences"]
  L --> N{"First launch?"}
  N -->|yes| W["Welcome -> languages -> genres"]
  W --> P["Persist guest preferences"]
  N -->|no| H["Home"]
  P --> H
  H --> F{"Navigation"}
  F --> D["Discover"]
  F --> X["Search"]
  F --> T["On This Day"]
  F --> G["Settings / preference changes"]
  F --> M["Personalized home collections"]
  D --> Q["Title detail"]
  X --> Q
  T --> Q
  M --> Q
  Q --> R["Verified metadata / OTT / similar"]
  R --> Q
  G --> H
  H --> A{"Network available?"}
  A -->|yes| B["Validated paginated API / query cache"]
  A -->|no| C["Show last-known cached data or honest empty state"]
  B --> H
  C --> H
~~~

## Metadata ingestion

~~~mermaid
flowchart TD
  A["Permitted source"] --> B["Source license + quota check"]
  B --> C{"Approved?"}
  C -->|no| STOP["Reject"]
  C -->|yes| D["Fetch bounded batch"]
  D --> E["Store source reference and raw staging record"]
  E --> F["Normalize identity, language, release types"]
  F --> G["Canonical external-ID match"]
  G --> H{"Conflict or ambiguous identity?"}
  H -->|yes| R["Review queue; do not publish"]
  H -->|no| I["Validate and trace field provenance"]
  I --> J{"Publishable?"}
  J -->|no| R
  J -->|yes| K["Transactional upsert / idempotency"]
  K --> L["Update indexes and invalidate affected caches"]
  L --> M["Publish to catalogue API"]
~~~

## Domain boundaries

- Catalogue engine: canonical title details and constrained pagination.
- Identity engine: authoritative external-ID matching, ambiguous-alias review.
- Language engine: original language vs translated title vs dubbing information.
- Search engine: exact/alias, then prefix and fuzzy; use pg_trgm only after performance testing.
- Discovery engine: filters/collections, paginated and deterministic.
- Recommendation engine: explainable language/genre ranking, no paid AI.
- Historical release engine: only explicitly verified original premieres for the default On This Day view.
- OTT engine: offers by provider, territory, verified date; stale is never falsely presented as current.
- Metadata ingestion and data-quality engines: separate from public API, staged and auditable.
- Operations/health: controlled diagnostics, no public secret exposure.

## Network and failure behavior

Guest preferences live locally. No email/sign-in is required. The frontend uses an isolated API client; failures show cached results if clearly marked or retryable error states. API errors have stable sanitized envelopes. SQL parameters and bounded result limits are mandatory. Administrative mutation endpoints are not part of the public worker.

## Architecture gates

- No claim of live database, working API, installed dependencies, native build or deployment without evidence.
- Free-tier quotas are finite: Worker request/CPU caps, Neon storage/compute/transfer, GitHub Actions usage. Free capacity is not the same as guaranteed free global scale.
- Maintain controlled release gates and document all major trade-offs in ADRs.
