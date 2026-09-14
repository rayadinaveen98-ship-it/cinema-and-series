# Artwork Publication Baseline — Cinema and Series V1

**Status: LOCKED**  
**Date: 2026-09-14**

## Principle

A Cinema and Series record never depends on having a poster.

Metadata identity and artwork publication are separate rights decisions.

# Publicly renderable artwork states

V1 may publish an asset only when it has one of:
- `OPEN_LICENSE_VERIFIED`;
- `PUBLIC_DOMAIN_VERIFIED`;
- `PROVIDER_LICENSED`;
- `RIGHTS_APPROVED`;
- `PROMOTIONAL_PERMISSION_VERIFIED` where the permission/use basis is explicit enough for the intended product use.

Assets in `PENDING_REVIEW`, `REJECTED` or `TAKEDOWN` are never publicly rendered.

# Initial source paths

## 1. Wikimedia Commons / open media
Allowed only per-file after the Asset Engine records:
- source page/file ID;
- creator;
- licence/version;
- attribution;
- public-domain rationale where applicable;
- ShareAlike/derivative obligations where applicable;
- verification timestamp.

`Exists on Commons` is not itself approval.

## 2. Explicitly licensed provider assets
May be added when a provider agreement grants the required downstream display/use rights.

## 3. Rights-holder supplied or explicitly approved promotional assets
Allowed only when the permission/press-use basis is recorded and compatible with our intended display.

## 4. Historical public-domain assets
Allowed after public-domain status is verified for the relevant jurisdiction/use case and documented.

# Not allowed as shortcuts

V1 must not publish an image merely because it appears on:
- Google Images;
- IMDb;
- TMDB test API;
- Moviebuff;
- BookMyShow;
- OTTplay;
- Wikipedia article pages;
- a studio's social post;
- a random press article.

Those may be discovery/reference locations, not automatic licences.

# No-artwork product behavior

If no publishable artwork exists, the consumer UI renders a premium CAS placeholder using:
- title;
- year/status;
- language/type;
- subtle typographic/cinematic treatment;
- optional rights-safe generated abstract texture that does not imitate/copy protected poster art.

The title remains searchable, browsable and complete as a metadata entity.

# Asset storage model

Every stored asset record carries:
- `asset_id`;
- linked entity;
- source;
- original source URL/identifier;
- creator/rightsholder where known;
- licence/permission basis;
- attribution text;
- territory/use constraints where known;
- retrieval/verification timestamps;
- checksum/content identity;
- publication state;
- takedown history;
- derivative/transformation history if any.

# Takedown behavior

A rights complaint or policy change can:
- immediately unpublish the asset;
- preserve the metadata title/person entity;
- preserve audit/history where legally permitted;
- replace the asset with the CAS placeholder;
- avoid broken entity pages.

# V1 asset completeness

Artwork completeness is measured separately from core metadata completeness.

A title with excellent identity/credits/release provenance and no publishable poster is a valid high-quality database record.

# Freeze consequence

No paid or unlicensed poster provider is required for V1 implementation. The Asset Engine ships with:
1. open/public-domain verification path;
2. provider/licensed permission path;
3. rights-holder/manual approval path;
4. high-quality placeholder fallback.
