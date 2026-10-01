# Cinema & Series — P3 ↔ P4 Onboarding Merge Handoff

**Status:** LOCKED PRE-IMPLEMENTATION OVERLAY — DO NOT IMPLEMENT BEFORE P3/P4 AUTHORIZATION  
**Date:** 2026-10-01  
**Parents:** `IDENTITY_AND_PROFILES_P3_PREP.md`, `FIRST_TIME_ONBOARDING_P4_PREP.md`

## Purpose

Resolve the remaining ambiguity when a device-local onboarding profile is upgraded into a Google-backed Cinema & Series profile, especially when the Google account already has its own onboarding progress.

This document is a contract overlay only. It creates no migration, endpoint, UI, D1 write path, or production behavior while P1/P2/P3 phase gates remain active.

Where the parent P3/P4 prep documents say conflicts must be resolved deterministically, this document defines that resolution contract.

---

## 1. Core ownership rules

1. P3 owns identity verification, session creation, account/profile ownership, merge idempotency, and server persistence.
2. P4 owns onboarding field validation, dependency revalidation, completion eligibility, and the user-facing conflict-resolution experience.
3. The Google identity object is never the onboarding profile itself; all cloud onboarding state belongs to the Cinema & Series `profile_id`.
4. Local state is untrusted client input. It may represent user intent, but it does not become server truth until validated and persisted.
5. Client timestamps are not trusted to overwrite cloud state merely because they are later.
6. No merge may write canonical catalogue, recommendation, artwork, genre, person, or title metadata.

---

## 2. Merge envelope and idempotency

A local-to-account upgrade submits a versioned merge envelope containing at minimum:

- `merge_id` — random client-generated idempotency identifier;
- `local_profile_id`;
- local onboarding schema version;
- local onboarding top-level state;
- validated-shape explicit preference fields;
- selected seed title IDs;
- local saves/interactions included by the P3 merge contract;
- optional client timestamps as informational metadata only.

Server rules:

1. `merge_id` is unique per account/profile merge attempt.
2. Replaying the same `merge_id` with the same canonical payload returns the same merge result.
3. Reusing a consumed `merge_id` with a materially different payload fails closed.
4. The server validates every title reference and every P4 field before accepting it.
5. A merge receipt records result state: `resolved`, `needs_resolution`, or `rejected`.
6. Network retry must never duplicate seeds, saves, watched state, or other set-like interactions.

---

## 3. Top-level onboarding-state precedence

### Cloud `complete`

A completed cloud profile remains complete.

- local onboarding progress does not reopen first-time onboarding;
- local explicit onboarding preferences do not silently replace completed cloud preferences;
- compatible non-onboarding set-like state such as saves/watched may still merge under P3 rules;
- conflicting local onboarding choices may be offered later as normal preference edits, not as a first-time merge overwrite.

### Cloud `not_started`, local `in_progress` or `complete`

After full validation, the local onboarding state may become the account profile onboarding state.

If the local payload claims `complete`, P4 completion validation must be rerun server-side; the client claim alone cannot set cloud state to complete.

### Cloud `in_progress`, local `not_started`

Keep cloud onboarding progress. Do not erase it with the empty/newer local profile.

### Both `not_started`

Result remains `not_started`.

### Both `in_progress`

Use the field-level rules below. The resulting onboarding state is recomputed from validated merged fields; it is not chosen by comparing `current_step` values.

### Local `complete`, cloud `in_progress`

Do not automatically prefer the local `complete` flag. Merge the explicit fields under the field-level rules, rerun server-side P4 validation, and require any conflicts to resolve before cloud completion can be written.

---

## 4. Field-level merge rules

### 4.1 Scalar explicit preferences

Examples:

- `content_scope`
- mainstream/hidden-gem bias
- classic/newer bias
- `region_scope`
- `surprise_level`

Rules:

1. only cloud has a valid value → keep cloud;
2. only local has a valid value → adopt local;
3. both have the same normalized value → keep that value;
4. both have different valid values → create an explicit conflict; do not choose by client timestamp;
5. cloud value is invalid under the current schema but local is valid → reject/repair through version migration rules rather than silently trusting local;
6. no conflicting scalar may be hidden from the user and no arbitrary last-write-wins rule is allowed.

For a conflict, the merge result carries both choices and P4 presents a concise resolution control. Cloud may be the visual default, but the merge is not `resolved` until the user chooses.

### 4.2 Multi-select explicit preferences

Examples:

- languages
- genres/moods

These are preference sets, not generic interaction sets.

Rules:

1. one side absent → use the present valid set;
2. normalized sets equal → keep once;
3. materially different sets → treat as an explicit preference conflict rather than blindly unioning;
4. P4 may present a combined selection as an editing convenience, but it must be user-confirmed before the conflict is considered resolved;
5. invalid/deprecated keys are removed only through explicit schema-migration/validation logic and reported to the merge result.

### 4.3 Seed titles

Seed titles are safe to union only after validation.

- normalize to exact canonical eligible title identities;
- deduplicate exact identities;
- discard/reject reviewed-excluded or unknown identities under explicit validation rules;
- revalidate against the merged `content_scope` and other P4 eligibility constraints;
- if an upstream conflict means eligibility cannot yet be determined, keep the seed as pending rather than silently deleting it;
- after conflict resolution, recompute distinct eligible seed count and enforce the final P4 minimum.

A unioned seed set does not by itself complete onboarding.

### 4.4 Saves / watched / explicit interactions

These follow P3 interaction semantics rather than P4 preference conflict semantics.

- idempotent set-like saves/watched may union;
- duplicate actions collapse by their natural identity key;
- `not_for_me` is sticky and is not cancelled merely because the other side contains a save;
- contradictory interaction types that cannot coexist must use an explicit product interaction policy, not onboarding merge precedence.

---

## 5. Dependency revalidation after merge

After field resolution, P4 recomputes validity from values rather than trusting either client's `completed_steps` or `current_step`.

At minimum revalidate:

- content scope versus selected Movie/Series seeds;
- required language rule;
- genre/mood rule;
- region and bias allowed values/ranges;
- surprise-level range;
- seed identity eligibility and distinct minimum;
- current schema version.

`completed_steps` is derived/rebuilt from validated state. A client cannot make a step complete by merely listing its key.

The resume point is the first required incomplete/invalid unit after this recomputation.

---

## 6. Conflict lifecycle

A merge with unresolved explicit-preference conflicts returns `needs_resolution`.

Requirements:

1. server persists enough merge/conflict state to make resolution retry-safe;
2. the account session can exist while resolution is pending;
3. onboarding may resume at a dedicated conflict-resolution step before the normal first incomplete step;
4. `complete` cannot be written while required conflicts remain unresolved;
5. resolving conflicts is an authenticated profile mutation;
6. replaying a resolution request is idempotent;
7. a new merge attempt cannot silently overwrite an unresolved older merge without explicit cancellation/replacement semantics.

---

## 7. When local state may be deleted

The client must not clear the local profile merely because Google authentication succeeded.

Local onboarding/profile state may be deleted only after the server returns a durable merge result of `resolved` and the client has received that acknowledgement.

If the merge returns `needs_resolution`, preserve local state until resolution is durably acknowledged, unless the server has explicitly persisted the entire needed local conflict payload under a tested recovery contract. V1 defaults to preserving local state.

If the request fails, times out, or returns `rejected`, keep local state.

This protects against auth-success / merge-failure data loss.

---

## 8. Reset ownership

“Reset onboarding” is not account deletion, logout, or local-profile deletion.

For a signed-in profile, an explicit onboarding reset may clear only onboarding/taste-capture fields owned by P4 according to the then-current product contract. It must not silently delete:

- the user account;
- provider identity binding;
- sessions (unless separately requested);
- saves/watched history;
- canonical catalogue data.

For local mode, a full “Delete local profile” remains the stronger P3 operation and clears the local profile as already specified.

If future product design wants reset to clear interactions too, that must be a separate explicit decision and confirmation surface.

---

## 9. Required implementation tests

When P3/P4 implementation is authorized, tests must cover at least:

1. cloud complete + local in-progress never reopens onboarding;
2. cloud not-started + valid local in-progress adopts local progress;
3. cloud in-progress + local not-started preserves cloud;
4. conflicting scalar preferences produce `needs_resolution`;
5. conflicting multi-select preferences are not silently unioned as final truth;
6. compatible seeds union, deduplicate and revalidate;
7. content-scope conflict cannot leave contradictory seeds marked valid;
8. local `complete` cannot bypass server completion validation;
9. client timestamps cannot silently defeat cloud conflict handling;
10. same `merge_id` + same payload is idempotent;
11. same `merge_id` + different payload fails closed;
12. network retry cannot duplicate interactions/seeds;
13. unresolved conflict blocks onboarding completion;
14. local state survives auth success followed by merge failure;
15. local state is cleared only after durable resolved acknowledgement;
16. onboarding reset does not delete account/session/saves by accident;
17. merge does not write canonical catalogue/recommendation/artwork metadata.

---

## 10. Activation boundary

This overlay closes a preparation ambiguity only.

Do not implement its schema/API/UI while the active roadmap gates prohibit P3/P4 implementation. Migration numbering remains unresolved until the earlier phases exit and `main` is revalidated.
