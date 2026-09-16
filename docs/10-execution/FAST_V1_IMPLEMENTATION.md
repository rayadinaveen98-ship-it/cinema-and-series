# Fast V1 Implementation — ACTIVE

**Date:** 2026-09-16  
**Status:** IMPLEMENTATION AUTHORIZED

## Product contract

Fast V1 is intentionally constrained to three user-facing promises:

1. movie names;
2. release dates;
3. a premium, fast cinematic interface.

The extensive research already present in this repository is preserved for future platform expansion but does not block Fast V1 implementation.

## Runtime architecture

```text
Scheduled GitHub Action
  -> targeted Wikidata acquisition
  -> deterministic candidate JSON/SQL
  -> Cloudflare D1 (after account binding)
  -> Cloudflare Worker /api/movies
  -> React + Vite premium SPA on Cloudflare Workers static assets
```

Wikidata is an acquisition source, not a live page-request dependency.

## Stack

- React 19 + TypeScript
- Vite
- Tailwind CSS
- Cloudflare Vite plugin
- Cloudflare Workers
- Cloudflare D1
- GitHub Actions + Python for scheduled acquisition
- Wikidata CC0 for discovery/base release candidates
- official first-party evidence for verification upgrades

## Release-date states

- `verified`: explicit official first-party release-date evidence
- `supported`: corroborated by suitable independent/authority evidence
- `unconfirmed`: currently only an open-data candidate or otherwise insufficiently verified

## Guardrails

- no TMDB runtime or ingestion dependency;
- no public WDQS request from the user-facing application;
- no CBFC CAPTCHA bypass;
- no arbitrary web-search result promoted to verified fact;
- no poster/still dependency until a rights-safe asset path is approved;
- UI must still look premium without copyrighted artwork.

## Deployment prerequisite

Cloudflare credentials are not required to build or validate the application locally/CI. They are required only to create/bind the production D1 database and deploy the Worker.
