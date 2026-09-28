# Artwork Foundation P2 — Coverage Audit Preparation

**Status:** WORKING — READ-ONLY PREP; DO NOT ACTIVATE P2 PRODUCTION BEFORE P1 EXIT  
**Date:** 2026-09-28  
**Parent:** `ARTWORK_FOUNDATION_P2_PREP.md`  
**Selector/rights contract:** `ARTWORK_FOUNDATION_P2_SCHEMA_SELECTOR_REVIEW.md`

## Purpose

Define the read-only coverage audit required before any broad P2 artwork population.

The audit answers a different question from catalogue completeness:

> Of the exact Movie and Series identities considered, how much artwork evidence exists, how much is publication-eligible under the locked rights rules for a declared territory and evaluation time, where are the gaps, and how concentrated or ambiguous are the sources?

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
- reports metrics only from supplied evidence;
- rejects malformed canonical vocabulary rather than silently reclassifying it;
- requires positive normalized safety evidence before any candidate may count as publication-eligible;
- binds results to an explicit audit territory and UTC evaluation timestamp;
- emits a deterministic SHA-256 attestation of the exact normalized input snapshot.

---

## Snapshot contract

The current required snapshot contract is:

```json
{
  "snapshot_version": "p2-artwork-coverage-snapshot-v1",
  "audit_context": {
    "territory": "IN",
    "evaluated_at": "2026-09-28T00:00:00Z"
  },
  "titles": [],
  "candidates": []
}
```

### Snapshot version

`snapshot_version` must be exactly `p2-artwork-coverage-snapshot-v1`.

The audit rejects absent or unknown versions. Future incompatible snapshot shapes must receive a new explicit contract version rather than being interpreted implicitly.

### Audit context

`audit_context` is required because publication eligibility is context-dependent.

- `territory` must be an uppercase two-letter territory code, for example `IN`;
- `evaluated_at` must be an explicit UTC RFC3339 timestamp in `YYYY-MM-DDTHH:MM:SSZ` form;
- normalized `territory_eligible`, `validity_eligible`, and `takedown_clear` facts are interpreted only for this declared context;
- a different territory or evaluation time is a different audit input and therefore a different attestation.

An audit report without explicit territory/time context is not acceptable evidence for P2 population planning.

### Input attestation

The report records:

```json
{
  "input_attestation": {
    "algorithm": "sha256-canonical-json-v1",
    "sha256": "..."
  }
}
```

Canonicalization is UTF-8 JSON with sorted object keys, compact separators, preserved Unicode, and non-finite numeric values rejected. The SHA covers the **entire normalized snapshot**, including:

- snapshot version;
- audit context;
- all exact title identities;
- all candidates and supplied evidence.

Object key insertion order does not change the digest. Changing territory, evaluation time, title/candidate content, or evidence changes the digest. This attestation provides reproducible audit lineage; it is not a rights approval signature.

---

## Title record

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

---

## Candidate discovery record

Every candidate requires exact title linkage plus stable source evidence:

```json
{
  "media_type": "movie",
  "source_table": "movies",
  "source_id": "wd-Q123",
  "source_key": "wikimedia_commons",
  "source_asset_id": "File:Example.jpg",
  "presentation_role": "poster",
  "publication_state": "DISCOVERED",
  "rights_basis": "NO_RIGHTS_BASIS",
  "hosting_mode": "REFERENCE_ONLY"
}
```

A candidate must provide `source_asset_id` or `source_page_url`. Unknown source identity is not sufficient evidence for the audit.

The normalized vocabulary is closed:

- `presentation_role`: `poster`, `backdrop`
- `publication_state`: exactly the canonical P2 publication states
- `rights_basis`: exactly the canonical P2 rights bases
- `hosting_mode`: exactly the canonical P2 hosting modes

Malformed or unknown vocabulary fails the audit input rather than becoming an `unknown` bucket.

---

## Candidate seeking publication-eligible counting

A candidate may count as publication-eligible only when the snapshot provides explicit positive evidence in addition to a locked public state/basis/hosting combination:

```json
{
  "link_exact": true,
  "rights_verified_at": "2026-09-28T00:00:00Z",
  "validity_eligible": true,
  "takedown_clear": true,
  "territory_eligible": true,
  "delivery_url": "https://...",
  "attribution_required": false
}
```

Rules:

1. every candidate must link to an exact title identity present in `titles`;
2. unknown title references fail the audit;
3. `ambiguous_link=true` is measurable evidence but cannot count as publishable coverage;
4. `link_exact` must be explicitly `true`;
5. discovery/no-rights records may count as discovered candidates, never as publication-eligible coverage;
6. `rights_verified_at` must be present;
7. `validity_eligible`, `takedown_clear`, and `territory_eligible` must each be explicitly `true` for the declared audit context;
8. `EMBED_ONLY` and `REFERENCE_ONLY` never count as poster/backdrop publication;
9. publication-eligible image delivery requires a valid HTTPS `delivery_url`;
10. `attribution_required` must be an explicit boolean; when true, non-empty `attribution_text` is required;
11. state/rights-basis mismatches fail closed;
12. `expired=true` or `takedown=true` force non-public classification even when normalized positive flags are also supplied;
13. audit classification is not a production approval action.

Missing territory, validity, takedown, exact-link, rights-verification, delivery, or attribution evaluation must never inflate publication-ready coverage.

---

## Locked publication-counting pairs

| Publication state | Rights basis |
|---|---|
| `OPEN_LICENSE_VERIFIED` | `OPEN_LICENSE` |
| `PUBLIC_DOMAIN_VERIFIED` | `PUBLIC_DOMAIN` |
| `PROVIDER_LICENSED` | `PROVIDER_CONTRACT` |
| `RIGHTS_APPROVED` | `RIGHTSHOLDER_PERMISSION` |
| `PROMOTIONAL_PERMISSION_VERIFIED` | `PROMOTIONAL_PERMISSION` |

These pairs are necessary but not sufficient: all contextual and fail-closed evidence checks above must also pass.

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
- provider/source concentration;
- publishability rejection-reason counts such as missing verification, unverified territory, unsafe hosting, invalid delivery URL, or missing attribution.

Every report must also echo its `snapshot_version`, `audit_context`, and input attestation so coverage numbers cannot be separated from the conditions under which they were evaluated.

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
3. declare audit territory and evaluation timestamp;
4. run discovery/rights adapters in non-mutating mode;
5. normalize evidence into the versioned snapshot contract, including explicit safety-evaluation fields for any candidate proposed as publication-eligible;
6. run `p2_artwork_coverage_audit.py` and preserve the report plus input SHA-256;
7. review coverage, ambiguity, rights yield, fallback, rejection reasons and concentration;
8. sample high-risk source/rights buckets manually where required;
9. only then design a bounded/resumable P2 population mutation plan.

The audit report is evidence for deciding how to populate P2; it is not itself an ingestion artifact.

---

## Exit from audit-prep state

This prep is sufficient when:

- offline audit utility tests pass;
- exact title identity is required;
- snapshot version and audit context are explicit;
- report/input lineage is deterministically attested;
- malformed candidate vocabulary is rejected;
- discovered vs publication-eligible coverage are separated;
- missing safety facts fail closed rather than being inferred;
- Movie/Series and language breakdowns are available;
- ambiguity, no-rights, duplicates, rejection reasons and provider concentration are measurable;
- no network/D1/mutation path is introduced;
- P1 remains the active production phase.

No P2 production phase is activated by satisfying this preparation document.
