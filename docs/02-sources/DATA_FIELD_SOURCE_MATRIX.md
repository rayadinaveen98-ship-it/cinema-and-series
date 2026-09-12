# Data Field Source Matrix — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

This document answers the most important sourcing question in Cinema and Series:

> For each canonical data domain, what evidence can establish it, what source paths are sustainable, how fresh must it be, and what happens if the preferred provider disappears?

A source appearing in this matrix is **not automatically approved for production**. `SOURCE_REGISTRY.md`, `SOURCE_LICENSING_MATRIX.md`, and adapter status remain binding.

## Source strategy notation

- **A** — direct authority / first party
- **B** — open structured source
- **C** — licensed/commercial provider
- **D** — curated/reference/archive source
- **H** — human/manual verification path

## V1 priority notation

- **P0** — fundamental; a trustworthy catalogue cannot exist without it
- **P1** — required for V1 quality
- **P2** — desirable when source-supported; not a blocker for every title
- **Later** — architecturally supported but not required for first V1 release

## Core identity

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| CAS canonical ID | P0 | Cinema and Series Identity Engine | none | permanent | Never sourced externally; immutable identity with merge/split history |
| Media/work type | P0 | A official/credits + B Wikidata + C licensed provider | D archive/catalogue | F3/F4 | Must normalize feature, short, series, miniseries, episode, special etc. |
| Canonical display title | P0 | A official final title; D archive for historical; B/C corroboration | H review | F3/F4 | Display title is locale-dependent; original title stored separately |
| Original title | P0 | A original work/credits/producer; D archive | B Wikidata/C provider | F3/F4 | Native script preserved |
| Original script | P1 | Unicode/script detection + sourced title language | H review | F3/F4 | Derived metadata permitted when deterministic |
| Alternate titles | P1 | A release materials + B Wikidata + C provider + D archive | H | F3/F4 | Each alias carries language/territory/type/source |
| Working title | P2 | A production announcement/trade evidence | H | F2 then historical | Must not replace final title; stored with validity/history |
| Year label | P0 | Derived from canonical release/premiere model | D archive | event-driven | UI convenience field, not independent truth |
| Original language(s) | P0 | A production/credits + D archive | B Wikidata/C provider | F3/F4 | Supports multiple genuine production languages |
| Production country/countries | P0 | A credits/companies + D archive | B/C | F3/F4 | Not inferred from language |

## People and credits

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Person canonical identity | P0 | CAS identity resolution using A/C/B external mappings | D authority files/H | F3 | Name equality alone never sufficient |
| Person canonical name | P1 | A professional/credit identity + authority references | B Wikidata/C provider | F3 | Preserve native names, aliases, stage names |
| Person aliases/native names | P1 | A/B/D/C | H | F3 | Alias source and script required |
| Cast credit | P0 for principal cast; P1 full cast | A final credits/official credit sheet | C provider/D archive/B referenced Wikidata | F3/F4 | Pre-release cast claims remain status-aware |
| Character name | P1 | A final credits/official material | C provider | F3 | Preserve provider/source wording |
| Credited-as name | P1 | A on-screen credits | C/D | F3/F4 | Important for historical identity |
| Director | P0 | A final credits | D archive/C/B | F3/F4 | Structured job, not title text |
| Writers/story/screenplay/dialogue | P1 | A final credits | D/C/B | F3/F4 | Preserve job distinctions and source wording |
| Producer roles | P1 | A final credits | D/C/B | F3/F4 | Producer/co-producer/executive producer separated |
| Cinematography | P1 | A final credits | D/C/B | F3/F4 | India-deep craft field |
| Editing | P1 | A final credits | D/C/B | F3/F4 | India-deep craft field |
| Music/score composer | P1 | A final credits/soundtrack credits | D/C/B; MusicBrainz for music identity | F3/F4 | Distinguish songs/score where possible |
| Lyricists/playback singers | P2 | A soundtrack/film credits | MusicBrainz core where applicable/D/C | F3/F4 | Strong India value; track-level later if data exists |
| Choreography/action/production design/costume/sound/VFX | P2 | A final credits | D/C | F3/F4 | Model as normalized jobs/departments |

## Companies and organizations

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Production company | P0 | A final credits/official production material | B Wikidata/C/D | F3/F4 | Company identity separate from role |
| Presenter/financier | P2 | A credits | C/D | F3 | Separate role |
| Distributor by territory | P1 | A distributor/release material | C/D/ticketing corroboration | F2/F3 | Territory/date-sensitive |
| Broadcaster/network/platform original | P1 for series/streaming originals | A platform/broadcaster | C/B | F2/F3 | Do not conflate platform with production company |
| Music label | P2 | A soundtrack/credit material | MusicBrainz/D/C | F3 | Later soundtrack integration |
| Post/VFX vendor | P2 | A credits | D/C | F3 | Optional completeness dimension |

## Production lifecycle and upcoming projects

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Project existence before release | P0 for future catalogue | A producer/studio/platform/distributor announcement | T3 reputable trade as candidate lead | F2/event-driven | Weak rumor stays outside canonical catalogue or in lead queue |
| Production status | P1 | A production/studio/platform | reputable trade with evidence | F2 | History retained, not overwritten |
| Announcement date | P1 | A original announcement timestamp | trade archive | historical after event | Announcement is event, not release |
| Filming start/end | P2 | A production/team announcement | trade reporting | F2 | Approximate precision permitted |
| Shelved/on-hold/cancelled status | P1 when known | A producer/studio/platform or strong trade evidence | H | F2 | Preserve prior lifecycle |
| Working/final title transition | P1 | A | C/D | event-driven | Alias/history relationship |

## Release and premiere events

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| World premiere | P1 | A festival/producer/distributor | D archive/trade/C | F2/F4 | Must identify premiere type and venue/territory |
| Festival screening | P2 | A festival programme | archive/trade | event-driven | Multiple screenings possible |
| Theatrical release by territory | P0 | A distributor/studio + actual market observation | licensed provider/ticketing/trade/archive | F1 near release then F3/F4 | Scheduled and actual dates separate |
| Language-version release | P1 | A distributor/version material | C/D | F2/F3 | Link to version/dub identity |
| Re-release | P1 | A distributor/archive/venue | trade/ticketing | F1/F3 | New ReleaseEvent, never overwrite original |
| Restoration screening/release | P2 | A archive/restoration producer/festival | D archive | F3/F4 | Link restored version |
| Digital purchase/rental release | P2 | A platform/distributor or licensed availability partner | C | F1 | Offer type is temporal |
| Streaming subscription release | P1 | A platform or licensed availability provider | C partner | F1 | Territory/provider/time-specific |
| Physical-media release | P2/Later | A distributor/label | licensed catalogues | F2/F3 | Version/region specific |
| Postponement/cancellation of release | P1 | A distributor/studio/platform | strong trade | F1/F2 | Prior scheduled event preserved as superseded/cancelled |

## Certification and regulatory metadata

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| India CBFC rating | P1 for India releases | A CBFC | licensed provider/D corroboration | F3 | Current public site useful for manual verification; no CAPTCHA bypass |
| CBFC certificate number/date | P2 | A CBFC | H evidence record | F3 | Version-specific |
| Certified length | P2 | A CBFC | C/D | F3 | Do not equate automatically with every released runtime |
| Other country ratings | P1 for priority markets | issuing national/regional authority | C provider/D | F3 | Source registry expansion required country by country |
| Content advisory/reason | P2 | issuing authority | licensed provider | F3 | Jurisdiction-specific taxonomy |

## Runtime and versions

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Runtime | P0/P1 | version-specific authoritative record/actual media metadata/official credits | C provider/D archive | F3/F4 | Store precision/source/version; conflicting runtimes are expected |
| Director's/extended/censored cut | P2 | A distributor/creator/home-media source | C/D | F3 | Separate Version entity where materially distinct |
| Restoration version | P2 | A archive/restoration distributor | D | F3/F4 | Restoration date/organization captured |
| Dub version | P1 | A distributor/platform/credits | C/D | F3 | Same work by default unless evidence shows separately produced work |
| Simultaneously shot language version | P1 | A production evidence | D/C/H | F3 | Explicit relationship; not auto-classified as dub/remake |

## Series hierarchy

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Series identity | P0 | A broadcaster/platform + CAS resolver | C TheTVDB/TMDB/IMDb licensed + B | F2/F3 | Reboots/same-name series remain separate works |
| Season identity/order | P0 | A broadcaster/platform | C provider | F2 | Support parts/specials without forcing false season numbers |
| Episode identity | P0 | A broadcaster/platform | C provider | F1/F2 | Stable CAS ID independent of provider numbering |
| Episode number/order | P1 | A | C | F1/F2 | Aired/order/production order can coexist |
| Episode title | P1 | A | C/B | F1/F2 | Localized aliases supported |
| Episode release date | P1 | A platform/broadcaster | C provider | F1/F2 | Territory/platform-sensitive for streaming |
| Episode runtime | P2 | A/platform metadata | C | F2/F3 | Episode-specific |
| Series status | P1 | A network/platform | C/trade | F2 | returning/ended/cancelled etc, with events |

## Relationships and graph

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Sequel/prequel | P1 | A official narrative/franchise material | C/D/B with references | F3 | Directionality explicit |
| Franchise/universe membership | P1/P2 | A rights-holder/studio | C/D | F3 | Avoid marketing inference without evidence |
| Remake relationship | P1 | A credits/rights-holder/creator | scholarly/trade/D | F3/F4 | Similarity alone insufficient |
| Adaptation/source work | P1 | A credits/official source | D scholarly/B referenced | F3/F4 | Link to external literary/work entity model later |
| Spin-off/reboot | P2 | A | C/D/trade | F3 | Provenance required |
| Alternate cut/restoration/dub relationship | P1/P2 | A/version evidence | C/D | F3 | Version graph |
| Anthology/segment membership | P2 | A final credits/program | C/D | F3 | Structural relationship |

## Descriptive metadata

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Synopsis/overview | P1 | licensed text source or rights-cleared first-party synopsis; alternatively original CAS editorial summary with source-backed facts | none by default | F3 | Do not copy copyrighted descriptions from arbitrary sites. AI may assist drafting only from cited facts and must not invent plot facts |
| Genres | P1 | CAS normalized taxonomy mapped from A/B/C claims | H editorial mapping | F3 | Provider genres are inputs, not our immutable taxonomy |
| Keywords/themes | P2/Later | licensed/open source + CAS normalized taxonomy | editorial contribution | F3 | Avoid copying proprietary keyword databases without rights |
| Content warnings | Later | issuing authority/provider/user systems | — | varies | Separate product domain |

## Artwork and media

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Primary poster | P1 for UX, not record validity | rights-cleared official/licensed provider asset | Wikimedia Commons open/public-domain asset | rights/event driven | Only publish if Asset Engine state permits; otherwise branded placeholder |
| Backdrop/still | P2 | licensed/rights-cleared source | open-license Commons | rights/event driven | Not required for metadata completeness |
| Person image | P2 | open/licensed/rights-cleared | Commons | rights/event driven | Identity record survives without portrait |
| Logo/title treatment | P2 | official licensed promotional material | open/public-domain where applicable | rights/event driven | Asset rights tracked separately |
| Trailer | P1/P2 | link/embed official YouTube/platform video using compliant API/client | studio/player embed | F1/F2 | Store platform/video identity, not unauthorized video copy |
| Trailer thumbnail | P2 | platform API under client policies | own generic thumbnail | F1 | Refresh/delete policy as required; not permanent owned artwork |

## Streaming/current availability

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Provider | P1 later in V1 if licensed path ready | JustWatch/other licensed availability partner or platform API | direct manual evidence | F1 | Must not block core catalogue launch if licensing unresolved |
| Offer type | P1 with availability | partner/platform | — | F1 | subscription/rent/buy/free/ad-supported/channel |
| Territory | P0 with availability | partner/platform | — | F1 | Required |
| Availability start/end observation | P1 | observation history | — | F1 | Temporal, not permanent fact |
| Audio/subtitle language availability | P2 | provider/partner | — | F1 | Platform/version specific |

## Historical/archive metadata

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Freshness | Notes |
|---|---:|---|---|---|---|
| Lost/partially lost status | P2 | archive/scholarly authority | B/D corroboration | F4 | Scope/definition recorded |
| Archive holdings | P2 | holding institution | FIAF/union catalog | F4 | Holding copy != rights ownership |
| Restoration history | P2 | archive/restoration project | festival/D | F4 | Event/version model |
| Approximate date | P1 where needed | archive/primary historical record | D scholarly | F4 | Store precision; never invent Jan 1 |
| Disputed historical credit/date | P1 where conflict exists | multiple D/A evidence claims | H | F4 | Public conflict state allowed |

## External identifiers

| Identifier | Priority | Source strategy | Notes |
|---|---:|---|---|
| IMDb ID | P1 | Wikidata/provider/manual mapping | External only; support redirects/remaps |
| TMDB ID | P1 | Wikidata/TMDB adapter | External only |
| TheTVDB ID | P1 for series | provider/Wikidata | External only |
| Wikidata QID | P1 | Wikidata | Excellent cross-ID anchor, not CAS primary key |
| EIDR ID | P2 | EIDR/partner mappings | High-value industry identity signal |
| ISAN | P2 | ISAN/partner mappings | Work/version identity signal |
| MusicBrainz IDs | P2/Later | MusicBrainz | Soundtrack/artist domain |
| Archive catalogue IDs | P2 | archive source | Institution-specific |
| Platform IDs | P2 | platform/provider | Version/offer/media links only |

## Ratings, reviews, box office, social data

These are **not core V1 catalogue requirements**.

| Domain | V1 status | Future sustainable source strategy |
|---|---|---|
| User ratings | NON-GOAL initially | own Cinema and Series rating system |
| IMDb rating | Later | licensed IMDb product if desired |
| Rotten Tomatoes | Later | licensed/approved integration |
| Metacritic | Later | licensed/approved integration |
| User reviews | NON-GOAL initially | own community system |
| Box office | Later unless reliable provider secured | licensed measurement/trade/official sources |
| Social popularity | Later | compliant platform APIs/own interactions |

The core database must never depend on these domains to establish title identity.

## Minimum sustainable-source requirement by V1 domain

### Core identity
Must have an open and/or first-party path that does not require a single commercial provider. Current foundation: Wikidata + official/archive evidence + CAS reconciliation.

### Released credits
Must support first-party/archive/manual evidence, with licensed provider acceleration optional.

### Historical titles
Must support archive/scholarly federation; no single consumer API is sufficient.

### Upcoming projects
Must support first-party announcement monitoring plus reputable-trade discovery; rumours cannot directly create canonical truth.

### Indian certification
Must support CBFC manual/official verification now; scalable production automation remains an OPEN access problem and is not allowed to bypass CAPTCHA.

### Streaming availability
A licensed provider path is preferred. If none is secured, availability can be excluded/delayed without compromising the catalogue foundation.

### Artwork
No movie record depends on copyrighted artwork. Rights-cleared/open/licensed asset or placeholder are the only acceptable rendering paths.

## Provider-loss fallbacks

| Dependency lost | System behavior |
|---|---|
| TMDB | CAS IDs/data remain; disable adapter; use Wikidata/official/archive/other licensed providers |
| TheTVDB | Series IDs remain; rebuild affected projections from other sources/manual queues |
| IMDb commercial | CAS identities remain; no deletion of canonical works; external mapping retained where permitted |
| JustWatch | Current availability marked stale/unknown after TTL; catalogue unaffected |
| Wikidata live endpoint | Use approved dumps/cache ingestion; catalogue does not depend on query endpoint uptime |
| Artwork provider | Assets subject to licence/contract handling; replace with rights-approved alternatives/placeholders |
| CBFC website unavailable | Existing provenance retained; new certification remains pending rather than guessed |

## Open research items before freeze

1. Priority-country certification authority matrix.
2. Priority-country national archive matrix.
3. Major global and Indian festival source registry.
4. Commercial-provider cost/contract comparison when launch economics are defined.
5. Sustainable automated CBFC access or explicit decision to keep certification verification manual.
6. Definitive synopsis/content-writing policy.
7. Artwork licensing/partner strategy after V1 visual requirements are known.
8. Availability provider selection or explicit defer decision.
9. Box-office provider research if promoted into V1 scope.
10. Validation of source coverage using the adversarial ~1,000-title corpus.

## Freeze rule

No field may enter `FROZEN_V1_CONTRACT.md` as required unless this matrix identifies:

- a permitted source strategy;
- fallback behavior;
- trust/authority ordering;
- freshness requirement where volatile;
- version/territory context where material;
- and a behavior for `UNKNOWN` when evidence is unavailable.

**Unknown is always preferable to fabricated data.**
