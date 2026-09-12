# Artwork & Media Rights Strategy — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series must never confuse metadata access with permission to publish posters, stills, portraits, logos, trailers, or other media.

A title record is valid without artwork. Artwork is a separately governed asset domain with its own provenance, licence, publication state, and takedown lifecycle.

## Non-negotiable principles

1. **Metadata rights != media rights.**
2. **Publicly visible != reusable.** Finding an image on Google, IMDb, Moviebuff, BookMyShow, a studio social account, or a press article does not grant Cinema and Series permission to host it.
3. **Every published asset must have an explicit rights basis.**
4. **The catalogue must work with zero copyrighted artwork.** A rights-safe placeholder is always preferable to unauthorized media.
5. **Provider contracts are asset-specific.** A licensed metadata provider's agreement must explicitly cover image display/caching before we use its assets.
6. **Asset rights can expire or be revoked without deleting the underlying title/person record.**
7. **No AI-generated fake poster may be presented as official artwork for a real movie/series.**
8. **Trailers should normally be linked/embedded through authorized platform mechanisms, not copied/downloaded.**
9. **Takedown is a first-class workflow.**
10. **Territory, version, language and artwork type are first-class asset metadata.**

## Asset classes

- poster / one-sheet;
- localized poster;
- teaser poster;
- backdrop/key art;
- production still;
- frame/still image;
- person portrait/headshot;
- title logo/wordmark;
- company logo;
- trailer/teaser video reference;
- trailer thumbnail;
- archival scan;
- certificate/document image;
- soundtrack/album art;
- other promotional media.

## Required Asset entity fields

At minimum:

- `asset_id` — CAS canonical asset ID;
- `asset_type`;
- `work_id` / `person_id` / `company_id` / related entity;
- `version_id` when artwork applies to a particular cut/language release;
- `language`;
- `territory`;
- `source_id`;
- `source_asset_id` / canonical source URL;
- `original_creator` where known;
- `rightsholder` where known;
- `licence_id` / licence text reference;
- `rights_basis`;
- `commercial_use_allowed`;
- `modification_allowed`;
- `attribution_required`;
- `attribution_text`;
- `share_alike_required`;
- `territory_restrictions`;
- `valid_from` / `valid_until` if contractual;
- `hosting_mode` (`SELF_HOSTED`, `PROVIDER_CDN`, `EMBED_ONLY`, `REFERENCE_ONLY`);
- `publication_state`;
- `source_retrieved_at`;
- `rights_verified_at`;
- `rights_verified_by`;
- `checksum` when stored;
- `width`, `height`, `mime_type`;
- `takedown_status`;
- `notes`.

## Rights basis vocabulary

### OPEN_LICENSE_VERIFIED
The asset is published under a licence compatible with our use and all conditions are stored/implemented.

### PUBLIC_DOMAIN_VERIFIED
A defensible public-domain basis has been documented for the relevant jurisdiction/use.

### PROVIDER_LICENSED
A commercial/provider agreement explicitly permits the planned display/hosting behavior.

### RIGHTSHOLDER_PERMISSION
The rightsholder or authorized representative has granted permission.

### PROMOTIONAL_USE_PERMISSION
Specific press/promotional terms allow the planned editorial/product use. Scope must be stored; this must not be assumed merely because a press kit exists.

### EMBED_PLATFORM_AUTHORIZED
Media is rendered via an authorized platform embed/API subject to its policies rather than copied into our storage.

### UNKNOWN / NO_RIGHTS_BASIS
Not publishable.

## Publication states

- `DISCOVERED`
- `RIGHTS_RESEARCH_PENDING`
- `RIGHTS_APPROVED`
- `OPEN_LICENSE_VERIFIED`
- `PUBLIC_DOMAIN_VERIFIED`
- `PROVIDER_LICENSED`
- `EMBED_APPROVED`
- `REJECTED`
- `EXPIRED`
- `TAKEDOWN_PENDING`
- `TAKEN_DOWN`

Public clients may only render states explicitly permitted by policy.

## Publication precedence

When multiple valid assets exist, selection can prefer:

1. official/current primary artwork under a provider/rightsholder licence;
2. official localized artwork licensed for the user's territory/language;
3. rightsholder-approved promotional artwork;
4. verified openly licensed artwork;
5. verified public-domain artwork;
6. Cinema and Series branded placeholder.

A lower-quality but authorized asset beats a beautiful unauthorized asset.

## Source policies

### Wikimedia Commons

Potentially valuable for:
- public-domain historic film material;
- freely licensed portraits;
- freely licensed posters/logos where actually eligible;
- archive photographs.

Rules:
- evaluate each file page individually;
- store licence/version/creator/source/attribution;
- implement ShareAlike requirements where applicable;
- verify that the actual use is compatible with personality/publicity/trademark and other non-copyright rights where relevant;
- do not assume Wikimedia's hosting is a legal warranty.

### TMDB / TheTVDB / IMDb commercial / other metadata providers

Images are usable only if the specific commercial agreement permits our intended product behavior.

Adapter configuration must record:
- display permission;
- CDN hotlink requirements;
- cache duration;
- transformation/resizing permissions;
- attribution/branding;
- termination/delete requirements;
- commercial/mobile/web scope.

The API returning an image path is not by itself the rights basis.

### Studios, streamers, distributors and publicists

Official posters/stills are copyrighted assets even when widely distributed for publicity.

Allowed routes:
- explicit partnership/licence;
- press-kit terms that clearly cover our use;
- written rightsholder permission;
- approved provider acting under a licence.

Do not scrape social feeds or press sites and permanently host assets based solely on public visibility.

### Moviebuff / BookMyShow / OTTplay / editorial sites

No image scraping or republication under the reviewed terms without permission. These can be reference/discovery sources only unless a partnership is obtained.

### YouTube

Preferred trailer strategy:
- identify official studio/distributor/platform channels;
- store YouTube video/channel IDs and compliant API metadata;
- embed with the official YouTube player/API where permitted;
- comply with YouTube branding, playback and metadata refresh/deletion rules;
- do not download/rehost video or extract media streams;
- do not treat thumbnails as permanent owned poster art.

### Film archives

Archival holding/public-domain status and reproduction rights are separate. A film may be public domain while a new restoration scan, photograph, catalogue image or reproduction has additional rights/contract terms. Capture the exact rights basis.

## Primary poster selection model

The canonical `primary poster` is a **derived presentation selection**, not a permanent field on the work.

Selection inputs:
- entity/work/version match;
- publication eligibility;
- target locale/language;
- territory rights;
- official/current status;
- image quality/resolution;
- spoiler/sensitivity policy if later needed;
- provider preference under contracts.

This allows the same film to show a Telugu poster in one context, an English international poster in another, and a public-domain historical poster in archival context without corrupting canonical identity.

## Placeholders

A missing poster must never block a title from appearing.

Cinema and Series should maintain premium branded placeholders based on:
- title typography;
- year/type metadata;
- neutral design tokens;
- no generated imitation of copyrighted poster composition;
- no fake cast likenesses;
- no implication that a generated image is official promotional art.

This guarantees 100% visual renderability even when asset coverage is low.

## Image transformations

Only transform an asset when its licence/contract allows it.

Potential transforms:
- resize;
- crop;
- format optimization;
- responsive derivatives;
- background blur for UI;
- thumbnailing.

Store whether transformations are allowed. Never automatically remove watermarks, copyright notices, signatures or attribution.

## Storage architecture implications

Asset metadata belongs in PostgreSQL; actual binary storage may be:

- our object storage for rights-approved self-hosted assets;
- provider CDN URL where contract requires hotlinking;
- platform embed reference for trailers;
- external archive/open-media URL where policy permits;
- no binary at all for reference-only assets.

A provider URL should not become the immutable identity of the asset; CAS asset identity and source mapping are separate.

## Hashing and duplicate detection

For legally stored assets, compute hashes to:
- detect exact duplicates;
- avoid redundant storage;
- propagate takedowns to exact copies;
- detect provider changes;
- support audit/re-ingestion.

Perceptual hashing may later flag likely visual duplicates, but automated deduplication must not merge assets with different rights/licence records.

## Takedown workflow

Required states:

1. receive complaint/request;
2. immediately flag affected asset and source mapping;
3. if policy/risk requires, hide asset while reviewing;
4. preserve internal audit record and claim/evidence;
5. determine rightsholder/licence status;
6. remove/disable as required;
7. propagate to cached/derived versions;
8. record resolution and date;
9. restore only if rights basis is validated.

Takedown never deletes the title/person itself unless the identity is separately invalid.

## Admin review UX requirements

The admin asset review screen should show:

- preview;
- related title/person;
- source;
- claimed rightsholder;
- licence/terms link;
- rights basis;
- attribution requirements;
- allowed hosting/transforms;
- territory/expiry;
- duplicate detection;
- approve/reject/request-review actions;
- full audit history.

The user/admin should **not** need to manually fill complex rights data when the source adapter/contract already provides deterministic rights metadata. The system should prepopulate it; human review is for ambiguity/exceptions.

## Metrics

Track separately from metadata coverage:

- titles with at least one publishable poster;
- titles with localized poster by language;
- people with publishable portrait;
- assets by rights basis;
- expiring assets;
- pending rights reviews;
- takedowns;
- provider dependency concentration;
- open/public-domain asset share.

Artwork percentage must never be mixed into claims of catalogue identity completeness without being labeled as an asset dimension.

## V1 recommendation

V1 should prioritize **legally safe functionality over artwork completeness**.

Minimum V1 requirement:
- Asset entity/rights schema exists;
- no unauthorized artwork path exists;
- placeholders are production-quality;
- Wikimedia/open assets can be handled with correct attribution;
- licensed/provider assets can later plug into the same model;
- official trailers can be linked/embedded through compliant platform integrations;
- admin rights-review/takedown workflow is specified.

## Rejected shortcuts

- scrape Google Images;
- scrape IMDb/TMDB/Moviebuff/BookMyShow artwork without a permitted licence/path;
- copy posters from Wikipedia pages without checking the underlying file licence;
- claim generic "fair use" as a platform-wide poster strategy;
- remove watermarks;
- use fan posters as official art;
- AI-generate fake official posters for real unreleased films;
- download and self-host YouTube trailers;
- assume studio social posts are automatically licensed for permanent commercial reuse.

## Freeze gate

Before V1 is frozen, we must decide:

1. which asset sources are production-approved;
2. whether a commercial artwork provider is necessary for launch;
3. exact placeholder visual system;
4. asset storage/CDN approach;
5. attribution rendering rules;
6. takedown contact/process;
7. provider termination cleanup behavior;
8. whether official press-kit/rightsholder submissions are supported in V1 or later.
