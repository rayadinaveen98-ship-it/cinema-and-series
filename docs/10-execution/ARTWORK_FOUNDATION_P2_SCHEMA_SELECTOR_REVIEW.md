# Artwork Foundation P2 — Schema & Selector Review

**Status:** LOCKED FOR P2.1 IMPLEMENTATION AFTER P1 EXIT  
**Date:** 2026-09-24  
**Parent contract:** `docs/10-execution/ARTWORK_FOUNDATION_P2_PREP.md`  
**Rights baseline:** `docs/02-sources/ARTWORK_PUBLICATION_BASELINE_V1.md`  
**Activation gate:** P1 must be formally COMPLETE before any P2 migration, D1 mutation, canonical artwork population, public artwork publication, or consumer migration.

## Purpose

Resolve the remaining pre-implementation ambiguities in P2 without activating P2 production work.

This document freezes:

1. canonical rights/publication vocabulary;
2. public eligibility rules;
3. deterministic artwork selection precedence;
4. schema-level invariants to implement after P1 exit;
5. adapter input/output boundaries;
6. P2.1 acceptance tests.

It creates no migration number and authorizes no production write.

---

# 1. Canonical vocabulary

The locked publication baseline remains authoritative. P2 must use one shared vocabulary rather than allowing each adapter to invent terms.

## 1.1 `publication_state`

Canonical values:

- `DISCOVERED`
- `PENDING_REVIEW`
- `OPEN_LICENSE_VERIFIED`
- `PUBLIC_DOMAIN_VERIFIED`
- `PROVIDER_LICENSED`
- `RIGHTS_APPROVED`
- `PROMOTIONAL_PERMISSION_VERIFIED`
- `REJECTED`
- `EXPIRED`
- `TAKEDOWN_PENDING`
- `TAKEN_DOWN`

Normalization rules:

- research term `RIGHTS_RESEARCH_PENDING` -> `PENDING_REVIEW`;
- research rightsholder approval -> `RIGHTS_APPROVED` after permission evidence is verified;
- research promotional-use approval -> `PROMOTIONAL_PERMISSION_VERIFIED` after the intended product use is verified;
- `UNKNOWN` / `NO_RIGHTS_BASIS` is represented as non-public discovery/review state plus a `rights_basis` of `NO_RIGHTS_BASIS`; it is never a publishable state.

Only these image-publication states are publicly renderable:

- `OPEN_LICENSE_VERIFIED`
- `PUBLIC_DOMAIN_VERIFIED`
- `PROVIDER_LICENSED`
- `RIGHTS_APPROVED`
- `PROMOTIONAL_PERMISSION_VERIFIED`

`DISCOVERED`, `PENDING_REVIEW`, `REJECTED`, `EXPIRED`, `TAKEDOWN_PENDING`, and `TAKEN_DOWN` are always non-public.

## 1.2 `rights_basis`

Canonical mechanism values:

- `OPEN_LICENSE`
- `PUBLIC_DOMAIN`
- `PROVIDER_CONTRACT`
- `RIGHTSHOLDER_PERMISSION`
- `PROMOTIONAL_PERMISSION`
- `PLATFORM_EMBED_AUTHORIZATION`
- `NO_RIGHTS_BASIS`

`rights_basis` explains why an asset may or may not be used. It does not by itself make the asset public.

Required public-state/basis pairings:

| `publication_state` | Required `rights_basis` |
|---|---|
| `OPEN_LICENSE_VERIFIED` | `OPEN_LICENSE` |
| `PUBLIC_DOMAIN_VERIFIED` | `PUBLIC_DOMAIN` |
| `PROVIDER_LICENSED` | `PROVIDER_CONTRACT` |
| `RIGHTS_APPROVED` | `RIGHTSHOLDER_PERMISSION` |
| `PROMOTIONAL_PERMISSION_VERIFIED` | `PROMOTIONAL_PERMISSION` |

Any other pairing fails closed.

## 1.3 `hosting_mode`

Canonical values:

- `SELF_HOSTED`
- `PROVIDER_CDN`
- `EXTERNAL_ALLOWED`
- `REFERENCE_ONLY`
- `EMBED_ONLY`

For poster/backdrop/logo/still image selection, only `SELF_HOSTED`, `PROVIDER_CDN`, or `EXTERNAL_ALLOWED` may return a renderable image URL.

`REFERENCE_ONLY` is never publicly rendered.

`EMBED_ONLY` belongs to platform media such as authorized trailer embeds. It must not be treated as poster/backdrop publication permission.

---

# 2. Central public eligibility rule

Adapters never provide a trusted `is_publishable=true` flag. Public eligibility is computed centrally.

An image asset is eligible only when every rule below passes:

1. `publication_state` is in the five-state public allowlist;
2. `publication_state` and `rights_basis` are a valid pairing;
3. `takedown_status` is clear and the publication state is not a takedown state;
4. `valid_from` is null or not in the future;
5. `valid_until` is null or strictly later than the request time;
6. explicit territory restrictions permit the request territory;
7. hosting mode is one of the three image-renderable modes;
8. a valid HTTPS delivery URL exists for externally delivered images, or the approved self-hosted asset resolves to a valid CAS delivery URL;
9. required attribution data is present when `attribution_required=true`;
10. the exact linked catalogue identity is valid for the requested Movie or Series.

Unknown or malformed rights/territory/expiry/hosting data fails closed rather than being guessed.

A title with zero eligible assets is valid and returns the CAS fallback.

---

# 3. Deterministic selector precedence

Selection must never trade rights safety for visual quality.

For a requested title identity and presentation role:

`exact title links -> public eligibility -> role -> territory -> locale -> rights/source preference -> visual suitability -> stable tie-break`

## 3.1 Hard filters

These are filters, never scores:

1. exact title identity;
2. public eligibility;
3. requested presentation role;
4. territory validity;
5. expiry/takedown validity.

A candidate failing a hard filter is removed entirely.

## 3.2 Locale rank

Among remaining assets, prefer in order:

1. exact requested language + exact territory;
2. exact requested language + territory-neutral;
3. language-neutral + exact territory;
4. language-neutral + territory-neutral;
5. another eligible locale only when product policy explicitly allows cross-locale fallback.

Locale never overrides public eligibility.

## 3.3 Rights/source preference

Among equally valid locale candidates, prefer:

1. rights-approved current official/provider/rightsholder artwork;
2. rights-approved promotional artwork;
3. verified open-licence artwork;
4. verified public-domain artwork.

Official-page, social, YouTube-thumbnail, Wikidata or Commons discovery status alone adds no publication preference. The candidate must first be rights-eligible.

## 3.4 Visual suitability

Only after rights/source preference may the selector consider:

- required aspect suitability;
- width/height/resolution;
- asset type suitability for the requested role;
- deterministic quality score whose inputs are documented and non-rights-related.

A lower-resolution eligible asset always beats an ineligible higher-resolution asset.

## 3.5 Stable tie-break

Final ties use a stable deterministic key, ending with CAS `asset_id` ascending. Selection must not depend on database row order.

---

# 4. Schema invariants for future P2 migration

No SQL is created by this review. The future P2 migration must encode the following constraints where practical and enforce the remainder in the service layer with tests.

## 4.1 `artwork_assets`

Required invariants:

- stable CAS `id` primary key;
- `asset_type`, `publication_state`, `rights_basis`, and `hosting_mode` use closed vocabularies;
- `source_key` required;
- `source_page_url` required for external/provider/open-media evidence paths unless a documented provider contract supplies an immutable source identifier instead;
- `delivery_url` may be null for non-public/reference-only assets;
- public image states require a compatible `rights_basis`;
- public image states require a renderable hosting mode;
- `attribution_required=true` requires non-empty `attribution_text`;
- `valid_until`, when present, must be later than `valid_from` when both exist;
- width/height, when present, must be positive;
- checksum is stored only when the binary may legally be stored/processed;
- `rights_verified_at` is required for all five public image states;
- `rights_verified_by` is required for manually/provider-approved public states where the source contract does not provide deterministic automated verification identity;
- takedown state always overrides any otherwise-public state at selection time.

Do not make checksum globally unique. The same binary may legitimately have distinct source/rights records.

When `source_asset_id` is available, `(source_key, source_asset_id)` should be unique for the same source version unless the provider contract explicitly requires versioned identities.

## 4.2 `title_artwork_links`

Required invariants:

- exact `media_type` is `movie` or `series`;
- exact source table + source ID are preserved;
- `asset_id` references `artwork_assets`;
- `presentation_role` uses a closed vocabulary;
- title-text-only matching is forbidden;
- a Wikidata QID is reconciliation evidence, not sufficient identity when ambiguity exists;
- the same link cannot be duplicated by ingest retries;
- locale and territory are nullable only to represent neutral scope, not unknown guessed values;
- deleting/unpublishing artwork never deletes the title.

The final unique key must include the exact title identity, asset, role, locale/territory neutrality and version key so retries are idempotent.

---

# 5. Adapter contracts

## 5.1 Discovery adapter output

A discovery adapter may emit only evidence/candidate facts, for example:

- `source_key`;
- `source_asset_id`;
- `source_page_url`;
- candidate delivery URL;
- observed asset type/dimensions;
- exact title-link evidence;
- retrieval timestamp;
- raw source metadata reference.

A discovery adapter must not assign a public `publication_state` unless it is also the approved deterministic rights adapter for that source contract.

## 5.2 Rights adapter output

A rights adapter may emit:

- canonical `rights_basis`;
- canonical candidate `publication_state`;
- licence/version or permission reference;
- creator/rightsholder;
- attribution requirements;
- commercial-use flag;
- transformation flag;
- ShareAlike obligations;
- hosting mode;
- territory/expiry scope;
- verification timestamp and verifier/source-contract identity.

Central validation still decides whether the output forms a valid public-state/basis/hosting combination.

## 5.3 Wikimedia contract

`Wikidata P18` is discovery/reconciliation only.

The resolved Commons file must provide enough per-file metadata to determine:

- canonical file/source page;
- creator when required;
- licence + version or public-domain basis;
- attribution requirement/text;
- commercial-use compatibility;
- transformation/ShareAlike obligations where applicable;
- verification timestamp.

Missing required rights metadata leaves the asset non-public.

## 5.4 Official page / YouTube contract

- OpenGraph images and thumbnails are candidate discovery only by default;
- public visibility does not imply reuse permission;
- YouTube trailer/video references may use authorized embed mechanisms under the platform contract;
- `EMBED_ONLY` video authorization never converts the thumbnail into publishable poster/backdrop art;
- an image becomes public only through a separately valid rights basis.

## 5.5 Provider/rightsholder contract

Provider configuration must explicitly describe:

- allowed display surfaces;
- web/mobile scope;
- allowed hosting or required CDN hotlinking;
- cache duration;
- resize/crop/format-transform permission;
- attribution/branding obligations;
- territory restrictions;
- expiry/termination/delete obligations.

Unknown scope fails closed.

---

# 6. Public API projection contract

The shared public projection for Movie and Series must be derived only from the central selector.

Minimum conceptual shape:

```json
{
  "artwork": {
    "posterUrl": null,
    "backdropUrl": null,
    "posterAttribution": null,
    "backdropAttribution": null,
    "hasPublishablePoster": false,
    "hasPublishableBackdrop": false,
    "isFallback": true
  }
}
```

Rules:

- public clients never receive internal review notes, private evidence, provider secrets or rejected candidate URLs;
- attribution is emitted when required by the selected asset;
- no eligible poster/backdrop yields the premium CAS fallback rather than a broken URL;
- legacy Movie `posterUrl` / `backdropUrl` aliases, while retained, must be derived from exactly the same selector result;
- Series uses the same selection contract as Movies.

---

# 7. P2.1 acceptance matrix

P2.1 may be considered implementation-ready only when automated tests prove at least:

1. `DISCOVERED` cannot render;
2. `PENDING_REVIEW` cannot render;
3. each of the five public states renders only with its matching rights basis;
4. mismatched state/basis fails closed;
5. `TAKEDOWN_PENDING` and `TAKEN_DOWN` cannot render;
6. expired asset cannot render;
7. future-not-yet-valid asset cannot render;
8. territory mismatch cannot render;
9. `REFERENCE_ONLY` and `EMBED_ONLY` cannot render as poster/backdrop;
10. missing required attribution cannot render;
11. locale preference cannot override rights eligibility;
12. official/provider preference cannot override rights eligibility;
13. exact-title identity beats any title-string similarity;
14. same title text for two different works never cross-links;
15. selector tie-break is stable across input order;
16. no eligible asset returns fallback state;
17. Movie legacy aliases equal the shared selector result;
18. Series gets the same shared artwork shape;
19. public projection omits internal/private evidence;
20. Wikidata P18 without resolved Commons rights metadata remains non-public.

---

# 8. Activation checklist after P1 exit

Before writing the first P2 migration:

1. P1 status is formally COMPLETE and final exact graph/quality evidence is merged;
2. inspect live migration directory and choose the next conflict-free migration number;
3. re-read this review against the then-current locked rights baseline;
4. convert the schema invariants into migration/check constraints;
5. implement the central selector as a pure, fully tested function;
6. implement the public eligibility validator separately from source adapters;
7. run the read-only Movie+Series artwork coverage audit;
8. review audit yield and ambiguous-link rate;
9. create a bounded/resumable production population plan;
10. only then authorize P2 production mutation.

Until those conditions hold, this document remains a preparation artifact only.
