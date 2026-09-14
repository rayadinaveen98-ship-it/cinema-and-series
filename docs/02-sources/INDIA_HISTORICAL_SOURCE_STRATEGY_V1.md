# India Historical Source Strategy — V1

**Status: LOCKED**  
**Date: 2026-09-14**

## Goal

Build historically meaningful Indian cinema coverage without pretending that a lawful open bulk source currently gives us everything and without scraping archives whose terms do not permit it.

# V1 strategy

## Production-ingestible baseline

1. **Wikidata CC0 structured data** for open historical seed and cross-identifiers.
2. **CAS editorial Claims** created from competent historical/archival evidence with source locators.
3. Any other open/public-domain structured dataset only after explicit Source Registry approval.

## High-authority manual/reference evidence

The following may be used for discovery, adjudication and manual evidence under their permitted/public research interfaces:
- NFDC / National Film Archive of India;
- Film Heritage Foundation;
- official government/institutional catalogues;
- festival and archive catalogues;
- scholarly catalogues and historical records;
- other national/regional archival institutions added to Source Registry.

Reference use does not imply permission for bulk copying.

# No unauthorized archive scraping

V1 will not:
- bypass CAPTCHAs;
- crawl archive sites against terms/technical restrictions;
- copy protected catalogue descriptions into CAS;
- mirror archive images/film scans without rights;
- treat a public search page as a bulk API.

# Coverage method

Historical coverage is built deliberately through benchmark cohorts:
- pre-1931 Indian cinema;
- early talkies;
- 1930s-1950s major regional cinemas;
- 1960s-1970s Telugu/Tamil/Malayalam/Kannada/Hindi/Bengali/Marathi and other language cohorts;
- lost/fragmentary films;
- alternate/disputed dates;
- incomplete credits;
- restored/reconstructed works;
- early film-industry organizations and people.

# Missing-data semantics

Historical records must distinguish:
- `UNKNOWN_TO_CAS` — we have not yet sourced it;
- `UNKNOWN_HISTORICALLY` — competent sources indicate uncertainty/absence;
- `DISPUTED` — credible sources conflict;
- `NOT_APPLICABLE`;
- `KNOWN_LOST` / `PARTIALLY_SURVIVING` where archival evidence supports it.

CAS Coverage must not punish an archival title as though historically unknowable data were merely an ingestion bug.

# Collaboration path

Partnership/collaboration with NFAI/NFDC, Film Heritage Foundation, regional archives or scholarly projects remains desirable.

A future partnership may add a scalable adapter only when:
- access is explicitly permitted;
- field/reuse rights are documented;
- provenance survives ingestion;
- archive IDs remain external mappings;
- media rights are separately handled.

# V1 freeze consequence

A bulk Indian historical archive feed is **not a prerequisite** for starting V1 implementation.

What is required before public launch is:
- historical benchmark coverage meets the locked quota/SLA;
- priority Indian eras/languages have measured coverage;
- no historical facts are fabricated to fill gaps;
- reference evidence is traceable.

This resolves the source-architecture question while keeping historical-depth quality as a measurable QA obligation.