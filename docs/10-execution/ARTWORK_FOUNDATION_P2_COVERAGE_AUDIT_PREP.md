# Artwork Foundation P2 — Coverage Audit Preparation

**Status:** WORKING — READ-ONLY PREP; DO NOT ACTIVATE P2 PRODUCTION BEFORE P1 EXIT  
**Date:** 2026-09-27  
**Parent:** `ARTWORK_FOUNDATION_P2_PREP.md`  
**Selector/rights contract:** `ARTWORK_FOUNDATION_P2_SCHEMA_SELECTOR_REVIEW.md`

## Purpose

Define the read-only coverage audit required before any broad P2 artwork population.

The audit answers a different question from catalogue completeness:

> Of the exact Movie and Series identities considered, how much artwork evidence exists, how much of it is actually publication-eligible under the locked rights rules, where are the gaps, and how concentrated or ambiguous are the sources?

This preparation authorizes **no migration, no D1 write, no artwork ingestion, no rights approval, and no public artwork publication**.

---

## Offline utility

`scripts/p2_artwork_coverage_audit.py`

The utility is deliberately offline. It:

- reads one normalized JSON snapshot;
- performs no HTTP requests;
- opens no Cloudflare/D1 connection;
- emits no SQL;
- changes no rights state;
- cannot approve a candidate;
- reports metrics only from supplied evidence.

This allows the audit/reporting contract to be tested while P1 remains active without starting P2 production implementation.

---

## Snapshot contract

Top-level object:

```json
{
  "titles": [],
  "candidates": []
}
```

### Title record

Minimum fields:

```json
{
  "media_type": "movie",
  "source_table": "movies",
  "source_id": "wd-Q123",
  "language": "Telugu"
}
```

Rules:

- `media_type` is exactly `movie` or `series`;
- `(media_type, source_table, source_id)` is the exact audit identity;
- duplicate title identities are rejected;
- title text is not identity;
- language may be omitted/unknown, but it must not be guessed for the audit.

### Candidate record

Minimum identity linkage:

```json
{
  "media_type": "movie",
  "source_table": "movies",
  "source_id": "wd-Q123",
  "source_key": "wikimedia_commons",
  "source_asset_id": "File:Example.jpg",
  "presentation_role": "poster",
  "publication_state": "OPEN_LICENSE_VERIFIED",
  "rights_basis": "OPEN_LICENSE",
  "hosting_mode": "EXTERNAL_ALLOWED"
}
```

Optional audit evidence may include:

- `source_page_url`
- `delivery_url`
- `attribution_required`
- `attribution_text`
- `territory_restrictions`
- `territory_eligible`
- `ambiguous_link`
- `expired`
- `takedown`

Rules:

1. every candidate must link to an exact title identity present in `titles`;
2. unknown title references fail the audit;
3. `ambiguous_link=true` is measurable evidence but cannot count as publishable coverage;
4. a discovery record with unknown/no rights basis may count as a discovered candidate, never as publishable coverage;
5. `EMBED_ONLY` and `REFERENCE_ONLY` never count as poster/backdrop publication;
6. missing required attribution prevents publishable counting;
7. state/rights-basis mismatches fail closed;
8. audit classification is not a production approval action.

---

## Locked publication-counting pairs

The audit counts an image candidate as publication-eligible only for these exact state/basis pairs, subject to the remaining fail-closed checks:

| Publication state | Rights basis |
|---|---|
| `OPEN_LICENSE_VERIFIED` | `OPEN_LICENSE` |
| `PUBLIC_DOMAIN_VERIFIED` | `PUBLIC_DOMAIN` |
| `PROVIDER_LICENSED` | `PROVIDER_CONTRACT` |
| `RIGHTS_APPROVED` | `RIGHTSHOLDER_PERMISSION` |
| `PROMOTIONAL_PERMISSION_VERIFIED` | `PROMOTIONAL_PERMISSION` |

This is reporting logic only. The future production selector remains separately gated by P2.1 implementation and tests after P1 exit.

---

## Required audit metrics

The report must preserve at least:

### Catalogue denominator

- total exact identities;
- Movie identities;
- Series identities;
- identities by known language.

### Candidate/discovery coverage

- titles with at least one discovered candidate;
- candidate coverage rate;
- raw candidate count;
- candidate counts by source.

### Publication-eligible coverage

- titles with at least one publishable poster;
- titles with at least one publishable backdrop;
- titles with any publishable artwork;
- fallback-only titles;
- all corresponding rates;
- results by Movie/Series;
- results by language.

### Rights/source risk

- publication-eligible candidates by rights basis;
- publication-eligible candidates by source;
- assets requiring attribution;
- assets with explicit territory restrictions;
- rejected/no-rights-basis candidates;
- ambiguous-link candidates;
- duplicate candidate occurrences;
- provider/source concentration.

Artwork coverage must never be presented as core catalogue identity completeness.

---

## Duplicate metric

For audit-only exact duplicate detection:

1. prefer `(source_key, source_asset_id, presentation_role)` when `source_asset_id` exists;
2. otherwise use `(source_key, source_page_url, delivery_url, presentation_role)`.

This metric flags repeated candidate evidence. It does **not** merge rights records and does not authorize deduplication across different rights/licence states.

---

## Provider concentration

Report at minimum:

- largest candidate source + count/share;
- largest publication-eligible source + count/share.

High concentration is not automatically a blocker, but it must be visible before broad P2 population because provider/licence loss could materially reduce visual coverage.

---

## Read-only pre-production sequence after P1 exit

Before broad P2 writes:

1. freeze final P2.1 schema/selector implementation;
2. export exact Movie + Series audit identities from production using a read-only query;
3. run discovery/rights adapters in non-mutating mode;
4. normalize evidence into this snapshot contract;
5. run `p2_artwork_coverage_audit.py`;
6. review coverage, ambiguity, rights yield, fallback and concentration;
7. sample high-risk source/rights buckets manually where required;
8. only then design a bounded/resumable P2 population mutation plan.

The audit report is evidence for deciding how to populate P2; it is not itself an ingestion artifact.

---

## Exit from audit-prep state

This prep is sufficient when:

- offline audit utility tests pass;
- exact title identity is required;
- discovered vs publishable coverage are separated;
- Movie/Series and language breakdowns are available;
- ambiguity, no-rights, duplicates and provider concentration are measurable;
- no network/D1/mutation path is introduced;
- P1 remains the active production phase.

No P2 production phase is activated by satisfying this preparation document.
