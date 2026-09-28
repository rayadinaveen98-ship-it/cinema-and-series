# Artwork Foundation P2 — Audit Snapshot Builder Preparation

**Status:** WORKING — READ-ONLY PREP; DO NOT ACTIVATE P2 PRODUCTION BEFORE P1 EXIT  
**Date:** 2026-09-28  
**Audit contract:** `ARTWORK_FOUNDATION_P2_COVERAGE_AUDIT_PREP.md`

## Purpose

Define the deterministic boundary between future read-only production exports / non-mutating artwork adapters and the P2 coverage audit.

The builder does **not** discover artwork, query production, approve rights, mutate D1, emit SQL, or publish assets. It only assembles already-exported exact title identities and already-normalized candidate evidence into the locked versioned audit snapshot.

## Utility

`scripts/build_p2_artwork_audit_snapshot.py`

Inputs are deliberately separate so catalogue identity evidence cannot be silently inferred from candidate data.

### Titles input

Strict JSON object containing exactly one field:

```json
{
  "titles": [
    {
      "media_type": "movie",
      "source_table": "movies",
      "source_id": "wd-Q123",
      "language": "Telugu"
    }
  ]
}
```

The future production identity export must be read-only and must preserve the exact source table + source row ID. Title text is not an identity key.

### Candidates input

Strict JSON object containing exactly one field:

```json
{
  "candidates": [
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
  ]
}
```

Candidates must already obey the normalized P2 candidate vocabulary. The builder never upgrades discovery evidence into an approved rights state.

## Builder behavior

The builder:

1. validates every exact title identity;
2. rejects duplicate title identities;
3. rejects candidate links to identities absent from the title export;
4. validates candidate vocabulary/source evidence using the same audit contract;
5. preserves candidate duplicates exactly so the downstream duplicate-rate metric remains meaningful;
6. sorts title rows deterministically by exact identity;
7. sorts candidate rows deterministically by exact title identity, source candidate identity, and canonical JSON tie-break;
8. adds the locked snapshot contract version;
9. adds the declared territory and UTC evaluation timestamp;
10. validates the assembled snapshot through the offline audit contract before writing output.

The same logical inputs in different list/object ordering therefore produce the same normalized snapshot and audit SHA-256.

## CLI shape

Conceptually:

```text
python scripts/build_p2_artwork_audit_snapshot.py \
  --titles <read-only-title-export.json> \
  --candidates <normalized-candidate-evidence.json> \
  --territory IN \
  --evaluated-at 2026-09-28T00:00:00Z \
  --output <audit-snapshot.json>
```

The command is local/offline. It does not contain Cloudflare credentials or external source clients.

## Production export boundary after P1 exit

This prep does **not** implement a live D1 export workflow while P1 is active. After P1 formally exits, the first P2 audit execution should:

1. define and review a read-only query/export for the exact Movie + Series denominator;
2. save that export as the strict `titles` input;
3. run approved discovery and rights adapters in explicit non-mutating mode;
4. normalize their evidence as the strict `candidates` input;
5. build the deterministic snapshot;
6. run the coverage audit;
7. preserve both snapshot SHA-256 and report as review evidence;
8. only after review design any bounded P2 production mutation.

## Safety invariants

- no title-string reconciliation inside the builder;
- no candidate deduplication or rights-record merging;
- no inferred territory/validity/takedown decisions;
- no network calls;
- no D1 access;
- no SQL generation;
- no migration reservation;
- no rights approval;
- no artwork publication;
- P1 remains the active production phase.
