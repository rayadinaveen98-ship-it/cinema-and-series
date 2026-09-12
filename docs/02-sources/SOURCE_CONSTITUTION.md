# Source Constitution

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Purpose

Cinema and Series is a multi-source data product. No single provider is allowed to define the product's identity, truth model, or long-term survivability.

## Source classes

### Class A — Authoritative / first party
Examples: production companies, studios, distributors, broadcasters, streaming platforms, official film/series websites, certification authorities, festivals, official trailers/channels, official creator/project announcements where appropriate.

Use primarily for announcement state, production status, dates, credits, titles, official media, and release information when the source is competent for that field.

### Class B — Open structured knowledge
Open datasets whose license permits the intended reuse. Wikidata is a priority research candidate because its structured data is CC0, but field quality and completeness must still be measured rather than assumed.

### Class C — Licensed/commercial metadata providers
Commercial or partner data providers may later increase global coverage or availability data. They are adapters into our model, not our canonical database.

### Class D — Discovery/reference sources
Press, trade publications, ticketing services, cinema portals, public catalogues, community databases, and other sources may help discover or corroborate facts. Reuse must follow applicable terms, licenses, and rights constraints.

## Non-negotiable rules

1. Public visibility does not automatically grant permission to scrape, store, or republish.
2. Metadata rights and artwork/media rights are evaluated separately.
3. Each source receives a documented access method, permitted use, attribution requirement, commercial-use status, freshness expectation, and failure mode.
4. A source may be reliable for one field and weak for another; trust is field-specific where practical.
5. Raw source observations are preserved so parsers can be re-run and decisions can be audited.
6. Ingestion creates observations/claims. It does not directly overwrite canonical truth.
7. Source disappearance or access loss must not invalidate Cinema and Series canonical IDs.
8. Paid/licensed providers must remain replaceable behind adapters unless contractual reality requires otherwise.
9. Terms/licensing changes are treated as operational incidents and reviewed before continued ingestion.
10. No source enters production ingestion until it appears in the Source Registry and Licensing Matrix with an explicit status.

## Initial policy decisions from research

### IMDb free datasets
**REJECTED for building/republishing our production database under the free non-commercial dataset terms.** IMDb's free datasets must not be treated as a free production-ingestion source for Cinema and Series. Commercial IMDb data may be evaluated separately as a future licensed provider.

### TMDB
**WORKING: potential adapter, never foundation.** Its developer API can be useful for research/prototyping under applicable terms, but commercial use/licensing and attribution must be evaluated before production use. TMDB IDs remain external mappings only.

### Wikidata
**WORKING: priority open-data candidate.** Structured data licensing is favorable for ingestion, but coverage, field quality, entity identity, vandalism/error handling, and refresh strategy must be benchmarked.

### Official/first-party sources
**WORKING: highest-authority candidates for fields they directly control.** Access and reuse rights still need source-by-source review; "official" does not automatically mean bulk republication rights for every asset.

### Streaming availability providers such as JustWatch
**WORKING: partner/licensing candidate rather than assumed free infrastructure.** Availability should live behind a provider abstraction.

## Source lifecycle

Each source must move through:

`DISCOVERED -> RESEARCHED -> LEGAL/TERMS REVIEWED -> TECHNICALLY VALIDATED -> APPROVED_FOR_TEST -> APPROVED_FOR_PRODUCTION`

Possible exits:

`REJECTED`, `SUSPENDED`, `DEPRECATED`.

## Required source record fields

At minimum:

- source_id
- name
- organization
- source_class
- canonical URL/domain
- access method
- authentication requirements
- fields offered
- territories/languages/title types covered
- update frequency
- rate limits/quotas
- cost
- terms URL/reference
- license/reuse status
- commercial-use status
- attribution requirements
- artwork/media rights notes
- robots/scraping constraints where relevant
- field-specific trust notes
- freshness SLA expectation
- parser/adapter owner
- last policy review date
- operational status
- fallback sources

## Pending research

The definitive Source Registry, Licensing Matrix, Trust Model, and Data Field Source Matrix remain OPEN and must be completed before V1 freeze.
