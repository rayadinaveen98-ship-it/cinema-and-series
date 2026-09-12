# Source Trust Model — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series must not use a simplistic rule such as "official source always wins" or "IMDb/TMDB is the truth". Trust is **field-specific, time-sensitive, version-sensitive, and evidence-sensitive**.

The trust model decides how claims are compared. It does not replace provenance, and it does not erase conflicts.

## Core principles

1. **Trust belongs to a source + field + context, not merely a source name.**
2. **Direct authority beats general popularity for facts the authority actually controls.**
3. **Freshness matters differently by field.** A streaming offer can be stale in hours; a 1957 director credit can remain valid indefinitely.
4. **Version matching matters.** A runtime from a US Blu-ray does not automatically describe an Indian theatrical cut.
5. **Independent corroboration matters.** Ten sites repeating the same press release are not ten independent sources.
6. **Specific evidence beats inferred evidence.** A certificate record is stronger than an article saying a film was "certified".
7. **Source reliability can evolve.** Adapters maintain historical quality metrics.
8. **Canonicalization never deletes dissenting claims.** It selects a current presentation value while preserving evidence.
9. **Licensing and factual trust are separate.** A highly authoritative source may be reference-only if reuse is not permitted.
10. **AI is never a source.** AI can rank or extract evidence, but cannot create factual authority.

## Evidence tiers

These tiers are a starting prior. Field-specific rules can move a source up/down.

### T5 — Direct controlling authority

Examples:
- certification authority for a certificate it issued;
- studio/producer/distributor for its own officially announced release date or production state;
- streaming platform for availability on its own service at the observation time;
- official festival programme for its own selection/screening;
- original on-screen credits or official credit sheet for final production credits;
- registry/identifier authority for identifiers it assigned.

**Meaning:** strongest available direct evidence for the fact under its control.

### T4 — Authoritative curated institution / specialist source

Examples:
- national film archive for its holdings/history;
- scholarly film catalogue within its documented scope;
- licensed professional metadata provider with editorial controls;
- reputable industry registry;
- official library/film-institute catalogue.

**Meaning:** high-quality curated evidence, but not necessarily the original issuer of every fact.

### T3 — Established secondary source

Examples:
- reputable trade publication;
- established editorial database/community database with moderation;
- ticketing platform for current theatrical observations;
- reputable contemporary press with named sourcing.

**Meaning:** valuable corroboration/discovery; may be canonical when stronger sources are unavailable and evidence is coherent.

### T2 — Community/reference source

Examples:
- Wikidata statement with weak/no reference;
- Wikipedia article used only as a discovery lead;
- community-edit database record without traceable evidence;
- user contribution from an established contributor without documentary evidence.

**Meaning:** useful candidate claim; corroboration preferred for important facts.

### T1 — Weak/unverified lead

Examples:
- entertainment rumor page;
- unnamed social-media claim;
- scraped aggregation page with unclear origin;
- forum post.

**Meaning:** discovery only. Does not become canonical for important fields without stronger evidence.

### T0 — Unsupported / synthetic

Examples:
- AI-generated assertion without source;
- guessed date;
- inferred person identity from name alone;
- fabricated poster metadata.

**Meaning:** prohibited as canonical evidence.

## Trust dimensions

Canonicalization should evaluate the following dimensions independently rather than multiplying arbitrary decimal scores.

### Authority
Does the source control or formally document the fact?

### Directness
Is the claim directly stated, or inferred from context?

### Specificity
Does the source identify the exact work/version/territory/person concerned?

### Freshness
Is the observation recent enough for this field?

### Version match
Does the evidence apply to the same cut/language/territory/release being resolved?

### Independence
Is the source independently reporting/observing, or repeating another source?

### Documentary quality
Does the source provide a certificate, programme, credit roll, official release, archive record or other concrete evidence?

### Historical track record
Has this source/adapter previously produced accurate claims for this field?

### Internal consistency
Does the claim conflict with the same source's related fields or known constraints?

## Field-specific authority examples

| Field | Strongest source types | Useful secondary sources | Weak/discovery-only |
|---|---|---|---|
| Certification | issuing rating/certification body | licensed curated DB, distributor | general articles/community DB |
| Official title | on-screen/official producer/distributor/platform/festival material | archive/catalogue/licensed DB | unsourced aggregation |
| Original language | final work/official credits/producer + archive evidence | curated DB/Wikidata with references | title spelling inference |
| Final cast/crew | on-screen credits, official credit sheet | archive/licensed DB, reputable industry DB | rumors/pre-release articles |
| Upcoming cast | producer/studio/platform/performer official announcement | major trade reporting | fan pages/rumors |
| Future release date | distributor/studio/platform/festival | ticketing platform near release, major trade | generic DB without source |
| Actual theatrical release | distributor/venue/ticketing observation + contemporary records | archive/trade press | old unsourced DB field |
| Historical premiere | archive/festival catalog/contemporary primary documentation | AFI/BFI/NFAI/scholarly catalogue | retrospective unsourced article |
| Runtime | certificate/version-specific technical record, actual media version | provider metadata with version context | generic runtime copied across versions |
| Streaming availability | provider itself or licensed availability partner | current reputable aggregator | old article/search snippet |
| Production status | production company/studio/platform | reputable trade with production evidence | rumors |
| Remake/adaptation relationship | official credits/rights-holder/creator documentation | scholarly/trade evidence | similarity/opinion alone |
| Box office | audited/official distributor/exhibitor data where available | reputable trade/measurement provider | promotional claims without methodology |
| Series episode order | broadcaster/platform/official episode listing | TV metadata provider | fan ordering without evidence |
| Person identity | official/agency/professional credits + unique external IDs | curated DB/authority file | same-name match alone |

## Freshness classes

### F0 — Live / intraday
Examples: showtimes, ticket availability.

Expected refresh: minutes to hours.

### F1 — Daily
Examples: streaming availability, near-term release status, active festival schedules.

Expected refresh: at least daily for monitored priority titles.

### F2 — Weekly / event-driven
Examples: productions in filming/post, future release dates months away, announced cast.

Expected refresh: weekly plus event-triggered updates.

### F3 — Stable current metadata
Examples: released-film cast/crew, final title, production companies.

Expected refresh: on source changes/corrections and periodic audits.

### F4 — Historical archival
Examples: silent-film records, old release dates, archival holdings.

Expected refresh: correction/collection driven; staleness is less important than source quality.

## Independence rules

Claims are not considered independent merely because they have different URLs.

The system should record, where detectable:
- original press release/source;
- syndication relationship;
- copied wording/hash similarity;
- citation chain;
- common wire service;
- common provider identifier.

Example:

`Studio announcement -> 30 news sites copy announcement`

This is principally one first-party claim plus secondary propagation, not 31 independent confirmations.

## Conflict states

A canonical field can have one of:

- `UNCONTESTED`
- `SUPPORTED`
- `CONFLICT_PRESENT`
- `DISPUTED`
- `UNRESOLVED`
- `HISTORICAL_SUPERSEDED`

### Example: future release reschedule

Old official announcement: 2027-08-07  
New official announcement: 2027-08-14

Do **not** mark the first claim as false/deleted. Mark it superseded in the release-event history.

### Example: historical dispute

Archive A: premiere 1954-03-12  
Archive B: premiere 1954-03-19

If neither can be decisively resolved, canonical presentation may display one preferred value with a visible conflict marker or show the date as disputed rather than inventing certainty.

## User-facing evidence labels

Avoid fake precision such as `confidence = 82%` unless a calibrated model genuinely supports that probability.

Preferred labels:

### OFFICIAL
A competent direct authority states the fact.

### CONFIRMED
Strong direct or independently corroborated evidence supports the fact with no material conflict.

### STRONGLY SUPPORTED
Good evidence exists, but it is not direct official authority or there are minor limitations.

### UNVERIFIED
Only weak/preliminary evidence exists. Important unverified facts generally stay out of canonical public fields unless the UI explicitly presents them as leads/rumours.

### CONFLICTING
Material credible sources disagree.

### UNKNOWN
No sufficient evidence.

## Canonicalization rules

### Rule 1 — No claim, no fact
Every non-derived canonical value must resolve to one or more source claims.

### Rule 2 — Newer does not automatically mean better
A newer blog post does not override an archival certificate.

### Rule 3 — Official does not always override observation
A platform may announce a release date that later passes without release. The historical model should preserve the announcement while actual-release evidence determines whether release occurred.

### Rule 4 — Version context is mandatory where material
Runtime/certification/language/release claims cannot override another version merely because source authority is higher.

### Rule 5 — Strong conflicts enter review
Automatic canonicalization stops when:
- two T5 claims conflict materially without temporal supersession;
- identity is uncertain;
- a relationship such as remake/dub is ambiguous;
- historical evidence cannot be reconciled;
- a person merge could corrupt many credits.

### Rule 6 — Human override requires reason
Manual canonical overrides must store:
- reviewer;
- timestamp;
- chosen claim/value;
- rejected/superseded claims;
- rationale;
- optional evidence note;
- review expiry if temporary.

## Trust by source currently researched

This table is illustrative, not a global rank.

| Source | Strong fields | Caution fields |
|---|---|---|
| CBFC | Indian certification, certified length/date/no. | not a complete catalogue; public bulk access unavailable |
| Studio/producer/distributor | own announcements/status/releases | promotional wording, future plans can change |
| Festival | its own selection/screening/premiere evidence | not authority for all worldwide releases |
| NFAI/BFI/AFI/FIAF resources | archival holdings/historical research within scope | coverage incomplete outside mission |
| IMDb licensed | broad metadata/credits/releases | provider-specific errors still possible; source evidence often not exposed to us |
| TheTVDB | TV hierarchy/metadata | community/provider corrections still possible |
| TMDB | localization/images/general metadata | community quality varies; provider not direct authority |
| Wikidata | cross-ID graph/multilingual identity when referenced | statement completeness/reference quality variable |
| Moviebuff | India-specific metadata benchmark | reuse requires permission; field provenance often not public |
| BookMyShow | near-term/current Indian showtime observation | weak historical archive source |
| JustWatch | licensed/current availability | availability expires quickly |
| Indiancine.ma/Cinemaazi | historical Indian discovery/scholarship | reuse constraints and acknowledged incomplete historical records |

## Quality feedback loop

The system should compute operational reliability statistics without presenting them as universal truth scores.

Examples:
- percent of claims later superseded/corrected by field;
- duplicate false-positive rate per source;
- future-release-date change frequency;
- stale availability rate;
- person-identity collision rate;
- parser extraction error rate;
- source response freshness/uptime.

These metrics can adjust automated review thresholds while preserving the human-readable evidence model above.

## Review queues triggered by trust model

- `IDENTITY_AMBIGUOUS`
- `HIGH_AUTHORITY_CONFLICT`
- `VERSION_MISMATCH`
- `HISTORICAL_DATE_CONFLICT`
- `RELATIONSHIP_UNVERIFIED`
- `PERSON_COLLISION`
- `SOURCE_STALE`
- `SOURCE_POLICY_CHANGED`
- `ASSET_RIGHTS_UNCLEAR`

## Freeze requirement

Before V1 is FROZEN:

1. every required field in `DATA_FIELD_SOURCE_MATRIX.md` must define its authority order;
2. automated canonicalization tests must cover conflicts and supersession;
3. no important field may rely on a T1/T0 source path;
4. freshness requirements must exist for volatile fields;
5. manual-review thresholds must be documented;
6. public evidence labels must map deterministically from claim state rather than arbitrary UI judgement.
