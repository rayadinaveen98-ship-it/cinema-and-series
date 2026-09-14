# Initial Production Source Baseline — Cinema and Series V1

**Status: LOCKED FOR V1 IMPLEMENTATION BASELINE**  
**Date: 2026-09-14**

## Purpose

This document defines the **minimum legally sustainable production-ingestion baseline** that Cinema and Series may implement first. It deliberately excludes attractive sources whose commercial/licensing/access path is not yet sufficiently safe.

This is not a claim that these sources alone can achieve IMDb-scale completeness. It is the safe foundation on which the catalogue can begin.

# 1. Production baseline

## 1.1 Wikidata structured data — APPROVED BASELINE

**Role:** global open seed, entity discovery, multilingual labels/aliases, external IDs, relationships, people/organizations and selected factual statements.

**Access path:**
- weekly recommended Wikidata entity JSON dumps for baseline/reconciliation;
- daily incremental/add-change dumps for change discovery where operationally useful;
- REST/API or entity fetches for targeted verification/retrieval;
- SPARQL/WDQS for research, validation and targeted queries, **not** as the dependency for full-catalogue bulk ingestion.

**Licensing:** structured data in Wikidata's main/property/lexeme/entity-schema namespaces is CC0.

**Important rule:** Wikidata is an evidence/source adapter. A Wikidata statement becomes a Claim with source identity, qualifiers/references/rank/retrieval metadata where available. It does not directly become canonical CAS truth.

## 1.2 MusicBrainz CC0 core — APPROVED BASELINE

**Role:** music identity and soundtrack relationships for artists, releases, recordings, musical works and core relationships relevant to Cinema and Series.

**Access path:**
- CC0 public full database dump (`mbdump.tar.bz2`) and other explicitly CC0 dump sets;
- web service for targeted lookup within policy/rate limits;
- periodic snapshot refresh.

**Explicitly excluded from unlicensed production ingestion:**
- supplementary CC BY-NC-SA data;
- user tags/ratings/annotations/derived statistics/search indexes/edit history where included in supplementary data;
- Live Data Feed replication packets unless the commercial/licensing path is explicitly approved;
- Cover Art Archive imagery unless its separate rights path is approved by the Asset Engine.

## 1.3 CAS Editorial / Control Room — APPROVED BASELINE

Human research and adjudication may create explicit CAS editor Claims from competent evidence sources. Editors must record source/evidence, context and rationale. Editors may not overwrite canonical projections directly.

## 1.4 Approved source-specific official evidence — MANUAL/ADAPTER-BY-ADAPTER

First-party studios, distributors, platforms, festivals, certification authorities and archives may be used only where the Source Registry and Licensing Matrix explicitly allow the access/use case.

Until a scalable production adapter is approved, such sources operate as:
- discovery leads;
- manual verification/evidence;
- targeted source-specific ingestion where terms permit.

# 2. Not in the initial production baseline

The following must **not** be used as hidden shortcuts in production ingestion:

- IMDb free contributor datasets;
- unlicensed TMDB commercial usage;
- unauthorized Moviebuff scraping;
- unauthorized BookMyShow scraping;
- unauthorized OTTplay scraping;
- CBFC CAPTCHA bypass or bulk scraping without an approved path;
- Wikipedia article text copied into canonical descriptions;
- arbitrary Google/web search results as canonical metadata;
- AI-generated facts without evidence;
- MusicBrainz supplementary/non-commercial data in commercial canonical storage;
- arbitrary posters/stills because they are publicly visible.

# 3. Initial data flow

```text
Wikidata CC0 dump --------------------┐
                                      │
MusicBrainz CC0 core -----------------┼-> SourceSnapshot / source record
                                      │        -> Observation
Approved official/manual evidence ----┘        -> Claim
                                               -> Identity Resolution
                                               -> Canonicalization
                                               -> Canonical Projection
```

No baseline adapter can write directly to canonical Work, Person, Organization, Release or Music facts.

# 4. Wikidata initial field envelope

Wikidata may initially contribute candidate Claims for:

- entity type / work-type signals;
- multilingual labels and aliases;
- original/native title candidates where modeled;
- release/publication dates with qualifiers;
- country/countries of origin;
- language(s);
- cast/crew relationships where statements exist;
- production/distribution organizations where statements exist;
- series/season/episode relationships where sufficiently explicit;
- sequel/prequel/remake/adaptation/franchise relationships where explicit;
- external identifiers (IMDb, TMDB, TheTVDB, MusicBrainz, ISAN/EIDR where present, archive IDs, etc.);
- people names/aliases and selected biographical identity signals;
- references and qualifiers supporting those statements.

Wikidata must **not** be treated as authoritative merely because a statement exists or has preferred rank.

# 5. MusicBrainz initial field envelope

Only fields verified as CC0 core may feed production Claims. Initial useful entities/signals include:

- Artist identity and aliases;
- Release Group / Release identity as applicable;
- Recording identity;
- Musical Work identity;
- track/medium relationships contained in the CC0 dump;
- artist credits;
- composition/performance/relationship metadata that belongs to the CC0 core;
- external identifiers/URLs where core and permissible;
- language/date/country data where core and source-supported.

The adapter must carry the originating MBID as an ExternalIdentifier only. MBIDs are not CAS canonical IDs and may be redirected/merged over time.

# 6. Freshness strategy

## Wikidata
- periodic full reconciliation from weekly JSON entity dump;
- daily incremental/add-change processing where technically validated;
- targeted entity refresh for active/upcoming titles and identity conflicts;
- preserve previous Claims when source statements change; never mutate history invisibly.

## MusicBrainz
- periodic CC0 snapshot refresh; initial target: at least weekly, aligned with available dump cadence;
- targeted API lookup only for permitted use and rate limits;
- do not use non-commercial Live Data Feed packets in commercial production unless separately approved.

# 7. Provider loss behavior

If Wikidata or MusicBrainz becomes temporarily unavailable:

- CAS canonical IDs survive;
- accepted historical Claims remain with provenance subject to retention policy;
- ingestion/refresh is marked stale/degraded;
- no entity is deleted merely because an upstream provider is unavailable;
- future reconciliation resumes when the adapter returns.

If licence/access terms materially change, the adapter kill switch is activated and source-policy review determines whether retained data must be recalculated, isolated or removed.

# 8. What remains manual/partner-dependent at initial launch

The baseline alone does **not** solve:

- authoritative CBFC bulk certification ingestion;
- exhaustive Indian theatrical dates;
- global streaming availability;
- rights-cleared commercial posters/stills for every title;
- exhaustive historical Indian credits;
- IMDb-scale global completeness;
- live ticketing/showtimes;
- reliable current box office.

These remain explicit coverage gaps, not reasons to violate source terms.

# 9. Freeze consequence

For V1 implementation, production ingestion may begin with:

1. Wikidata structured CC0 adapter;
2. MusicBrainz CC0-core adapter;
3. CAS editorial/manual evidence pipeline;
4. individually approved first-party/authority adapters added only after source-specific review.

Everything else is opt-in by later source approval/ADR or contract.

This baseline resolves the architecture question **"what can the first real database legally and sustainably ingest?"** without pretending it solves final catalogue completeness.