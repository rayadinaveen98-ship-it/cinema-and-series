# Cinema & Series — Phase 2 / Gate 1: source-backed UX and accessibility audit

**Date:** 2026-10-18
**Basis:** `main` at `d74d06aa09cc44c94e04c24e7a3c40aee7864cdc`, after the +10K Indian-film growth milestone and D1 quota mitigation.
**Scope:** Currently deployed *fast-track V1* React interface: Home, Movies, Series, Upcoming, card/detail flows, API loading behavior, mobile layout rules and navigation.
**Type:** **Static source and interaction-path assessment, NOT a screenshot/visual-compliance audit.** A browser/screenshot pass remains required before Phase 2 UI sign-off. Production D1 was daily-read-quota paused during source inspection. No production DB queries or D1 writes were performed for this review.

## Executive finding

The V1 has a coherent basic content model, consistent reusable cards, image-error fallbacks, debounced search, stable "Load more" for Movies/Series, and increasingly honest source/verification messaging. The immediate problem is **the app sometimes appears empty or complete when it is neither**. Reliability and accessibility need correction before a broad aesthetic redesign.

### Current route contract and scope decision

`src/main.tsx` uses `HashRouter`; `src/App.tsx:484-498` defines only `/`, `/movies`, `/series`, and `/upcoming`. Browser deep links must use `/#/movies`, `/#/series`, `/#/upcoming` unless routing changes. A plain `/movies` URL can load the SPA at its Home hash route rather than Movies.

The previously discussed **Today / OTT / Radar** experiences are **not implemented as routes in this active V1**. This is an explicit **scope reconciliation item**, not evidence those designs were deleted. `docs/10-execution/V1_FAST_TRACK_PRODUCT_AND_TECH_LOCK.md` currently defers streaming availability and a native Android app. Do not mix the deferred feature roadmap into the core V1 visual cleanup without an explicit product decision.

## Walkthrough and acceptance state (from source, not visual screenshots)

| Step | User flow / code reference | Source-level health | What remains |
|---|---|---|---|
| 01 | Landing/Home: `App.tsx:369-395` | **At risk** | Hero and 3 rails depend on swallowed fetch failures, zero counts may be displayed |
| 02 | Navigate via desktop/mobile: `App.tsx:264-288,484-498` | **Mostly structured** | Hash deep links, tiny mobile labels; keyboard focus-state test needed |
| 03 | Movie search/filter/browse: `App.tsx:401-431` | **Functional foundation** | Search labelling, touch target sizes, missing/failed counts |
| 04 | Movie card → movie details: `App.tsx:300-312,329-347` | **Needs accessibility work** | Dialog naming/focus/close label, missing hero fallback selector |
| 05 | Series search/filter/browse: `App.tsx:433-462` | **Functional foundation** | Same filter labelling/touch issues; keep existing pagination |
| 06 | Series card → series details: `App.tsx:313-323,349-367` | **Needs accessibility work** | Dialog focus trap/return, labels, source wording |
| 07 | Upcoming 7/30/all window: `App.tsx:464-480` | **Incomplete** | Hard 80-record cap, silent errors, no empty state |
| 08 | Quota failure, empty data, mobile: `App.tsx:91-139,144-250`, `app-v2.css` | **Mixed** | Movies/Series show retry; Home/Upcoming silently swallow errors. Visual checks pending |

## Confirmed code findings

Priority **P0** blocks truthful or dependable use; **P1** is serious UX/accessibility; **P2** is polish/efficiency.

| ID | Priority | Observation (grounded source) | Remediation and acceptance condition |
|---|---|---|---|
| UX-01 | **P0** | `useMovies` and `useSeries` swallow fetch errors via `.catch(() => undefined)` (`App.tsx:109-139`). Home and Upcoming use these hooks. | Unify request states with the paginated hooks: clear loading/error/empty/503 and retry. During simulated quota failure, no rail or Upcoming view silently looks like a valid empty list. |
| UX-02 | **P0** | Upcoming fetches `useMovies(query, 80)` and renders those records only (`App.tsx:464-477`). API offers offset pagination; page has no Load more. | Add bounded pagination or next-page control to Upcoming, retaining selected date window and language. Every available page must be reachable; do not imply `All upcoming` equals 80. |
| UX-03 | **P0** | Home and library use `useCounts` initial `{movies:0,series:0,total:0}` and silently catch error (`App.tsx:91-97`); displayed as a real 0 in the hero (`369-395`). | Track count loading/failed separately, show placeholders/error/retry; never imply the catalogue has zero titles when the count query failed. |
| UX-04 | **P1** | Movie/series modals have `role=dialog`, `aria-modal=true`, Esc handling, but no visible `aria-labelledby`, focus placement/trap, or return focus (`253-262,329-367`). Close button text is only `×`. | Name dialogs from title, label the close button, move focus inside, trap tab focus, restore focus to card on close; verify Esc and backdrop click. |
| UX-05 | **P1** | Search uses placeholder-only inputs; filter trigger lacks `aria-expanded`/`aria-controls` (`397-417,433-448`). Upcoming language select lacks an associated label (`475`). Window buttons do not expose pressed state. | Give inputs explicit labels, expose expanded/pressed state, associate panel/control IDs, announce result counts, and verify keyboard-only usage. |
| UX-06 | **P1** | CSS explicitly uses 7–11px text for several metadata and controls, including 8px mobile nav labels; controls often 38px tall (`src/app-v2.css`). | Define readable type scale and touch targets (aim >=44x44 CSS px on mobile), preserve density where helpful, measure contrast and zoom behavior. |
| UX-07 | **P2** | `PosterArtwork(hero)` emits `detail-fallback-letter` (`App.tsx:292-298`), but `app-v2.css` styles the rendered element through `.detail-hero>span`; this **currently does match** the component's direct-child span. The named class has no explicit rule, making styling fragile if markup changes. This is **not a confirmed rendering defect**. | Consider a named selector and verify both missing and broken detail artwork by actual screenshot before making visual changes. |
| UX-08 | **P1** | `HashRouter` is used (`src/main.tsx:1-13`). A user opening `/movies` directly without a hash may land on Home; the app's own `Link` components create hash routes. | Publish/share hash-correct links, or adopt one clear router model with a tested history fallback. Smoke-test direct entry and refresh for every destination. |
| UX-09 | **P1** | `/api/movies` prepares 8 concurrent DB statements including large faceted aggregates every page/query (`worker/index.ts:443-560`), `/api/series` prepares 7 (`340-440`). Heavy D1 read use previously exhausted free allowance. | Separate/cached facets from paged rows, measure D1 rows read on test workload, avoid repeated full-catalogue metrics on every search and page. **No speculative production migration.** |
| UX-10 | **P2** | Movie and Series titles/metadata can be ellipsized; the mobile CSS sets item copy to ~10/8px; no expanded title outside detail modal (`app-v2.css`). | Prioritize title readability, 2-line titles or clear truncation, and accessible full names. Verify 320/390/768/1440 px and 200% text zoom. |
| UX-11 | **P2** | Search is debounced (good) but movie result order remains year-first even with `q` (`worker/index.ts:489-502`); no relevance tiers or clear result feedback. | Consider exact-title/prefix before year recency after measuring; keep deterministic ID tiebreaker; show query/filtered result count. |
| UX-12 | **P2** | `countryLabel` maps absent country data to `Global` (`App.tsx:71`), which can misleadingly imply global distribution rather than unknown origin. | Use `Country unknown` when metadata missing; `Global` only when sourced as global. |
| UX-13 | **P2 / scope** | Today, OTT and Radar are absent from current V1 routes. Previous requests mention them, but the V1 product lock explicitly defers OTT availability. | Decide whether these belong in a **later phase** or a different code path; do not invent new tabs in this UI pass. |
| UX-14 | **P2** | No accepted evidence of an actual mobile/tablet browser run, keyboard-only audit, screenreader pass, poster render check or loading-state screenshots from this audit. | Run screenshot/interaction QA when a browser capture tool and stable live data/fixture are available. Keep it a required final gate, not an assumed pass. |

## Strong foundations to retain

- The movie/series browse pages use bounded 60-title pagination with query-key isolation, request aborts and source-specific error/retry state (`App.tsx:163-250,401-462`).
- Debounced movie/series searches reduce wasted remote requests (`App.tsx:99-107`).
- Successful images use a reusable error-triggered initial fallback in cards (`App.tsx:290-323`); fix its detail hero styling rather than replacing it.
- Year-precision releases are explicitly labeled unconfirmed with correct Wikidata/Wikipedia provenance; do not remove accuracy messaging (`App.tsx:329-347`).
- Responsive breakpoints at 1180, 920, 700 and 430px and reduced-motion support exist in `app-v2.css`.
- D1 quota failures are explicitly represented on Movies/Series, and edge-cache fallback is present in the worker. Keep those safeguards.

## Proposed implementation order (separate, testable PRs)

1. **PR-A, P0 reliability and truthful completion**: shared catalogue request status for Home/Upcoming, proper counts loading/error, error/empty UX, Upcoming pagination with independent page state. Regression tests simulate API 503, empty results, 80+ upcoming and filter change.
2. **PR-B, P1 keyboard and readable controls**: modal dialog focus/labels/restore, search/select accessible names, filter expanded states, mobile 44px targets and >=12px functional labels. Keyboard and accessibility checks.
3. **PR-C, P1 visual and detail polish**: details fallback CSS, consistent film/series card title wrapping and hierarchy, reliable mobile/tablet spacing, artwork-failure screens, simplify long technical copy while preserving provenance.
4. **PR-D, performance and quota**: instrument rows-read and isolate/cached facets and statistics; compare benchmark before/after using nonproduction or post-reset guarded probes, without extra production write load.
5. **Gate: actual visual + E2E acceptance**: required screenshots/interaction evidence on desktop 1440, tablet 768, mobile 390/320, keyboard navigation, 200% zoom, success/error/empty states. Check directly opened `/#/movies`, `/#/series`, `/#/upcoming`. Only then call the UX audit visually complete.

## Definition of done

- All four active routes work with full/empty/error/quota-paused mocked responses; Home and Upcoming explain failures instead of rendering silent blanks.
- Upcoming reaches every result across bounded pages; filter changes do not leak old result sets.
- All dialogs can be opened and closed via keyboard; they have discernible labels, trap focus, and restore focus on close.
- Search, filters and upcoming segmentation are properly labeled and expose their state to assistive tech.
- Functional text and touch targets are legible on a 390px device and at 200% zoom; labels do not depend on placeholder text.
- Count metadata never represents a network failure as an actual zero.
- Known hash deep links open their intended route on refresh; external share links use an explicitly supported URL format.
- Movie source attribution, release verification, and quota safeguards remain intact.
- Final visual inspection is evidenced by real screenshots, not inferred from CSS alone.

## Evidence and limits

Source-level findings are **confirmed from code presence/absence**. Severity is an engineering prioritization, not a measured user-impact estimate. The separate Cloudflare Worker runtime incident has its own evidence in GitHub Actions (D1 daily row-read quota exceeded on 2026-10-18); this audit did **not** re-query D1 or conclude production recovered. No page screenshots could be captured in the current chat, so visual appearance, physical tap geometry, color-contrast ratios, screenreader output and browser behavior are **not yet verified**. Do not describe this document as a completed screenshot-based audit.
