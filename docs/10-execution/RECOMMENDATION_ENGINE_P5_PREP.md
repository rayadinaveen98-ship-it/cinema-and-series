# Cinema & Series — Recommendation Engine V1 P5 Prep

**Status:** PREPARED / DO NOT IMPLEMENT BEFORE P4 EXIT  
**Prepared:** 2026-09-22  
**Phase:** P5 — Recommendation Engine V1  
**Active roadmap:** `docs/10-execution/PERSONALIZED_DISCOVERY_ACTIVE_ROADMAP_V1.md`  
**Onboarding dependency:** `docs/10-execution/FIRST_TIME_ONBOARDING_P4_PREP.md`  
**Identity dependency:** `docs/10-execution/IDENTITY_AND_PROFILES_P3_PREP.md`

## Purpose

Prepare the deterministic recommendation-engine contract for Cinema & Series without starting P5 implementation while P1 production population and later P2–P4 implementation gates remain incomplete.

The locked product philosophy remains:

`Eligible catalogue -> taste score -> diversity filter -> weighted random selection`

Recommendations are **relevant first, random second**. V1 does not require black-box ML.

This document prepares scoring semantics, input/output boundaries, safety invariants, interaction behavior, diversity, explanation rules, cold-start behavior and the future test corpus. It does not add recommendation code, profile schema, migrations, production tables, UI, API routes or D1 mutations.

---

## Phase ownership

P5 owns:

- deterministic taste-profile construction from validated user preference state
- recommendation eligibility rules
- deterministic relevance scoring
- diversity controls
- weighted random selection inside a relevance-qualified pool
- recommendation explanations
- explicit interaction feedback semantics
- recommendation test corpus and sanity gates

P5 does not own:

- canonical catalogue metadata — P1
- artwork provenance/publication rights — P2
- account/session identity — P3
- onboarding capture/persistence — P4
- Discover UI — P6
- personalized Home presentation — P7
- notifications — P9

No P5 inference may become canonical catalogue metadata.

---

## Source-of-truth inputs

### Catalogue/title inputs

P5 may consume only data already accepted by the relevant canonical product contracts.

Primary recommendation signals from the active roadmap:

- genre
- director / creator
- cast
- language
- country / industry
- release era
- movie vs series type
- explicit user interactions

The P1 canonical relationship contract remains authoritative for:

- Wikidata `P136` — genre
- Wikidata `P57` — director
- Wikidata `P170` — creator for Series where explicitly validated
- Wikidata `P161` — cast

P5 must not reconstruct missing canonical relationships from title text, popularity, image content, model guesses or page categories.

### User inputs

P5 consumes validated state handed off by P4/P3:

- content scope: movies / series / both
- explicit language choices
- explicit genre/mood choices with valid mappings where applicable
- mainstream vs hidden-gem preference
- classics vs newer preference
- India / international / both
- surprise level
- selected canonical seed title IDs
- later explicit title interactions

P5 must never use Google email, name, avatar, IP address, raw user-agent, inferred demographics or other unrelated identity data as recommendation signals.

---

## Deterministic taste-profile model

A taste profile is a versioned derived structure computed from explicit preferences and canonical title metadata.

It is not canonical title metadata and must be rebuildable from source inputs.

Prepared logical dimensions:

- `content_type_weights`
- `language_weights`
- `genre_weights`
- `person_weights`
- `country_industry_weights`
- `era_preference`
- `mainstream_hidden_gem_bias`
- `surprise_level`
- `seed_title_ids`
- interaction-derived adjustments
- profile/scoring version

### Seed-title expansion

For each valid seed title, P5 may derive weighted signals from canonical metadata already available for that title:

- genres
- director for Movies
- creator for Series where available
- cast
- language
- country/industry where supported
- release era

If a seed title lacks a particular signal, P5 skips that signal. It must not invent it.

### Duplicate/fan-out control

High-fanout metadata must not dominate simply because a title has many cast members or many granular genre claims.

Prepared requirements:

- deduplicate identical title-signal relationships
- cap or normalize per-title contribution for high-cardinality dimensions such as cast
- prevent the same person appearing in multiple seed titles from growing without a deterministic bound
- distinguish role semantics where useful (`director`, `creator`, `cast`)

Exact production caps/weights remain **WORKING parameters** until P5 starts and can be validated against a test corpus.

---

## Weight policy

This prep deliberately does **not** lock arbitrary numeric weights.

At P5 implementation start, one versioned parameter set must be selected and tested. Parameters should include, at minimum:

- explicit preference contribution
- seed-title genre contribution
- seed-title director/creator contribution
- seed-title cast contribution
- language contribution
- country/industry contribution
- era contribution
- content-type contribution
- explicit interaction boosts/penalties
- exploration/surprise contribution

Requirements for the eventual parameter set:

1. stored centrally rather than scattered magic numbers
2. versioned
3. deterministic for identical inputs
4. testable against a fixed corpus
5. explainable in user-facing reasons
6. easy to tune without changing canonical metadata
7. bounded so one dimension cannot accidentally dominate without an explicit decision

Do not describe a parameter set as “AI learned” unless a later phase actually introduces and validates such a system.

---

## Candidate eligibility

Scoring occurs only after eligibility filtering.

A candidate title must satisfy the applicable rules below.

### Required identity rules

- valid canonical Movie or Series identity
- not excluded by reviewed media-identity corrections
- not an unresolved cross-type collision
- usable display title
- enough metadata to calculate a meaningful score under the active engine version

### User-scope rules

- respect Movies / Series / Both selection
- respect hard user exclusions
- titles explicitly marked `not_for_me` are excluded from ordinary recommendation surfaces unless a future explicit undo changes that state
- titles already selected as seed titles should not normally be returned as discovery recommendations

### Watched behavior

`watched` is not the same as `not_for_me`.

Prepared default:

- exclude watched titles from ordinary “what should I watch next?” surfaces
- retain them as positive taste evidence only if the user did not also express a negative preference
- allow future specialized history/rewatch surfaces to use a different rule

### Saved behavior

Saved titles remain eligible or ineligible depending on surface intent.

Prepared default:

- ordinary discovery may avoid repeating saved titles too aggressively
- a saved title is a positive preference signal
- a dedicated saved/watchlist surface is not a recommendation surface and follows its own product rules

### Availability

Do not hard-filter by streaming availability unless Cinema & Series has a reliable, current availability contract. Availability uncertainty must not silently become a recommendation-quality judgment.

---

## Scoring contract

Each eligible title receives a deterministic **relevance score** before randomness.

Conceptually:

```text
score(title, profile) =
    content_type_component
  + language_component
  + genre_component
  + people_component
  + country_industry_component
  + era_component
  + explicit_interaction_component
  + exploration_component
  + optional_surface_component
```

This formula is conceptual. Exact normalization and parameters are locked only when P5 implementation begins.

### Score requirements

- same catalogue/profile/version -> same score
- missing metadata must not create fabricated positive matches
- components must be inspectable for explanation/debugging
- negative feedback must be capable of reducing/excluding related candidates without corrupting canonical data
- score scale must be stable enough to define relevance-qualified pools
- score ties must have deterministic pre-random ordering for testing

### Normalization

Because dimensions have different cardinalities, raw match counts are insufficient.

Future implementation should normalize dimensions so, for example:

- a title with 20 cast members does not automatically outrank one with 5
- extremely broad genres do not dominate every recommendation
- multiple seed titles reinforcing the same signal help, but with bounded diminishing influence where appropriate

The exact normalization function remains WORKING until corpus validation.

---

## Relevance-qualified pool

Random selection is allowed only after relevance qualification.

Prepared model:

1. score all eligible candidates for the requested surface/filter set
2. remove candidates below a minimum usefulness rule or outside the chosen relevance band
3. apply diversity controls
4. select using weighted randomness within the surviving pool

The engine must never perform a uniform random draw over the full catalogue and label it personalized.

### Pool construction options for implementation validation

Valid implementation candidates include:

- top-N by score
- titles within a score delta from the best candidate
- score percentile threshold
- hybrid minimum score + bounded top-N

The exact strategy is not locked by this prep because corpus tests should determine which provides enough relevance while preserving variety.

It must become one explicit versioned rule before P5 exits.

---

## Weighted randomness

Randomness prevents the product from returning the identical top title every time while preserving relevance.

Requirements:

- random selection occurs only inside the relevance-qualified/diversified pool
- selection probability must remain positively related to relevance unless a clearly labeled exploration mode says otherwise
- a random seed can be injected in tests for reproducibility
- production may use a non-deterministic runtime seed after deterministic candidate scoring/pool construction
- repeated “Another Pick” actions should avoid immediate duplicates

### Surprise level

`surprise_level` changes exploration strength; it does not bypass eligibility or safety.

Prepared semantics:

- low surprise: concentrate selection near strongest relevance cluster
- medium surprise: wider qualified pool
- high surprise: permit more adjacent/outside-comfort-zone candidates while retaining a minimum relevance relationship

Even maximum V1 surprise must not become full-catalogue roulette.

---

## Diversity guard

Diversity is applied before final weighted selection and/or during multi-item list assembly.

Goals:

- prevent a recommendation rail from being near-duplicates
- avoid all items sharing the same dominant genre/person/language unless the surface explicitly asks for that
- preserve selected content/language preferences
- allow meaningful variety across eras, industries and creators where candidate quality supports it

Potential diversity dimensions:

- Movie vs Series
- language
- primary genre
- director / creator
- franchise/series family later, when reliable
- release era
- country/industry

### Diversity must not manufacture weakness

Do not force a low-quality candidate merely to satisfy a quota.

If the qualified pool is narrow, it is acceptable to return fewer distinct options or explain that the current preference/filter combination is narrow rather than injecting irrelevant titles.

Exact diversity limits remain WORKING parameters until validated.

---

## Recommendation surfaces and surface modifiers

Core scoring remains shared. Surfaces may apply explicit modifiers or eligibility filters.

Prepared surfaces from the roadmap:

- Top Picks for You
- Because You Like `<genre/title>`
- Hidden Gems for You
- From Directors/Creators You May Like
- Series You Might Love
- Outside Your Comfort Zone
- A Random Pick for Tonight

### Top Picks for You

Use strongest general profile relevance with diversity.

### Because You Like X

Require a real traceable relationship to the stated reason.

If the reason is a title, explanation signals may come from canonical overlap such as shared genre/director/creator/cast/language.

Do not claim “Because you like X” when no material scoring relationship exists.

### Hidden Gems for You

Needs a separate evidence-backed definition of “hidden gem” before production. P5 may consume a future title classification but must not invent obscurity solely from a low view/popularity field of uncertain provenance.

Until that definition exists, this surface remains contractually named but its eligibility classifier is OPEN.

### Director/Creator surface

Requires canonical P1 role relationships and a meaningful profile affinity to the person.

### Series You Might Love

Restrict content type to Series and apply shared relevance logic.

### Outside Your Comfort Zone

Use controlled exploration: preserve some positive relevance bridge while intentionally reducing similarity to the strongest cluster.

### Random Pick for Tonight

Random means weighted random from a qualified pool, not unrestricted random.

---

## Explanation contract

Every returned recommendation should be capable of producing at least one honest, traceable reason when the surface expects an explanation.

Prepared reason classes:

- genre affinity
- language affinity
- director affinity
- creator affinity
- cast affinity
- similar to a seed/liked title through concrete shared signals
- era preference
- India/international preference
- controlled exploration based on surprise level

### Explanation rules

- reason must correspond to a non-zero scoring contribution or explicit surface rule
- do not expose internal numeric weights to users unless intentionally designed later
- do not claim causal certainty (“you will love this”)
- avoid unsupported emotional/theme descriptions
- one concise primary reason is preferable to a noisy list
- debugging output may include full component breakdown, but user copy should remain simple

---

## Explicit interaction model

Prepared interaction actions:

- `save`
- `unsave`
- `watched`
- `unwatched`
- `not_for_me`
- `undo_not_for_me`
- positive actions associated with “More Like This” where product implementation records them

### Interaction principles

1. Explicit actions outrank inferred behavior.
2. `not_for_me` is a strong negative signal/exclusion, not a canonical title judgment.
3. `watched` is history, not inherently positive or negative.
4. `save` is a positive-intent signal.
5. Undo operations must restore the appropriate prior semantic state, not append contradictory permanent flags.
6. Interactions are user/profile data, never shared canonical metadata.
7. Repeated idempotent actions must not multiply influence.

### Negative-feedback propagation

A `not_for_me` action may reduce affinity to related signals, but propagation must be bounded.

One disliked title must not automatically blacklist an entire genre, language, country or actor.

Implementation should distinguish:

- direct title exclusion — strong
- related-signal negative adjustment — weaker and bounded

Exact penalty parameters remain WORKING until validated.

---

## More Like This

“More Like This” creates a temporary or explicit reference-title context in addition to the normal profile.

Candidate similarity may use canonical overlap in:

- genre
- director / creator
- cast
- language
- country/industry
- era

Requirements:

- reference title itself excluded
- user hard negatives still excluded
- relevance to the reference cannot be fabricated
- profile affinity may still break ties or filter obviously unsuitable candidates
- resulting explanation should identify a real overlap

Whether invoking “More Like This” itself creates a durable positive interaction is a product decision to lock at implementation; do not silently treat every click as a permanent strong preference without explicit design.

---

## Another Pick

“Another Pick” should request another item from the same logical surface/context while applying a short-term session exclusion set.

Prepared behavior:

- exclude immediately shown items for a bounded recent window
- preserve same filters/context
- rescore only when source state/profile context changed; otherwise reuse deterministic score state where practical
- perform a new weighted draw among remaining qualified candidates
- once the pool is exhausted, product may reset the recent exclusion set with clear deterministic rules

Do not permanently penalize a title merely because the user asked for another pick unless the user separately chooses `not_for_me`.

---

## Cold-start contract

### No completed onboarding

Do not claim personalization.

The product may show non-personalized editorial/release/catalogue surfaces, but P5 personalized surfaces should wait for sufficient explicit state.

### Completed onboarding, sparse seed metadata

Use explicit questionnaire preferences plus whatever validated seed signals are available.

Do not invent metadata for sparse seeds.

### Local profile

P5 should work from local explicit state under P3/P4 semantics without requiring cloud identity.

### New signed-in profile after local upgrade

Use the merged profile state after P3’s idempotent migration. Do not maintain separate competing taste profiles for the same migrated state.

---

## Catalogue change and rebuild semantics

Taste profiles and recommendation scores are derived data and must tolerate catalogue changes.

Prepared rules:

- profile/source data carry version identifiers
- if canonical metadata changes through reviewed provenance-safe updates, derived taste/recommendation state may be rebuilt
- removed/excluded title identities must disappear from future candidate pools
- stale cached recommendations must never reintroduce a reviewed-excluded identity
- rebuild must not mutate canonical metadata

P5 should prefer recomputable derived state over opaque irreversible aggregates.

---

## Caching contract

Caching may improve latency but must not become truth.

Safe cached objects may include:

- versioned derived taste profile
- candidate score list for a profile/surface/filter/version tuple
- recent draw/session exclusions
- precomputed global metadata features derived from canonical relationships

Cache keys must include enough version information to avoid serving scores built against incompatible profile/catalogue/scoring versions.

P5 implementation must remain viable on the project’s free-first architecture; avoid unnecessary D1 write amplification from every recommendation request.

---

## Determinism and reproducibility

For tests and debugging, recommendation construction must support reproducibility.

Given:

- same canonical catalogue snapshot
- same profile state
- same interaction state
- same engine parameter version
- same requested surface/filters
- same injected random seed

…the ordered candidate pool and selected result(s) must be reproducible.

This is mandatory for meaningful regression testing.

---

## Test corpus preparation

P5 implementation must ship with a fixed synthetic/curated test corpus that exercises both India-first and international behavior.

The corpus should include profiles such as:

- Telugu mainstream Movie-heavy user
- Malayalam/Tamil hidden-gem leaning user
- Hindi + international mixed user
- Series-first user
- classics-focused user
- newer-release-focused user
- narrow single-language preference
- multilingual broad preference
- high-surprise explorer
- low-surprise conservative profile
- local profile
- migrated local-to-Google profile
- user with watched/save/not-for-me history

No test profile needs to correspond to a real person.

---

## Recommendation sanity invariants

At minimum, future P5 tests must prove:

1. same deterministic inputs yield same score breakdown
2. user content-scope filter is respected
3. hard `not_for_me` title is never returned in ordinary recommendation surfaces
4. seed title itself is not returned as a new recommendation
5. watched exclusion behaves according to surface rule
6. duplicate interaction retries do not multiply weight
7. missing metadata contributes zero rather than fabricated matches
8. Movie creator relationships are not invented from Series creator logic
9. Series creator signal works when canonical relationship exists
10. high-cardinality cast cannot dominate unboundedly
11. weighted randomness never draws outside qualified pool
12. low surprise is more concentrated than high surprise under the same profile
13. maximum surprise still preserves minimum relevance
14. diversity guard prevents obvious repetitive rails when alternatives exist
15. diversity never injects below-threshold junk merely to satisfy quotas
16. explanation reason corresponds to an actual score/surface contribution
17. `Another Pick` avoids recent duplicates without creating negative feedback
18. `More Like This` returns candidates with traceable overlap
19. local and equivalent migrated profile produce equivalent taste state after merge
20. reviewed-excluded identities cannot enter candidate pools
21. engine version changes are explicit and regression-testable
22. no recommendation operation mutates canonical P1/P2 metadata

---

## Quality metrics prepared for validation

P5 should not be declared successful from subjective screenshots alone.

Useful offline metrics include:

- eligibility rate by profile/surface
- qualified-pool size
- top-K genre/language/person overlap with profile
- intra-list diversity
- duplicate rate across repeated draws
- explanation availability rate
- exclusion correctness
- percentage of recommendations with sufficient provenance-backed metadata
- sensitivity of recommendations to deliberate profile changes
- stability under non-material catalogue ordering changes

These metrics are diagnostic; no arbitrary pass thresholds are locked by this prep.

Human review of fixed test profiles remains required before P5 exit.

---

## Popularity and hidden-gem caution

The roadmap wants mainstream-vs-hidden-gem preference, but the product must not pretend it already has a trustworthy universal popularity model.

Before popularity affects P5 production scoring, its source and semantics must be documented.

Acceptable directions may later include:

- evidence-backed title popularity/engagement source with clear date/scope
- product-local interaction aggregates after sufficient usage, with privacy safeguards
- editorial/reviewed classification

Do not use arbitrary database order, title age or missing artwork as a proxy for obscurity.

Until a reliable classifier exists, mainstream/hidden-gem preference can influence only dimensions for which the product has an explicit valid signal or remain partially dormant without fake behavior.

---

## Era semantics

P4 captures classics-vs-newer preference. P5 must define a deterministic mapping before using it.

Possible implementation forms:

- continuous age-decay/affinity function
- versioned era buckets
- profile-relative recency weighting

The exact mapping is OPEN until test-corpus review.

Requirements:

- use real supported release/air chronology
- do not infer exact dates from year-only data
- missing chronology contributes no era match rather than an invented one

---

## Country / industry semantics

India/international preference is a discovery preference, not user identity.

P5 must consume only title country/industry signals already supported by the catalogue contract.

For Indian cinema, language and country/industry may overlap but must not be treated as identical concepts.

Do not infer a user’s region, ethnicity or nationality from their movie choices.

---

## Mood semantics

The roadmap permits genre/mood onboarding choices, while P1 currently locks canonical genre relationships.

Therefore:

- canonical genres may directly match canonical title genre metadata
- moods that do not have an evidence-backed title-feature model remain explicit profile labels only
- unsupported moods must not be silently mapped to genres/persons through an LLM guess

A future reviewed mood/title tagging system may extend P5, but it is not required for V1.

---

## API/output contract preparation

Exact API paths are deferred to implementation, but a recommendation result should logically contain:

```text
request_context
engine_version
surface
candidate_title_id
media_type
relevance_score or opaque internal score reference
primary_reason
reason_code
supporting_signal_ids (internal/debug as appropriate)
selection_context
artwork projection from P2/API layer
```

Public responses need not reveal proprietary/internal numeric weights.

Debug/test mode should make score components inspectable without exposing another user’s profile data.

P5 must not directly embed guessed artwork URLs; it consumes P2’s title-artwork projection/fallback contract.

---

## Interaction persistence preparation

P5 may require profile interaction storage when implementation begins, but **this document reserves no migration number**.

Before implementation:

- revalidate migration numbering against `main`
- reuse P3/P4 profile ownership model
- define idempotent unique semantics for current interaction state
- distinguish event history from current-state flags if both are needed
- avoid write-on-read behavior
- define retention/deletion under P3 account/local-profile deletion contracts

No `0023+` migration is authorized while P1 owns its active schema window.

---

## Security and privacy gates

Future P5 implementation must prove:

- one profile cannot retrieve another profile’s private recommendation context
- recommendation endpoints validate P3 identity/session where cloud profile data is used
- local recommendation state stays local unless explicitly merged
- user interactions cannot mutate shared catalogue metadata
- malformed title IDs are rejected
- reviewed-excluded identities remain excluded
- debug score breakdown is not exposed across users
- no identity PII is used as a taste signal
- account/local-profile deletion removes owned interaction/taste derived state as required

---

## Performance expectations

P5 must work interactively on the existing web-first product and Android wrapper.

Prepared implementation principles:

- filter before expensive scoring where possible
- use indexed normalized metadata relationships
- avoid full-catalogue client downloads
- bound candidate-pool construction
- cache derived features safely
- avoid D1 writes during ordinary recommendation reads
- design for current free-first Cloudflare architecture before introducing external vector/ML infrastructure

A future scale threshold may justify additional infrastructure, but V1 should first prove usefulness with deterministic relational scoring.

---

## Implementation order once P5 is authorized

1. re-read P1–P4 final evidence and current roadmap
2. freeze engine input/output schema version
3. define fixed test corpus
4. choose initial WORKING weight/normalization parameter set
5. implement deterministic taste-profile builder
6. implement candidate eligibility filters
7. implement componentized relevance scoring
8. implement qualified-pool rule
9. implement diversity guard
10. implement weighted random selection with injectable test seed
11. implement explanation generator from score/surface evidence
12. implement interaction state and bounded feedback effects
13. implement `More Like This` context
14. implement `Another Pick` recent-exclusion behavior
15. run offline corpus metrics and human sanity review
16. tune parameters through explicit version changes, never silent magic-number drift
17. expose stable engine contract to P6 Discover and P7 Home

Do not start with UI randomization or black-box embeddings before deterministic scoring is proven.

---

## P5 exit gate

P5 is complete only when:

- deterministic taste profile builds from validated P4/P1 inputs
- eligibility rules correctly respect scope, exclusions and reviewed identities
- scoring is componentized and reproducible
- relevance-qualified pool prevents full-catalogue roulette
- diversity guard works without degrading relevance below the minimum rule
- weighted random selection is reproducible in tests and varied in production
- explanation reasons are truthful and traceable
- explicit interactions have idempotent bounded effects
- `Another Pick` and `More Like This` semantics pass regression tests
- fixed India-first + international corpus passes sanity review
- no canonical metadata is invented or mutated
- engine contract is stable enough for P6/P7 consumption

---

## Explicitly deferred

Not required for P5 V1:

- collaborative filtering
- embeddings/vector database
- LLM-generated taste inference
- deep-learning ranking
- cross-user similarity
- social recommendations
- streaming-provider availability ranking without reliable availability data
- opaque auto-tuning in production
- demographic targeting
- advertising optimization

These may be considered later only with evidence that deterministic V1 is insufficient.

---

## Sequencing lock

This document is **PREPARED ONLY**.

It does not change the active implementation sequence.

Current production priority remains **P1 Recommendation Metadata Foundation** until its full 16,380-title graph is in production and all exact graph/provenance/Catalogue Quality exit gates pass.

P2 production follows P1. P3 follows its required prior-phase exits. P4 follows P3. **P5 implementation follows P4 exit.**

No recommendation engine code, profile scoring service, interaction migration, recommendation API, Discover behavior or Personalized Home logic is authorized by this document.
