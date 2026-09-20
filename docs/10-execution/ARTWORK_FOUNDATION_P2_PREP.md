# Artwork Foundation P2 — Pre-Implementation Contract

**Status:** WORKING — PREP ONLY; DO NOT ACTIVATE BEFORE P1 EXIT  
**Date:** 2026-09-20  
**Parent roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`  
**Rights baseline:** `docs/02-sources/ARTWORK_PUBLICATION_BASELINE_V1.md`  
**Rights research:** `docs/02-sources/ARTWORK_MEDIA_RIGHTS_STRATEGY.md`

## Purpose

P2 will replace the current movie-only artwork convenience fields with a shared, rights-aware artwork foundation for Movies and Series while preserving the existing API/UI during migration.

This document is architecture preparation only. It authorizes **no migration, D1 mutation, source ingestion, public artwork publication, or P2 production workflow while P1 remains active**.

P1 currently owns migrations `0021` and `0022`; no P2 migration number is reserved here. Migration numbering must be reconciled only after P1 closes and any dormant branches are rebased.

---

# 1. Existing state and gap

## 1.1 Movie-only legacy storage

Migration `0015_movie_artwork.sql` added directly to `movies`:

- `poster_url`
- `backdrop_url`
- `artwork_source`
- `artwork_source_url`
- `artwork_updated_at`

The Worker projects those fields into movie catalogue API rows as `posterUrl`, `backdropUrl`, `artworkSource`, and `artworkSourceUrl`.

This model is useful as a compatibility projection but is not sufficient as the canonical P2 asset model because it:

- is movie-only;
- cannot represent multiple assets per title cleanly;
- cannot represent locale/territory variants;
- cannot preserve complete rights/licence/attribution state;
- cannot represent expiry/takedown independently of the title;
- treats source provenance too coarsely;
- cannot safely distinguish discovery from publication eligibility;
- cannot share one rights-reviewed asset across multiple catalogue projections of the same title.

## 1.2 Series currently has no artwork model

`series_titles` has no poster/backdrop/artwork fields. P2 must not solve this by merely duplicating the five legacy movie columns into `series_titles`.

## 1.3 Legacy artwork refresh is not the P2 rights model

`scripts/artwork_refresh.py` currently discovers:

1. first-party release-page/OpenGraph or official YouTube thumbnail candidates;
2. Wikidata `P18` -> Wikimedia Commons image candidates.

It then emits direct `UPDATE movies` SQL.

That discovery logic may be reusable, but **direct publication is not**. The locked artwork publication baseline requires a publishable rights basis, and Wikimedia candidates require per-file licence/creator/attribution verification. An official webpage, studio page, YouTube thumbnail, or publicly reachable image URL is not automatically a licence for permanent product display.

Therefore P2 separates:

`candidate discovery -> rights verification -> asset record -> title link -> presentation selection`

No candidate becomes publicly renderable merely because discovery succeeded.

---

# 2. Locked P2 principles

1. **Metadata rights != artwork rights.**
2. **A title is valid with zero publishable artwork.**
3. **Movie and Series use one shared artwork domain model.**
4. **Artwork asset identity is separate from title identity.**
5. **A source URL is provenance, not permission.**
6. **Only explicitly publishable rights states may reach public APIs.**
7. **Primary poster/backdrop is a derived presentation selection, not permanent canonical truth.**
8. **Locale, language, territory, asset role, rights basis and hosting mode are first-class.**
9. **Takedown/unpublication must never delete the title itself.**
10. **Legacy movie artwork fields remain compatibility-only until consumers migrate.**
11. **No guessed title-based image URLs.**
12. **No fake AI poster may be presented as official artwork for a real title.**
13. **P2 may improve visual coverage without weakening the publication baseline.**

---

# 3. Source priority: discovery priority vs publication eligibility

The active roadmap's artwork priority remains useful, but it must be interpreted as **selection/discovery precedence among rights-eligible assets**, not as an automatic rights grant.

## Tier A — first-party/rightsholder/provider artwork

Examples:

- studio/distributor/streamer supplied asset;
- explicit press-kit asset with compatible terms;
- licensed commercial provider asset;
- directly granted rightsholder permission.

Publication requires one of the locked approved rights bases/states. Merely extracting `og:image` from an official page is candidate discovery only.

## Tier B — official YouTube

Official YouTube is primarily a trailer/video reference and embed source.

- official video/channel identity may be stored;
- official player/embed may be used where permitted;
- a thumbnail URL is not automatically permanent poster/backdrop publication permission;
- a thumbnail may become publishable only if the applicable platform/rightsholder terms establish a compatible rights basis.

## Tier C — Wikidata P18 -> Wikimedia Commons

`P18` identifies a candidate file; it does not approve publication by itself.

Before public rendering, record and validate at least:

- Commons file/source page identity;
- creator where available;
- licence name/version or public-domain basis;
- attribution text/requirements;
- commercial-use compatibility;
- derivative/modification conditions;
- ShareAlike conditions where relevant;
- verification timestamp.

## Tier D — Cinema & Series fallback

If no rights-approved asset exists, render a premium CAS placeholder. This is a complete supported state, not an error state.

---

# 4. Proposed canonical data model

The exact SQL is deferred until P1 closes. The conceptual model is locked for implementation review.

## 4.1 `artwork_assets`

One row represents one independently rights-governed media asset.

Minimum fields:

- `id` — CAS stable asset ID;
- `asset_type` — `poster`, `backdrop`, `teaser_poster`, `logo`, `still`, or future approved type;
- `source_key` — adapter/source identity;
- `source_asset_id` — provider/file ID where available;
- `source_page_url` — canonical evidence/file/details page;
- `delivery_url` — URL used only when hosting policy allows it;
- `hosting_mode` — `SELF_HOSTED`, `PROVIDER_CDN`, `EXTERNAL_ALLOWED`, `REFERENCE_ONLY`, `EMBED_ONLY` as applicable;
- `original_creator`;
- `rightsholder`;
- `licence_id` / licence text reference;
- `rights_basis`;
- `publication_state`;
- `commercial_use_allowed`;
- `modification_allowed`;
- `attribution_required`;
- `attribution_text`;
- `share_alike_required`;
- `territory_restrictions`;
- `valid_from`;
- `valid_until`;
- `width`;
- `height`;
- `mime_type`;
- `checksum` when legally stored/downloaded;
- `source_retrieved_at`;
- `rights_verified_at`;
- `rights_verified_by`;
- `takedown_status`;
- `created_at`;
- `updated_at`.

### Canonical rule

No row is public merely because `delivery_url` exists. Public eligibility is derived from `publication_state + rights_basis + hosting_mode + territory/expiry rules`.

## 4.2 `title_artwork_links`

A separate link table associates an asset with a concrete catalogue title identity.

Minimum fields:

- `media_type` — `movie` / `series`;
- `source_table` — initially `movies`, `catalogue_titles`, `series_titles`;
- `source_id` — exact source-row ID;
- optional `wikidata_qid` as a reconciliation aid, never as the sole link when ambiguous;
- `asset_id` -> `artwork_assets.id`;
- `presentation_role` — `poster`, `backdrop`, `logo`, etc.;
- `language`;
- `territory`;
- optional `version_key` for future cuts/releases;
- `selection_priority` — deterministic presentation preference, not a claim of rights;
- `linked_at`;
- `link_source` / evidence reference.

The link must preserve the exact catalogue identity used for the association. Do not merge two works only because titles match.

## 4.3 Why not use `recommendation_titles` as the artwork parent

`recommendation_titles` is a recommendation projection, not the universal catalogue identity layer. Artwork must also work for titles outside the recommendation-eligible set and future catalogue growth. P2 therefore must not make asset existence depend on P1 recommendation membership.

---

# 5. Public eligibility vocabulary

P2 must align names with the locked publication baseline before SQL is frozen.

Publicly renderable states currently include:

- `OPEN_LICENSE_VERIFIED`
- `PUBLIC_DOMAIN_VERIFIED`
- `PROVIDER_LICENSED`
- `RIGHTS_APPROVED`
- `PROMOTIONAL_PERMISSION_VERIFIED` when the recorded permission is compatible with intended use

Non-public states include at minimum:

- `DISCOVERED` / `PENDING_REVIEW`
- `REJECTED`
- `EXPIRED`
- `TAKEDOWN_PENDING`
- `TAKEN_DOWN`
- `UNKNOWN` / `NO_RIGHTS_BASIS`

Before implementation, normalize vocabulary differences between the research document and locked publication baseline into one enum/check contract. No ingestion adapter may invent its own publication vocabulary.

---

# 6. Primary artwork selection

The API derives the best eligible poster/backdrop for a request context.

Conceptual flow:

`linked assets -> rights-eligible filter -> territory/expiry filter -> role filter -> locale preference -> source/officiality preference -> quality preference -> deterministic tie-break`

Selection inputs may include:

- `media_type` / exact title identity;
- required role (`poster`/`backdrop`);
- requested language/locale;
- user/product territory;
- publication eligibility;
- hosting mode;
- official/rightsholder/provider preference where rights-approved;
- resolution/aspect suitability;
- deterministic fallback ordering.

A lower-resolution authorized asset beats a beautiful unauthorized asset.

No database column named `primary_poster_id` is required for V1 unless profiling later proves that a derived query/cache is insufficient.

---

# 7. Backward-compatible API migration

P2 must not break existing Movie UI while the new asset model rolls out.

## Stage A — canonical model introduced, existing API unchanged

- populate rights-safe canonical asset/link records only after P2 authorization;
- existing `movies.poster_url/backdrop_url/...` continue to serve legacy consumers temporarily;
- Series continues to use fallback until shared API projection is ready.

## Stage B — shared artwork projection

Movie and Series responses gain a consistent object, conceptually:

```json
{
  "artwork": {
    "posterUrl": "...",
    "backdropUrl": "...",
    "posterAttribution": "...",
    "backdropAttribution": "...",
    "hasPublishablePoster": true,
    "hasPublishableBackdrop": true,
    "isFallback": false
  }
}
```

Do not expose internal rights-review notes or private evidence in the public payload.

For a transition period, top-level movie `posterUrl` / `backdropUrl` may remain as aliases derived from the same shared selector.

## Stage C — consumers migrate

- Home/Movie/Series/Discover cards use shared artwork payload;
- Series receives the same visual capability as Movies;
- placeholders are generated/rendered consistently;
- legacy direct movie columns stop being authoritative.

## Stage D — legacy retirement

Only after every consumer and writer has migrated:

- stop legacy artwork writes;
- decide whether old movie columns remain as denormalized compatibility cache or are removed in a later migration;
- document any removal separately with rollback/consumer evidence.

P2 does not require destructive legacy-column removal to be considered successful.

---

# 8. Adapter architecture

Each source adapter has two distinct outputs:

## 8.1 Discovery record

May contain:

- source asset/file/video ID;
- source page URL;
- candidate delivery URL;
- dimensions/type clues;
- linked title evidence;
- retrieval timestamp.

A discovery record is **not publishable**.

## 8.2 Rights assessment

Deterministically captures where possible:

- rights basis;
- licence/version;
- attribution;
- hosting/display rules;
- territory/expiry;
- transformation permissions;
- review state.

If deterministic assessment is incomplete, the asset remains non-public pending review.

### Initial adapter behavior

- **Wikimedia Commons:** extend retrieval to licence/extmetadata/creator/attribution details and fail closed when required rights data is unavailable.
- **Wikidata P18:** discovery/reconciliation only; actual rights decision belongs to the resolved Commons file.
- **official pages:** discovery/evidence only unless explicit compatible permission is recorded.
- **YouTube:** video/embed reference first; thumbnail publication is separately rights-gated.
- **licensed providers/rightsholder submissions:** adapter contract must encode permitted display/cache/transform scope.

---

# 9. Placeholder system

P2 must guarantee 100% visual renderability independent of rights-safe real-art coverage.

Fallback inputs may use only canonical metadata such as:

- title;
- year / release status;
- Movie vs Series;
- language;
- deterministic CAS design tokens;
- rights-safe abstract texture/pattern where used.

Fallback must not:

- imitate a known poster composition;
- invent actor likenesses;
- imply studio/rightsholder endorsement;
- appear to be an official poster.

Fallback behavior must work in poster and backdrop aspect contexts and support reduced-motion UI.

---

# 10. Coverage audit before production enrichment

P2 follows the same prove-before-write discipline as P1.

Run a read-only audit over Movies + Series before broad production ingestion.

Required metrics:

- total distinct Movie identities considered;
- total distinct Series identities considered;
- titles with at least one discovered candidate;
- titles with at least one rights-approved poster;
- titles with at least one rights-approved backdrop;
- coverage by media type;
- coverage by major India languages/industries;
- coverage by source/right basis;
- assets requiring attribution;
- assets with expiry/territory restrictions;
- duplicate candidate rate;
- ambiguous title-link rate;
- rejected/no-rights-basis rate;
- fallback rate;
- provider concentration.

Artwork coverage must remain separate from catalogue metadata completeness.

---

# 11. Quality and safety gates

P2 production mutation is authorized only when all applicable gates pass:

1. P1 is formally COMPLETE.
2. P2 migration numbering is conflict-free.
3. shared Movie+Series schema is reviewed.
4. public-eligibility enum is normalized to the locked publication baseline.
5. no adapter can publish a `DISCOVERED`/unknown-rights candidate.
6. Wikimedia path records sufficient licence/attribution data.
7. exact-title linkage avoids title-text guessing.
8. API returns no non-public asset.
9. expiry/takedown immediately removes asset from public selection.
10. placeholder path works with zero assets.
11. read-only coverage audit is reviewed.
12. bounded/resumable mutation plan exists.
13. Catalogue Quality S0/S1 remains clean after mutations.

---

# 12. P2 test contract

Minimum automated coverage should include:

- source discovery cannot imply publication approval;
- non-public states never pass selector;
- expired/taken-down asset never passes selector;
- territory mismatch never passes selector;
- locale preference does not override rights eligibility;
- rightsholder/provider/open asset priority is deterministic among eligible candidates;
- Commons record without required licence metadata remains non-public;
- attribution-required asset exposes required public attribution field;
- exact Movie and Series identity links work;
- same-title different-work identities never merge by title string;
- legacy Movie aliases equal shared-selector result during compatibility stage;
- Series receives shared artwork payload;
- no eligible asset produces premium fallback, not a broken URL;
- public API never returns internal review notes/private evidence;
- takedown state propagates immediately to presentation selection.

---

# 13. What may be reused from current implementation

Potentially reusable after refactoring:

- HTTPS URL validation;
- YouTube ID parsing for official video references;
- official-page OpenGraph discovery as a candidate-discovery mechanism;
- Wikidata `P18` candidate lookup;
- Commons file resolution;
- image dimension/aspect hints;
- deterministic no-title-URL-guessing rule.

Must not be carried forward as-is:

- direct `UPDATE movies` as canonical ingestion;
- treating official-page/YouTube discovery as publication permission;
- treating a Commons image URL without per-file rights metadata as publishable;
- storing only one coarse `artwork_source` string as sufficient provenance;
- Movie-only asset semantics.

---

# 14. P2 implementation slices after P1 exit

## P2.1 — schema + selector contract

- freeze canonical tables/check constraints;
- freeze public eligibility vocabulary;
- implement pure selector tests;
- no broad enrichment yet.

## P2.2 — compatibility API

- shared selector/projection for Movies + Series;
- preserve movie top-level artwork aliases temporarily;
- introduce premium fallback object.

## P2.3 — Wikimedia rights-aware adapter

- `P18` discovery;
- Commons extmetadata/licence/creator/attribution verification;
- bounded read-only coverage audit;
- review yield before writes.

## P2.4 — first-party/provider adapter boundary

- official-page/YouTube discovery remains candidate-only by default;
- add explicit rightsholder/provider permission paths;
- encode provider contract behavior rather than assuming it.

## P2.5 — bounded production population

- reviewed candidates only;
- resumable writes;
- post-write rights/identity/quality audit;
- zero unauthorized public path.

## P2.6 — consumer migration

- Movies, Series, Home, Discover cards/hero use shared artwork object;
- legacy movie projection retained only as compatibility cache/alias if still needed.

---

# 15. P2 exit definition

P2 is complete when:

- Movie + Series share one rights-aware artwork foundation;
- public APIs can derive poster/backdrop consistently for both media types;
- no unauthorized/discovered-only candidate can leak into public selection;
- Wikimedia/open assets preserve required licence/attribution evidence;
- licensed/rightsholder assets have explicit rights basis;
- missing artwork always renders a premium CAS fallback;
- legacy movie-only artwork storage is no longer canonical;
- coverage and fallback rates are measurable;
- takedown/expiry behavior is testable and enforced;
- post-mutation Catalogue Quality remains clean.

---

# Immediate consequence while P1 is active

Until P1 formally exits:

- **do not add a P2 migration**;
- **do not populate canonical artwork tables**;
- **do not expand legacy artwork publication based on this document**;
- **do not begin P2 consumer migration**;
- read-only research, tests, schema design review and adapter-contract design are allowed.

The active production priority remains completing the corrected P1 recommendation graph safely, one quota-bound operation at a time.
