# P1 V3 Physical Shard 3 — Offline Preflight

**Status:** READ-ONLY PREFLIGHT COMPLETE  
**Prepared:** 2026-09-23  
**Production mutation:** **false**  
**Authoritative live status:** `RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md`

## Purpose

Pre-rehearse the next P1 production operation from the immutable reviewed V3 artifact without Cloudflare credentials, D1 access, quota reservation or workflow dispatch.

This is **not** permission to run a second mutation on 2026-09-23 UTC. The Sep23 quota day is already consumed by physical shard 2. The live controller must still re-run every production safety check on a later fresh UTC quota day.

## Immutable evidence source

- analysis workflow run: **`35428784454`**
- analysis commit: **`8fdbfeedb28e7e8624fac1a7156f953f21adb618`**
- artifact: `recommendation-metadata-materialization-v3-repartitioned`
- artifact ID: **`10579264534`**
- GitHub artifact digest: **`sha256:059b989bd4e8dae069039f74c7415ddaa3070c9217ac8b6e428b9992f6545bc5`**
- artifact-attestation SHA-256: **`8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986`**
- projection SHA-256: **`f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6`**
- normalized graph SHA-256: **`9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78`**
- reviewed parent partitions reused rather than rewritten: **`[0, 8]`**

## Exact reviewed shard 3 shape

From the immutable attestation, materialization summary and executable cost manifest:

- physical shard: **3**
- recommendation titles: **1,056**
- genre upserts: **192**
- people upserts: **4,877**
- title-genre relationships: **1,041**
- title-credit relationships: **5,384**
- data statements: **12,550**
- reviewed estimated D1 rows written: **49,159**
- conservative P1 ceiling: **80,000**
- conservative P1 headroom: **30,841**
- free daily rows-written limit used by the reviewed cost model: **100,000**
- free daily headroom: **50,841**

Fingerprints:

- shard materialization SHA-256: **`441b5038e6bece81b997c885d2248a9e855381360b80a5c928a7c80f2d20fb54`**
- reviewed SQL SHA-256: **`6228f2a51ade3bf37fbdea04f1fb15ad29f5457b5c90e2fc9ee8aa19e8b0a357`**
- executable SQL SHA-256: **`c0aa44243de94f3d37c89ef854da68ff415c4253781e7f739bf001e5e4589c39`**
- cost-manifest SHA-256: **`c7b2ea077c374ffa6581ad8f3b269a0e9d0442bb659e3570b865d727ebc4bccc`**
- report SHA-256: **`0a30e372947b6da67e77dad8fa4aa0082c1fa713eee39bf6b43b457cc4488a37`**

The executable bytes independently hash to the attested executable SHA above.

## Expected next-day controller transition

On the next fresh UTC quota day, assuming production remains unchanged, the permanent controller should classify the ordered prefix as:

- `topup` = `complete`
- `1` = `complete`
- `2` = `complete`
- `3` = `not_started`

It should then:

1. verify immutable V3 attestation and graph/projection fingerprints,
2. confirm reviewed source cleanup remains exact,
3. recapture the live corrected projection,
4. confirm no UTC guard already exists for the new day,
5. classify shard 3 exactly `not_started`,
6. read **49,159** from the immutable attestation,
7. reject the operation if the cost is no longer within the locked ceiling,
8. reserve one UTC guard with token `<controller-run-id>:3`,
9. dispatch exactly one graph-attested V3 writer for operation `3`.

The writer must independently repeat provenance, artifact, projection, executable, guard-ownership and pre-state checks before mutation.

## New reusable offline preflight

`scripts/p1_v3_operation_preflight.py` validates a reviewed operation directly from a restored immutable artifact. It performs no network or D1 operation.

Example after restoring the reviewed artifact to `data/generated/reviewed-v3`:

```bash
python scripts/p1_v3_operation_preflight.py \
  --artifact-dir data/generated/reviewed-v3 \
  --operation 3 \
  --json-out data/generated/p1-v3-shard3-preflight.json
```

The utility fails closed on:

- wrong attestation SHA,
- wrong projection or graph SHA,
- changed parent-partition plan,
- unauthorized operation,
- missing physical shard attestation,
- executable byte drift,
- cost-manifest drift,
- relationship/title count mismatch,
- cost above the 80,000-row P1 ceiling,
- cost above the reviewed 100,000 free daily limit.

## What this preflight does not prove

Offline evidence cannot prove tomorrow's live production state. It does not replace:

- the fresh UTC guard check,
- live source-cleanup verification,
- live corrected projection recapture,
- live shard-state classification,
- exact guard ownership,
- post-write state verification,
- post-write orphan/provenance checks.

Those remain mandatory in the permanent controller/writer.

## Result

**SHARD 3 OFFLINE PREFLIGHT: PASS**

Reviewed immutable inputs are internally consistent, the selected executable is fingerprint-exact, the expected slice is **1,056 / 1,041 / 5,384**, and the reviewed write estimate **49,159** remains safely below both the P1 conservative ceiling and the free daily rows-written allowance.
