# Cinema & Series — Identity & Profiles P3 Prep

**Status:** PREPARED / DO NOT IMPLEMENT BEFORE P2 EXIT  
**Prepared:** 2026-09-21  
**Phase:** P3 — Identity & Profiles  
**Active roadmap:** `docs/10-execution/PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`

## Purpose

Prepare the implementation contract for Cinema & Series identity, profile persistence and session handling without starting P3 production schema/UI work early.

P3 exists to support the locked first-time journey:

1. Continue with Google
2. Continue locally
3. build taste preferences
4. allow a local profile to be upgraded to a signed-in account later
5. preserve the user’s saved/taste state through that upgrade

This document is architecture and contract preparation only. No P3 migration number is reserved here and no P3 production mutation should happen before P1/P2 exit gates are satisfied.

---

## Locked principles

1. **Local-first is a real mode, not a fake login.** A user may use Cinema & Series without creating an online account.
2. **Google is an identity provider, not the canonical user ID.** Google `sub` is stored as provider identity; Cinema & Series issues its own internal profile/user IDs.
3. **No email address is used as the stable provider key.** For Google, verified `sub` is the unique provider identifier.
4. **Local-to-account upgrade must preserve user state.** Saved titles, watched/not-for-me interactions, onboarding choices and taste data must not disappear when the user signs in.
5. **Sessions are server-controlled.** Do not keep a long-lived Google ID token in browser storage as the Cinema & Series session.
6. **No passwords in V1.** Google + local mode only.
7. **Minimize PII.** Store only what the product needs. Email/display name/avatar from Google are optional presentation/account-management fields, not recommendation signals.
8. **Identity never creates canonical movie metadata.** Profile/taste state is separate from catalogue truth.
9. **Web and Android wrapper share the same account/session API contract.** Native Android later reuses the same logical identity model.
10. **Deletion and logout semantics must be explicit and testable.**

---

## Current-platform fit

Preferred implementation remains inside the existing stack:

- Cloudflare Worker for auth/session endpoints
- D1 for signed-in account/profile/session state
- browser/device local storage for true local-only profile state
- Google Identity Services for Google sign-in
- no additional auth SaaS required for V1

This keeps the product within the current free-first architecture and avoids introducing a second system of record.

---

## Identity model

### Canonical internal IDs

Use opaque application-owned IDs:

- `user_id` — signed-in account identity
- `profile_id` — recommendation/profile identity
- `session_id` — server session identity
- `local_profile_id` — device/browser-scoped local identity, generated client-side

Recommended shape: random UUID/128-bit opaque identifiers. Never derive IDs from email, Google `sub`, title choices or device fingerprinting.

### Provider identity

Signed-in Google account maps through a separate provider identity row:

- provider = `google`
- provider_subject = verified Google `sub`
- user_id = internal Cinema & Series user

Unique constraint should be on `(provider, provider_subject)`.

Google `sub` must only be accepted after server-side token verification.

---

## Proposed logical schema

Names below are contract names only. Final migration numbering is assigned only when P3 starts.

### `users`

Purpose: canonical signed-in account.

Suggested fields:

- `id TEXT PRIMARY KEY`
- `status TEXT NOT NULL` — `active | deleted`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`
- `last_seen_at TEXT`
- `deleted_at TEXT`

Do not put recommendation/taste columns directly on `users`.

### `user_identities`

Purpose: external identity-provider binding.

Suggested fields:

- `id TEXT PRIMARY KEY`
- `user_id TEXT NOT NULL`
- `provider TEXT NOT NULL`
- `provider_subject TEXT NOT NULL`
- `email TEXT`
- `email_verified INTEGER`
- `display_name TEXT`
- `avatar_url TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Constraints:

- unique `(provider, provider_subject)`
- FK `user_id -> users.id`

Provider presentation fields are mutable cache fields. They do not identify the user.

### `profiles`

Purpose: one recommendation/profile identity per user for V1, while leaving room for multi-profile support later.

Suggested fields:

- `id TEXT PRIMARY KEY`
- `user_id TEXT NOT NULL UNIQUE`
- `display_name TEXT`
- `onboarding_state TEXT NOT NULL`
- `onboarding_completed_at TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Suggested onboarding states:

- `not_started`
- `in_progress`
- `complete`

### `profile_preferences`

Purpose: compact explicit preference state from onboarding/settings.

Suggested fields:

- `profile_id TEXT PRIMARY KEY`
- `content_scope TEXT NOT NULL` — `movies | series | both`
- `mainstream_hidden_gem_bias REAL NOT NULL`
- `classic_new_bias REAL NOT NULL`
- `region_scope TEXT NOT NULL` — `india | international | both`
- `surprise_level REAL NOT NULL`
- `updated_at TEXT NOT NULL`

Languages/genres should not be stored as comma-separated columns. Use normalized child tables when P4/P5 implementation begins.

### Future-normalized preference children

Prepared now, implemented only when needed:

- `profile_languages(profile_id, language_key, weight, source)`
- `profile_genres(profile_id, genre_id, weight, source)`
- `profile_title_seeds(profile_id, title_id, weight, source)`
- later interaction-derived signals stay distinct from explicit onboarding preferences

### `sessions`

Purpose: revocable server sessions.

Suggested fields:

- `id TEXT PRIMARY KEY`
- `user_id TEXT NOT NULL`
- `secret_hash TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `last_seen_at TEXT NOT NULL`
- `expires_at TEXT NOT NULL`
- `revoked_at TEXT`
- `user_agent_hint TEXT`

Store only a hash of the browser session secret. A stolen D1 row must not itself be a valid session token.

Do not store raw bearer/session secrets.

---

## Local-only profile contract

A local profile must work without creating a D1 user.

### Storage

Persist local-only state on the device/browser:

- local profile ID
- onboarding progress
- explicit preferences
- selected seed titles
- saved titles
- watched/not-for-me interactions that are safe to keep locally
- schema/version marker

Recommended browser storage:

- IndexedDB for structured profile state
- small non-sensitive feature/version flags may use `localStorage`

Do not use cookies as the primary local-profile database.

### Local-profile limitations shown to the user

A local profile:

- is tied to this browser/device
- does not automatically sync to other devices
- may be lost if site/app data is cleared
- can later be upgraded by signing in with Google

Do not imply cloud backup for local-only mode.

### Local profile deletion

“Delete local profile” must:

1. clear the local profile and interaction stores
2. clear onboarding/taste state
3. clear any local-only cache keyed specifically to that profile
4. leave public catalogue/cache data intact
5. return the product to first-time identity state

---

## Google sign-in contract

Use Google Identity Services on the client and verify the returned credential on the Worker before creating/binding an account.

### Required verification

The Worker must verify at minimum:

- token signature against Google keys
- issuer
- audience equals Cinema & Series Google client ID
- expiration
- nonce/CSRF flow as required by the chosen GIS integration

Only after successful verification may `sub` be used as `provider_subject`.

### Account resolution

For a verified Google identity:

1. lookup `(provider='google', provider_subject=sub)`
2. if found: load existing user/profile
3. if not found: create `users`, `user_identities`, `profiles`
4. if a local profile upgrade payload is present: migrate local state under the merge contract below
5. issue a Cinema & Series server session

Do not merge accounts solely because email strings match.

---

## Session contract

### Cookie

Web session should use a first-party cookie with:

- `HttpOnly`
- `Secure`
- explicit `SameSite` value
- narrow path/domain appropriate to the deployed app
- finite expiry

Recommended default for the current same-site architecture: `SameSite=Lax`, unless a future cross-site auth flow proves it inadequate.

### Session token shape

Recommended opaque token:

`<session_id>.<random_secret>`

Server:

1. parse session ID
2. load session row
3. compare constant-time hash of secret
4. require not revoked and not expired
5. load active user/profile

### Expiry

V1 recommendation:

- absolute session lifetime: 30 days
- rotate/reissue after sensitive account events or if product security requirements tighten
- update `last_seen_at` opportunistically, not on every request if that creates unnecessary D1 writes

### Logout

Logout must:

- revoke/delete current session server-side
- expire browser cookie
- keep the account/profile itself

### Logout all devices

Future-safe endpoint should revoke all active sessions for the user.

---

## Local-to-Google upgrade / merge contract

This is the critical P3 behavior.

### Rule

Signing in must never silently discard local state.

### Merge payload

Client may submit a versioned local-state envelope after Google verification:

- `local_profile_id`
- onboarding state/preferences
- selected seed titles
- saved titles
- explicit interactions
- client schema version

The server must validate every referenced title against known catalogue/recommendation identities. Client-provided genre/person metadata is never trusted as canonical catalogue metadata.

### Merge behavior

When Google identity has no prior Cinema & Series profile:

- adopt the local onboarding/preferences state
- copy saved/interactions to the new signed-in profile
- mark merge receipt/idempotency token consumed

When Google identity already has a profile:

- do not overwrite cloud profile wholesale
- union idempotent sets such as saves/watched where semantics allow
- preserve explicit cloud settings when conflict policy says cloud wins
- surface/resolve preference conflicts deterministically

Recommended initial conflict policy:

- completed cloud onboarding outranks incomplete local onboarding
- explicit latest user action wins when timestamps are trustworthy
- set-like interactions union by `(profile_id, title_id, action)`
- `not_for_me` should not be overridden merely by a local save

### Idempotency

Upgrade must be safe to retry. Use a migration/merge receipt keyed by a random client-generated merge ID or server-issued nonce so network retries cannot duplicate state.

Only after successful server acknowledgement should the client delete local-only profile state.

---

## Auth/API surface prepared for P3

Paths are provisional but contract semantics should remain stable.

- `POST /api/auth/google` — verify Google credential, resolve/create account, optional local-state merge, create session
- `POST /api/auth/logout` — revoke current session
- `POST /api/auth/logout-all` — revoke all sessions
- `GET /api/me` — current identity/profile/session summary
- `PATCH /api/me/profile` — profile presentation/preferences allowed by current phase
- `DELETE /api/me` — delete signed-in account under deletion contract
- local-only mode remains client-side until upgrade

Every state-changing request must use the authenticated session and appropriate CSRF protections for the selected cookie architecture.

---

## Account deletion contract

Signed-in “Delete account” must not be ambiguous with “Logout”.

Deletion should:

1. revoke all sessions immediately
2. remove provider identity bindings
3. remove or tombstone user/profile rows according to retention needs
4. delete personal preference/interaction state owned by that profile
5. preserve public catalogue/release metadata
6. never delete shared title/genre/person canonical records

If analytics are added later, account deletion requirements must be revisited explicitly.

---

## Privacy boundaries

Do not use the following as recommendation signals in V1:

- Google email
- Google name
- Google avatar
- IP address
- raw user-agent
- inferred demographics

Recommendation behavior is based on explicit taste choices and title interactions.

Avoid device fingerprinting for local identity.

---

## Security gates

P3 implementation is not complete until tests cover:

1. invalid/expired Google token rejected
2. wrong audience rejected
3. provider `sub` is canonical external key
4. repeated Google login resolves same user
5. session secret is never stored raw
6. expired/revoked session rejected
7. logout invalidates session
8. local-only mode makes no account row
9. local-to-Google migration is idempotent
10. retry after interrupted merge does not duplicate interactions
11. existing cloud profile is not destructively overwritten by local state
12. account deletion revokes all sessions
13. one user cannot read/modify another profile
14. CSRF protections cover cookie-authenticated mutation endpoints
15. no auth endpoint changes P1/P2 canonical catalogue metadata

---

## D1 write-discipline implications

Identity/profile traffic is fundamentally different from the current bulk catalogue/recommendation enrichment jobs.

P3 implementation must therefore:

- use small request-scoped writes
- avoid “update last_seen on every page/API request” write amplification
- batch migration of local state where safe
- keep catalogue/recommendation bulk pipelines separate from user-data tables
- preserve Free-tier awareness until the project intentionally changes plans

No P3 migration should be merged while P1 owns migrations `0021` and `0022` and P2/P3 numbering has not been revalidated against `main`.

---

## Implementation order once P3 is authorized

1. finalize migration number against current `main`
2. add user / provider identity / profile / session schema
3. add auth utility module and session-cookie helpers
4. implement read-only `/api/me`
5. implement Google credential verification + account resolution
6. implement session issue/verify/revoke
7. implement local profile client store
8. implement local-to-account merge endpoint/transaction
9. implement account/local-profile deletion flows
10. add exhaustive identity/session/merge tests
11. only then hand the stable profile contract to P4 onboarding UI

---

## Exit gate for P3

P3 is complete when:

- Google sign-in works against verified server-side identity
- Continue locally works without an online account
- sessions survive normal reload/revisit and can be revoked
- local-to-account upgrade preserves local state deterministically
- logout/delete-local/delete-account semantics are distinct and tested
- profile/preferences persistence contract is stable for P4/P5
- no regression is introduced into catalogue/release/recommendation metadata systems

---

## Explicitly deferred

Not part of P3 V1:

- passwords/email-password auth
- Apple login
- phone OTP
- social graph
- public profiles
- multiple household profiles under one account
- parental/child profiles
- cross-device local-mode sync without sign-in
- recommendation ML
- storing provider access tokens when only identity is needed

These remain OPEN only if later product evidence requires them.
