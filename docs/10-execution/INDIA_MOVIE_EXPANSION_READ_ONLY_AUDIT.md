# India Movie Expansion — Read-Only Discovery Gate

**Status:** IMPLEMENTED AUDIT / NO PRODUCTION IMPORT AUTHORIZED  
**Date:** 2026-10-16  
**Active roadmap:** `PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Product goal

Prioritize significantly broader Indian cinema coverage, including old, contemporary,
regional and smaller-industry productions. The proposed **+10,000**, **+25,000**
and **+50,000** figures are *targets*, not evidence of available unique titles.
Do not promise the last target until source and baseline measurements support it.

## What was added

- `scripts/audit_indian_movie_growth.py`: read-only category/page discovery
  and duplicate comparison against the production Movie tables.
- `tests/test_indian_movie_growth_audit.py`: deterministic offline tests.
- `.github/workflows/india-movie-growth-audit.yml`: safe production
  identity snapshot, bounded source scan, a Markdown summary and JSON evidence.

First default cohort: **2015–2026**, max **8,000 distinct article pages**.
The tool supports follow-up date cohorts back to **1913** and a configurable
candidate cap of **15,000 per audit**. The result is a *sampled candidate audit*,
not an exhaustive total for Indian cinema.

## Language discovery

Hindi, Telugu, Tamil, Malayalam, Kannada, Bengali, Marathi, Punjabi,
Gujarati, Odia, Assamese and Bhojpuri, plus Wikipedia's year-specific
`Indian films` category.

Category memberships are discovery evidence:
- Indian-films category = stronger Indian-origin lead;
- language category = weaker Indian-origin lead (films in a language
  may be made outside India);
- identity and year conflicts stay in review;
- movie type/country must be confirmed for an import.

## Unique-title counting

Deduplicate source articles by Wikipedia page ID and Wikidata QID.
Compare each candidate against all existing exact-day `movies` and
year-precision `catalogue_titles` using stable page ID/QID.
Title + year equality is **possible duplicate**, never a new record.

Each report separates:
1. already in production;
2. possibly existing title/year;
3. needs further year/identity review;
4. new Indian-category candidates;
5. new language-only candidates.

**New candidate is not a confirmed importable film.** A later guarded
import requires movie-type and India-origin verification, plus the usual
duplicate, title, year and provenance checks.

## Run / artifacts

Run `India Movie Growth — Read-Only Discovery Audit` on GitHub Actions.
It runs on this workflow's first main-branch push, or can be dispatched with
specific year cohorts. It creates a 30-day `india-movie-read-only-discovery`
artifact and a summarized report in the workflow job.

It executes only two **SELECT** queries against Cloudflare D1.
It performs no D1 migrations, inserts or updates.

## Simple artwork direction

For the consumer app, use a straightforward priority:
1. film's official poster/promotion image from the rights holder's
   own public source or authorized delivery;
2. suitable official channel thumbnail, where reuse is allowed;
3. suitably licensed Wikimedia Commons image;
4. attractive title-art fallback.

Capture image URL and source, verify the right movie, and check rendering.
Official publication is not automatically permission to republish, but
routine cases should not require an unnecessarily elaborate manual workflow.
Keep empty/broken imagery out of the UI.

## Next decision after first audit

Compare observed new candidate yield with missing Indian-language
coverage. Extend discovery by decade (1913–2026) and then validate
the highest-yield candidate groups before importing any production data.
