# Source Licensing Matrix — Research Foundation v0.1

**Status: WORKING**  
**Policy review date: 2026-09-12**

> This is an engineering/product policy record based on publicly available terms reviewed during Research Foundation v0.1. It is not a substitute for legal advice. Before a commercial public launch, material provider agreements and ambiguous licence interactions should receive qualified legal review.

## Decision vocabulary

- **GREEN — production-compatible candidate:** public terms appear compatible with the planned use, subject to listed conditions.
- **AMBER — test/reference/conditional:** useful, but commercial reuse, ShareAlike, provider agreement, field scope, refresh policy, or rights questions must be resolved.
- **RED — not permitted for our production ingestion under reviewed terms.**
- **BLUE — first-party authority/reference:** highly valuable evidence, but no scalable reuse right/API has yet been established.

## Matrix

| Source | Structured metadata reuse | Commercial production | Automated/bulk access | Artwork/media | Attribution / special obligations | Decision |
|---|---|---|---|---|---|---|
| Wikidata | CC0 structured data | Yes under CC0 | API/SPARQL/dumps | Not applicable to most structured records | Preserve provenance as our policy even when not legally required | GREEN |
| Wikipedia | CC BY-SA text | Possible if licence obligations satisfied | APIs available | Media has separate licences | Attribution + ShareAlike for reused article text | AMBER / reference-first |
| Wikimedia Commons | Per-file free licence/public domain | Often yes, file dependent | API available | Yes, but every file differs | Per-file attribution/licence/SA/other rights | AMBER with Asset Engine gate |
| IMDb free contributor datasets | Explicit personal/non-commercial restrictions; no repurposing into movie DB | No for our intended database | Downloadable datasets | Not our source path | Required IMDb acknowledgement for permitted use | RED |
| IMDb commercial | Contract/licence dependent | Yes if contracted | GraphQL/bulk via AWS Data Exchange | Contract/product dependent | Contract terms | AMBER / partner required |
| TMDB developer API | Non-commercial with attribution | Commercial licence required | API + ID exports | Images included under provider terms, not owned by us | TMDB attribution; commercial agreement if revenue purpose | AMBER |
| TheTVDB | API licence with published revenue tiers | Yes under appropriate tier | API | Provider says it does not claim ownership of all images/data; downstream rights need care | Attribution required unless approved otherwise | AMBER |
| TVmaze public API | CC BY-SA | Commercial use possible under CC BY-SA, but SA implications need review | Free REST API | API content subject to same published licence context; asset specifics still need caution | Attribution + ShareAlike | AMBER |
| JustWatch | Partner/licence based | Yes through partnership | Partner API/data/widget | Agreement dependent | Partner terms/branding | AMBER / partner required |
| EIDR | Registry/member terms | Agreement dependent | UI/API/sandbox/member services | Not primary artwork source | Participation/terms | AMBER / identity only until agreed |
| ISAN | Registry/API terms | Agreement dependent | API credentials/services | Not primary artwork source | ISAN service terms | AMBER / identity only until agreed |
| CBFC | Public official facts; site is all-rights-reserved | No bulk right established | CAPTCHA public search; no public bulk API found | Certificate scans/media require separate rights | Respect technical controls; government-site terms | BLUE |
| NFDC-NFAI | No general open bulk reuse licence identified | Permission/collaboration needed | Film Search / institutional services | Archive media rights complex | Source-specific | BLUE |
| Indiancine.ma | Site describes non-commercial research purpose; annotations/materials have CC BY-SA terms | Not assumed commercial-compatible | Website/archive | Films depend on copyright status; access restrictions | Research/fair-dealing/CC terms vary | BLUE/AMBER reference only |
| Cinemaazi | Text/images cannot be used without permission per disclaimer | Permission required | Website | Permission/rights required | Attribution/permission as applicable | BLUE/RED for unlicensed reuse |
| Moviebuff | Terms prohibit data mining/scraping; commercial/non-personal reuse requires express permission | Permission required | No unauthorized scraping | Protected content/third-party media | Written permission | RED without partnership; AMBER as partner candidate |
| BookMyShow | Site states content/images are copyright protected and unauthorized use prohibited | Permission/partner route needed | No production bulk API identified | Protected/third-party | Provider/rights-holder terms | BLUE/AMBER partner candidate |
| OTTplay | Terms prohibit automated scraping and copying/republication | Permission/partner route needed | No unauthorized scraping | Protected content | Provider terms | RED without partnership |
| YouTube Data API | API data under YouTube API Terms/Policies | Yes only in compliant approved client use | Quota-controlled API | Video/thumbnail use governed by API/client policies; do not treat as owned assets | resource metadata refresh/delete rules; branding/player rules; quota/audit | AMBER |
| MusicBrainz core | CC0 core database | Yes | API/dumps | Cover Art Archive is separate | Core vs supplementary data must remain distinguished | GREEN for core only |
| MusicBrainz supplementary | CC BY-NC-SA 3.0 | Not for ordinary commercial use without commercial licence | dumps/live feed options | Separate | Attribution + NC + SA unless licensed otherwise | RED for unlicensed commercial production |
| AFI Catalog | Public research access; no open bulk commercial licence identified | Permission/licence review needed | Website search | Rights vary | Source-specific | BLUE |
| BFI National Archive | Public collection search; no general open bulk reuse licence identified | Permission/licence review needed | Website/research services | Archive rights vary | Source-specific | BLUE |
| FIAF databases | Institutional/vendor access | Licensed access | Ovid/ProQuest/institutional | Not a general media source | Vendor terms | AMBER / research institution path |
| Official studio/producer/distributor press | Facts are authoritative but site/content terms vary | Source-by-source | Source-by-source; never assume scraping | Posters/stills/trailers are copyrighted even when promotional | Permission/press-use terms/provider terms | BLUE until source adapter reviewed |
| Official streamer/platform pages | First-party release/status facts | Source-by-source | Source-by-source | Artwork/media copyright remains | Platform terms/API rules | BLUE until source adapter reviewed |
| Official festival catalogues | Strong premiere/selection evidence | Source-by-source | Source-by-source | Stills/posters often rights-holder content | Festival/site terms | BLUE until source reviewed |

## Key policy conclusions

### 1. Facts and database rights are different questions

A factual datum may not itself be copyrightable in some jurisdictions, but copying a protected database, breaching terms, bypassing technical controls, or reproducing protected text/images can still create legal/contractual risk. Engineering policy therefore follows the source's permitted access path rather than relying on a simplistic "facts are free" assumption.

### 2. Metadata licence never automatically grants poster/still rights

The Asset Engine must maintain an independent rights decision for every asset. Examples:

- TMDB returning a poster URL does not make the poster ours.
- TheTVDB stating it does not claim ownership of all images does not itself give Cinema and Series a universal licence.
- A studio posting an official poster publicly does not automatically authorize us to host a permanent commercial copy.
- Wikimedia Commons files can be reused only under each file's specific terms and other applicable rights.

### 3. Open data can still create licence-composition problems

TVmaze's CC BY-SA licence is permissive for reuse, including commercial use, but ShareAlike can affect how a combined/derived dataset must be distributed depending on the facts and legal interpretation. We must not mix ShareAlike data into the canonical proprietary store until the intended boundary and obligations are reviewed.

### 4. IMDb has two completely different source paths

**Free contributor datasets:** RED for our production database.  
**Commercial IMDb products:** legitimate future partner option.

No future engineer may treat the free TSVs as a shortcut.

### 5. TMDB is a test/partner source, not the foundation

The developer API is excellent for prototyping and research, but a revenue-generating production product requires a commercial arrangement. This reinforces the adapter architecture.

### 6. Government/official source authority does not equal bulk-reuse permission

CBFC is the best authority for Indian certification, yet its public interface is CAPTCHA-gated and the site is marked all rights reserved. We can cite/verify facts manually or seek an official data path; we must not bypass the CAPTCHA or assume official status gives unrestricted scraping rights.

### 7. Research sources may still be extremely valuable even when not ingestible

Cinemaazi, Indiancine.ma, Moviebuff, AFI, BFI, NFAI and other archives can reveal:

- missing titles;
- alternate identities;
- disputed dates;
- historical sources;
- relationships;
- deeper credit structures.

A human researcher may use them to discover better evidence, but prohibited content should not be copied into production.

## Source-specific obligations to implement if approved

### Wikidata
- preserve source QID/external mapping;
- record retrieval time and statement references/qualifiers;
- do not assume every statement is correct simply because licence is open.

### Wikimedia Commons
Asset record must include:
- Commons file/page ID;
- original creator;
- source;
- licence identifier/version;
- attribution text;
- public-domain rationale where relevant;
- derivative/ShareAlike obligations;
- verification timestamp;
- takedown path.

### TMDB
If used in production:
- commercial licence completed;
- required TMDB branding/notice implemented;
- API/image use conforms to agreement;
- cache/refresh and termination provisions recorded.

### TheTVDB
If used in production:
- correct revenue tier;
- attribution implemented unless waived;
- image/rightsholder risk policy approved;
- provider ID stored as external mapping only.

### YouTube
If used:
- only official API access;
- quota policy implemented;
- API resource metadata refresh/delete schedule (generally 30 days where required);
- embedded-player requirements respected;
- no video downloading/archival copying through unsupported means;
- no prohibited derived metrics.

### MusicBrainz
- ingest only fields verified to belong to the CC0 core unless another commercial licence is obtained;
- never accidentally mix CC BY-NC-SA supplementary dumps into commercial canonical data.

## Artwork/media publication states

Every asset should have one of:

- `RIGHTS_APPROVED`
- `OPEN_LICENSE_VERIFIED`
- `PUBLIC_DOMAIN_VERIFIED`
- `PROVIDER_LICENSED`
- `PROMOTIONAL_PERMISSION_VERIFIED`
- `PENDING_REVIEW`
- `REJECTED`
- `TAKEDOWN`

Only the first four/five states may be publicly rendered, depending on exact policy.

## Data-source publication states

For every adapter/field combination:

- `INGEST_ALLOWED`
- `INGEST_ALLOWED_WITH_ATTRIBUTION`
- `INGEST_ALLOWED_UNDER_CONTRACT`
- `REFERENCE_ONLY`
- `MANUAL_VERIFICATION_ONLY`
- `PROHIBITED`
- `SUSPENDED_PENDING_TERMS_REVIEW`

This status belongs to the **source + use case + field + environment**, not merely the source name.

## Terms-change monitoring

Provider terms can change. For every production source we must store:

- terms URL/reference;
- policy version/date observed;
- last review date;
- next review date;
- responsible owner;
- change-monitor status;
- kill switch for adapter.

A material terms change is an operational incident. The source can be suspended without deleting already-created Cinema and Series canonical IDs.

## Evidence links reviewed

- IMDb non-commercial use restrictions: https://help.imdb.com/article/imdb/general-information/can-i-use-imdb-data-in-my-software/G5JTRESSHJBBHTGX
- IMDb commercial licensing/developer documentation: https://data.imdb.com/ and https://help.imdb.com/article/imdb/general-information/content-licensing/GZGA5HDQ8NE97LVR
- TMDB API FAQ: https://developer.themoviedb.org/docs/faq
- TheTVDB API/licensing: https://thetvdb.com/api-information
- TVmaze API/licensing: https://www.tvmaze.com/api
- Wikidata licensing: https://www.wikidata.org/wiki/Wikidata:Licensing
- Wikimedia reuse guidance: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia
- JustWatch partnerships: https://partners.justwatch.com/
- EIDR: https://www.eidr.org/
- ISAN: https://www.isan.org/
- CBFC Film Search/FAQ: https://www.cbfcindia.gov.in/cbfcAdmin/search-film.php and https://cbfcindia.gov.in/cbfcAdmin/faq.php
- NFDC-NFAI: https://nfai.nfdcindia.com/
- Indiancine.ma copyright/about: https://indiancine.ma/copyrights and https://indiancine.ma/about
- Cinemaazi disclaimer: https://www.cinemaazi.com/disclaimer
- Moviebuff Terms: https://www.moviebuff.com/info/terms
- BookMyShow: https://in.bookmyshow.com/terms-and-conditions
- OTTplay Terms: https://www.ottplay.com/terms-of-use
- YouTube Data API policies/docs: https://developers.google.com/youtube/v3/ and https://developers.google.com/youtube/terms/
- MusicBrainz data licence: https://musicbrainz.org/doc/About/Data_License

## Freeze gate

Before `FROZEN_V1_CONTRACT.md` can be marked FROZEN:

1. every V1 data field must have at least one legally sustainable source strategy;
2. every production adapter must be explicitly approved;
3. no RED source can appear in production ingestion code;
4. ShareAlike/contractual boundary questions must be resolved;
5. artwork strategy must have a functioning rights gate;
6. a provider-loss scenario must exist for every critical field.
