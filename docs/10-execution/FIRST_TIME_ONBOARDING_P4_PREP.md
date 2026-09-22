# Cinema & Series — First-Time Onboarding P4 Prep

**Status:** PREPARED / DO NOT IMPLEMENT BEFORE P3 EXIT  
**Prepared:** 2026-09-22  
**Phase:** P4 — First-Time Onboarding  
**Active roadmap:** `docs/10-execution/PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`  
**Identity dependency:** `docs/10-execution/IDENTITY_AND_PROFILES_P3_PREP.md`

## Purpose

Prepare the product, state-machine, persistence and validation contract for the first-time Cinema & Series onboarding flow without starting P4 UI, schema, API or recommendation implementation early.

The locked first-time journey remains:

1. premium welcome
2. Google or local identity choice
3. taste setup
4. title seed selection
5. preference summary
6. one-time welcome transition
7. personalized product entry

This document is preparation only. It does not authorize P4 implementation, reserve a migration number, create profile tables, add auth code, write production D1 data or start P5 recommendation scoring.

P4 implementation begins only after the required P1, P2 and P3 exit gates are satisfied.

---

## Locked boundaries

P4 owns the **first-time experience and explicit preference capture**.

P4 does not own:

- canonical movie/series metadata creation
- artwork ingestion or rights decisions
- identity-provider verification or session internals
- recommendation scoring
- inferred taste weights from catalogue metadata
- recommendation ranking or diversity logic
- notification delivery

Those remain owned by P1/P2/P3/P5/P9 respectively.

Onboarding must never fabricate metadata to make a screen look complete.

---

## Locked first-time experience

### 1. Premium welcome

Purpose:

- establish Cinema & Series identity
- communicate discovery + release-intelligence value
- give the user a clear single path into setup

Requirements:

- cinematic but fast
- responsive on web and Android wrapper
- reduced-motion alternative
- no mandatory autoplay audio
- no data write merely for viewing the welcome screen
- returning completed users must not be forced through it again

Primary action advances to identity choice.

### 2. Identity choice

Options:

- Continue with Google
- Continue locally

P4 renders the choice, but P3 owns the actual identity/session contract.

For local mode, the user must be told clearly that:

- the profile is device/browser-local
- it will not automatically sync across devices
- clearing site/app data may remove it
- it can later be upgraded to a Google-backed profile

Do not create a fake account for local mode.

### 3. Taste questionnaire

Capture explicit choices for:

- content scope: Movies / Series / Both
- languages
- genres / moods
- mainstream vs hidden gems
- classics vs newer titles
- India / international / both
- surprise level

Questions should use simple user-facing language. Internal normalized values remain implementation details.

### 4. Seed-title selection

The user chooses titles they already like.

Locked product intent is a **5–6 title minimum range**. The exact hard minimum is intentionally not changed by this prep document because the active roadmap uses both “5–6” and “at least 5–6” wording.

Before P4 implementation begins, the exact threshold must be resolved as one explicit constant within that locked range. The UI may encourage more than the minimum, but must not imply that a larger selection is mandatory unless the product decision is changed explicitly.

Seed selection must preferentially use titles with strong recommendation metadata and suitable artwork/fallback presentation.

### 5. Preference summary

Before completion, show a compact summary of the user’s explicit selections and allow edits.

The summary is not an AI-generated personality label and must not claim unsupported traits such as “you are an adventurous cinephile.”

### 6. Completion transition

After valid setup is persisted successfully:

- show the one-time “Welcome to Cinema & Series” transition
- target duration: approximately 2–3 seconds
- reduced-motion version must be available
- do not replay on normal returning sessions

### 7. Product entry

After completion, route into the normal product shell.

P4 does not guarantee personalized recommendations are already rendered by itself. P5 owns the deterministic taste-profile builder and recommendation engine.

---

## Prepared onboarding state machine

Use one explicit versioned state machine rather than scattered booleans.

Prepared step keys:

- `welcome`
- `identity`
- `content_scope`
- `languages`
- `genres_moods`
- `discovery_bias`
- `era_bias`
- `region_scope`
- `surprise_level`
- `seed_titles`
- `summary`
- `completion_pending`
- `complete`

These are contract keys, not database columns.

### Top-level profile onboarding states

Remain aligned with P3:

- `not_started`
- `in_progress`
- `complete`

### Transition rules

1. New profile begins `not_started` at `welcome`.
2. Advancing past the first persisted preference changes state to `in_progress`.
3. A user may move backward and edit any prior explicit answer before completion.
4. Refresh/restart resumes at the first incomplete required step, not necessarily the last rendered screen.
5. `completion_pending` exists so persistence success and the one-time completion transition are not conflated.
6. `complete` may be set only after every required validation passes and the complete onboarding payload is durably stored for the selected identity mode.
7. The welcome animation itself must never be the source of truth for completion.

### Returning users

If onboarding state is `complete`:

- skip first-time onboarding
- route to the product
- expose preference editing later through Profile/Settings rather than replaying the first-time flow

If state is `in_progress`:

- resume safely
- preserve valid prior answers
- do not restart from zero unless the user explicitly resets the profile

---

## Versioned onboarding payload

Prepare one versioned explicit-preference envelope.

Conceptual shape:

```text
onboarding_schema_version
profile_identity
content_scope
languages[]
genres_or_moods[]
mainstream_hidden_gem_bias
classic_new_bias
region_scope
surprise_level
seed_title_ids[]
current_step
completed_steps[]
started_at
updated_at
completed_at
```

Implementation may normalize these fields across tables, but API/client behavior must preserve the logical contract.

Do not trust client-supplied title metadata, people, genres, artwork provenance or recommendation weights as canonical catalogue truth.

---

## Explicit preference semantics

### Content scope

Allowed values:

- `movies`
- `series`
- `both`

A single value is required.

### Languages

Requirements:

- support multiple selections
- use stable normalized language keys, not arbitrary free text
- India-first presentation should make major Indian languages easy to reach without excluding international languages
- preserve explicit ordering only if the product intentionally treats it as meaningful

Do not infer language preference from device locale alone.

### Genres / moods

P4 should present user-friendly genre/mood choices, but canonical genre IDs must map to real P1 metadata where a canonical genre relationship is claimed.

A mood can remain a product preference label if it is not represented as canonical title metadata.

Do not silently turn a mood label into a canonical genre.

### Mainstream vs hidden gems

Store as an explicit preference/bias, not as a claim that a title objectively belongs to one category unless such classification has its own evidence-backed contract.

### Classics vs newer

Store as a preference axis.

The exact era boundary used later by P5 must be deterministic and documented there; P4 only captures the user preference.

### Region scope

Allowed values prepared by P3:

- `india`
- `international`
- `both`

This is a discovery preference, not a statement of nationality or identity.

### Surprise level

Capture as a bounded user preference.

P5 decides how this maps to exploration outside the user’s strongest taste cluster.

P4 must not implement recommendation randomness itself.

---

## Seed-title candidate contract

Onboarding title choices are especially important because P5 will later derive metadata signals from them.

### Candidate eligibility

A title shown in the onboarding picker should satisfy all of the following at P4 implementation time:

1. valid canonical Movie or Series identity
2. not excluded by reviewed media-identity corrections
3. sufficient P1 recommendation metadata for useful taste extraction
4. title label suitable for user display
5. presentation-safe artwork according to the active P2 policy, or a premium fallback state
6. no unsafe/unsupported title merge

### Metadata readiness

Prefer titles with:

- at least one usable canonical genre
- at least one useful people signal appropriate to media type where available
- resolved language/industry context when supported by current product data

P4 must not create missing genre/cast/creator/director data merely to make a title eligible.

### Coverage and diversity

The seed picker should provide useful breadth across:

- Movies and Series according to selected scope
- selected languages
- India and international catalogues according to region scope
- mainstream and less obvious titles where data/artwork quality supports them
- older and newer eras

Do not hard-code a tiny static “popular movies” list as fake personalization.

### Search inside seed selection

Search may expose eligible catalogue titles beyond the initial suggestion set.

If a searched title is known to the catalogue but not recommendation-ready, the UI should not silently pretend it can contribute a full taste signal. Product behavior for such titles must be explicit before implementation: either exclude them from seed selection or allow them with clearly bounded signal contribution.

### Duplicate protection

Seed title IDs must be unique.

Movie/Series records that resolve to the same reviewed identity must not count twice.

---

## Persistence contract

### Local mode

Until upgraded to a signed-in profile, store the versioned onboarding state in the local-profile store defined by P3.

Requirements:

- durable across normal refresh/restart
- schema/version marker
- atomic or safely recoverable step updates
- no cloud-account claim
- reset/delete local profile clears onboarding state under the P3 deletion contract

### Signed-in mode

Persist explicit onboarding state against the authenticated Cinema & Series profile, not the Google identity object itself.

Requirements:

- server validates every mutation
- only authenticated profile may update its own state
- idempotent retries
- no update writes to canonical catalogue/recommendation metadata tables
- avoid write amplification from cosmetic screen navigation

### Local-to-Google upgrade during onboarding

If a local user signs in before onboarding completes:

- preserve valid local answers
- perform P3’s idempotent local-to-account merge
- continue from the resolved merged onboarding state
- do not force the user to repeat completed steps
- clear local state only after server acknowledgement under P3 rules

### Signed-in to local downgrade

Logging out does not automatically convert cloud profile state into a local profile.

If the product later supports “continue locally after logout,” that behavior must be specified separately rather than implicitly copying account data.

---

## Validation contract

P4 completion must fail closed if required data is invalid.

Validate at minimum:

1. recognized onboarding schema version
2. valid content scope
3. required language-selection rule satisfied
4. required genre/mood-selection rule satisfied
5. each scalar bias inside its allowed range
6. valid region scope
7. surprise level inside allowed range
8. seed-title minimum satisfied using distinct eligible title IDs
9. all submitted seed IDs resolve to allowed catalogue identities
10. no reviewed-excluded identities included
11. profile ownership/session valid for signed-in mode
12. local profile identifier valid for local mode

Client-side validation improves UX but is not the only validation for signed-in persistence.

---

## Progress and resume semantics

Progress percentage should be derived from required completion units, not hard-coded decorative numbers.

Recommended behavior:

- each step has a stable key
- required vs optional status is explicit
- completion is computed from validated state
- optional skips do not make the progress bar lie
- moving backward preserves later answers unless those answers become invalid because an upstream dependency changed

Example dependency:

If content scope changes from `both` to `movies`, selected Series seed titles may no longer satisfy the seed-selection contract. The UI must revalidate them rather than silently keeping contradictory state.

---

## Editing and dependency invalidation

Changing a prior answer may affect later state.

Prepared rules:

- language changes re-evaluate suggested seed-title candidates but do not automatically delete still-valid selected titles
- content-scope changes revalidate media-type-specific seed selections
- region changes re-rank suggestions but do not rewrite the user’s explicit seed choices by itself
- genre/mood changes affect suggestions, not canonical title metadata
- preference-axis changes never mutate title data

Any destructive removal of a user selection should be explicit and understandable.

---

## Failure and recovery states

The onboarding flow must handle:

- network loss during signed-in save
- expired/revoked session
- Google auth cancellation
- local storage unavailable/full
- stale client schema version
- title becoming ineligible between selection and completion
- duplicate submission/retry
- completion request succeeding while client acknowledgement is interrupted

Rules:

1. Never mark `complete` solely on the client before durable persistence succeeds.
2. Retry-safe requests must not duplicate preferences or seed selections.
3. If completion succeeded server-side but the response is lost, reload must discover `complete` rather than restarting onboarding.
4. Authentication failure returns to a recoverable identity/session state without erasing local unsaved choices unnecessarily.
5. Unsupported/stale payload versions fail with an explicit upgrade/recovery path.

---

## One-time completion transition semantics

The 2–3 second welcome transition is presentation state, not profile truth.

Prepared behavior:

- durable onboarding completion is written first
- client records/derives whether the transition needs to display for this completion event
- interruption during animation does not revert onboarding
- returning completed users do not see it repeatedly
- reduced-motion users get a short non-motion equivalent

Avoid a permanent D1 write merely to track every animation playback if the same semantic can be handled safely by completion state/client acknowledgement.

---

## Accessibility and interaction requirements

P4 implementation must include:

- complete keyboard navigation on web
- visible focus states
- semantic form controls
- screen-reader labels and error messages
- sufficient contrast
- reduced-motion support
- no information communicated only by color
- touch targets appropriate for mobile/Android wrapper
- no forced time limits
- validation errors attached to the relevant control and summarized when needed

Cinematic presentation must not reduce usability.

---

## Performance contract

First-time setup should feel premium without becoming heavy.

Implementation should:

- lazy-load nonessential visual assets
- keep initial welcome/identity path responsive on ordinary mobile connections
- prefetch only bounded candidate data
- paginate/search title candidates rather than shipping the catalogue to the client
- use appropriately sized artwork derivatives when P2 exposes them
- avoid blocking setup on nonessential analytics or animation assets

---

## Privacy boundaries

Do not derive or request sensitive personal characteristics for onboarding.

P4 V1 does not need:

- age
- gender
- religion
- political views
- exact location
- contacts
- device fingerprint

Recommendation-relevant onboarding data is limited to explicit cinema/series taste choices and selected titles.

Google email/name/avatar are identity/presentation fields under P3, not recommendation signals.

---

## Analytics preparation

If product analytics are later added, event names may be prepared around anonymous/product events such as:

- onboarding_started
- onboarding_step_completed
- seed_title_selected
- onboarding_resumed
- onboarding_completed

But analytics are not required for P4 V1 and must not block onboarding.

Do not log raw session secrets, Google credentials or unnecessary PII.

---

## P4 ↔ P5 handoff

P4 produces **validated explicit preference state**.

P5 consumes that state and builds the deterministic taste profile.

P4 hands P5:

- content scope
- explicit language choices
- explicit genre/mood choices that have valid mappings
- mainstream/hidden-gem preference
- classic/newer preference
- region preference
- surprise level
- selected canonical title IDs

P5, not P4, derives weighted signals from:

- genre
- director/creator
- cast
- language
- country/industry
- release era

No derived P5 weights should be accepted blindly from the onboarding client.

---

## Prepared API semantics

Exact paths are deferred, but implementation behavior should support:

- read current onboarding state
- save validated partial progress
- query/search eligible seed-title candidates
- complete onboarding atomically/idempotently
- reset onboarding only through an explicit user action

Potential logical operations:

- `GET onboarding state`
- `PATCH onboarding progress`
- `GET onboarding title candidates`
- `POST onboarding completion`

Local mode may implement equivalent behavior client-side until account upgrade.

This document does not authorize API implementation before P4 starts.

---

## Security gates for future implementation

P4 is not complete until tests prove:

1. one user cannot read or mutate another profile’s onboarding state
2. local mode does not create a cloud account silently
3. signed-in mutation requires valid P3 session
4. malformed preference values are rejected
5. unsupported seed title IDs are rejected
6. reviewed-excluded identities cannot enter seeds
7. duplicate seed IDs do not inflate the minimum
8. completion is idempotent
9. interrupted completion resumes correctly
10. local-to-account upgrade preserves onboarding progress
11. completion cannot mutate canonical catalogue metadata
12. returning completed users skip first-time onboarding
13. reduced-motion path works without losing required information

---

## Implementation order once P4 is authorized

1. re-read active roadmap and P1/P2/P3 exit evidence
2. resolve the exact seed-title minimum within the locked 5–6 range
3. freeze onboarding schema version and required/optional step definitions
4. finalize persistence/API shape against implemented P3 schema
5. build eligible seed-title read model against completed P1/P2 foundations
6. implement onboarding state/resume logic
7. implement Welcome + Identity presentation surfaces against P3
8. implement taste questionnaire
9. implement title search/suggestion/selection
10. implement preference summary/edit flow
11. implement idempotent completion
12. implement one-time transition + reduced-motion fallback
13. add validation/security/resume/accessibility tests
14. hand validated explicit state to P5

Do not begin with animation polish before state and recovery semantics work.

---

## P4 exit gate

P4 is complete only when:

- first-time users can choose Google or true local mode through the implemented P3 contract
- every required taste answer is validated and persisted
- the resolved title-seed minimum is enforced using distinct eligible canonical identities
- setup survives refresh/restart and resumes correctly
- local-to-Google upgrade preserves progress
- preference summary/editing works
- completion is durable and retry-safe
- completed returning users do not replay onboarding
- the one-time welcome transition and reduced-motion alternative behave correctly
- validated explicit preference state is stable enough for P5
- no P1/P2 canonical catalogue/artwork provenance contract is bypassed

---

## Explicitly deferred

Not part of P4 V1:

- recommendation scoring/ranking
- collaborative filtering
- black-box ML taste inference
- social onboarding
- importing streaming-service watch history
- contact/friend discovery
- household/multiple profiles
- age/child-profile setup
- notification permission prompts
- public profile creation
- mandatory analytics consent flow beyond what applicable product/privacy requirements later demand

---

## Sequencing lock

This document is **PREPARED ONLY**.

It does not change the active implementation order.

Current production priority remains **P1 Recommendation Metadata Foundation** until its exact 16,380-title graph, provenance/referential checks, Catalogue Quality S0/S1 gate and final evidence are complete.

P2 production follows P1. P3 implementation follows the required prior phase exits. P4 implementation follows P3.

No Welcome/Login/Taste UI, onboarding API, onboarding migration or production preference write is authorized by this document.
