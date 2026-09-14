# Automation Thresholds — Cinema and Series V1

**Status: LOCKED**  
**Date: 2026-09-14**

## Principle

V1 optimizes for **zero silent destructive identity errors**, not maximum automation rate.

The system automates low-risk evidence processing and canonical field updates aggressively where rules are deterministic, while identity merges, ambiguous Work/Version decisions and rights-sensitive publication remain protected.

# 1. Action classes

- `AUTO_APPLY` — deterministic, low-risk change; immediately apply and audit.
- `AUTO_APPLY_WATCH` — apply, but create watch/alert because value is volatile/high-impact.
- `HUMAN_REVIEW` — no canonical/destructive action until reviewed.
- `HOLD` — insufficient evidence, policy uncertainty or unresolved conflict.
- `REJECT` — invalid, prohibited, wrong entity or unsupported.

# 2. Identity safety rules

## 2.1 Entity merge

**V1 rule: NEVER fully automatic.**

All Work, Person and Organization merges require `HUMAN_REVIEW`.

Even when two sources share an external identifier, the Identity Engine may produce a high-confidence merge proposal but cannot execute it automatically.

Reason: a false merge corrupts credits, releases, relationships and provenance across the graph and is more expensive than a temporary duplicate.

## 2.2 Existing external-ID attachment

`AUTO_APPLY` only when:
- the exact external namespace+identifier is already mapped to exactly one CAS entity;
- incoming evidence refers to that same provider entity;
- no conflicting CAS mapping exists;
- adapter/source policy allows the field.

If an external ID appears mapped to multiple CAS entities -> `HUMAN_REVIEW` / identity conflict.

## 2.3 New candidate entity creation

Can be `AUTO_APPLY` into candidate/canonical catalogue only when all are true:
- source is approved for entity discovery;
- work/person/org type is supported;
- identity fingerprint passes minimum evidence policy;
- no strong duplicate candidate exceeds review threshold;
- required provenance is present.

A newly created entity may still have sparse metadata. Creation is not proof that every imported claim is canonical.

# 3. Work vs Version / dub / remake

The following always require `HUMAN_REVIEW` unless an already-adjudicated deterministic relationship rule applies:
- remake vs dub ambiguity;
- simultaneously-shot language version ambiguity;
- alternate cut vs separate Work;
- compilation/combined release vs new Work;
- reboot/revival vs continuation ambiguity;
- split Work / re-edited streaming structure ambiguity.

Once a specific pattern has a gold-corpus rule and deterministic classifier with required evidence, low-risk instances may later move to automation by a superseding policy version.

# 4. Field canonicalization thresholds

## 4.1 AUTO_APPLY

Allowed when:
- one eligible direct-authority claim exists and there is no eligible competing claim for the same slot; OR
- two or more independent eligible strong claims agree and no equal/higher-authority conflict exists; OR
- the change is deterministic normalization/derivation from already canonical evidence.

Examples:
- normalized ISO language/script mapping;
- source-approved external ID mapping with no conflict;
- direct certification authority value for its own certificate context;
- final official title replacing a prior working title while preserving history;
- deterministic transliteration search token generation;
- canonical search projection rebuild.

## 4.2 AUTO_APPLY_WATCH

Use when evidence is strong enough to display but the field is volatile or operationally important.

Examples:
- future release date from competent first party;
- current production state;
- upcoming title change;
- current availability offer when a licensed source exists;
- official cast announcement before final credits.

Watch means:
- automatic canonical projection is allowed;
- next refresh due date is scheduled;
- conflicting/newer evidence escalates immediately;
- history is preserved.

## 4.3 HUMAN_REVIEW

Required when:
- two direct/high-authority claims conflict without temporal explanation;
- a field affects entity identity/Work boundaries;
- historical sources disagree materially;
- a manual claim would override stronger direct evidence;
- rights/licensing status is uncertain;
- a source mapping would create a graph-wide merge/split;
- date precision/context cannot be reconciled automatically.

## 4.4 HOLD

Use when:
- evidence is plausible but below threshold;
- source is reference-only for that use;
- source terms are pending review;
- relationship is suspected but unsupported;
- AI extraction has no verified evidence locator;
- candidate title is only rumor/unverified trade chatter.

## 4.5 REJECT

Use when:
- source/use is prohibited;
- evidence is demonstrably wrong entity;
- malformed/invalid value;
- unsupported AI-generated fact;
- duplicate source propagation adds no new evidence and is being treated as independent confirmation;
- asset rights fail publication gate.

# 5. Trust tiers are gates, not confidence percentages

V1 does not publish or base destructive decisions on a generic `87% confidence` number.

Rules use discrete evidence classes and context:
- direct authority / regulator;
- strong open/structured source;
- licensed/curated provider;
- archival/scholarly source;
- reputable secondary source;
- weak/unverified lead.

Source trust remains field-specific.

# 6. Manual claims

A CAS editor can create an explicit manual/editorial Claim with:
- source/evidence locator;
- semantic slot;
- proposed value;
- rationale;
- timestamp/editor;
- authority classification.

Manual Claims **do not automatically outrank direct authoritative evidence**.

An editor may issue a CanonicalDecision that prefers a claim only with a reason code. Strong-authority override requires written rationale and remains reversible/audited.

# 7. Source suspension

When a source is suspended:
- stop new ingestion immediately;
- retain existing source Claims if retention is legally permitted;
- mark source policy/status change;
- recanonicalize only where continued use/publication is no longer permitted or evidence becomes invalid;
- preserve historical audit decisions;
- never delete CAS entity identity merely because one source was suspended.

# 8. Protected actions

Always protected in V1:
- merge Work/Person/Organization;
- split merged entity;
- delete/tombstone canonical entity;
- Work <-> Version reclassification;
- manual override of direct authority;
- source production activation;
- source policy exception;
- rights-sensitive asset approval where rights are uncertain.

# 9. Approval model for single-owner V1

V1 does **not** require mandatory two-person approval because the project initially has a single primary operator.

Instead protected actions require:
- explicit confirmation in Control Room;
- reason code;
- optional notes/evidence;
- immutable audit event;
- reversible operation where technically possible.

The data model must support future dual-review/approval without schema redesign.

# 10. Quality targets

Before freeze/production:
- known critical false automatic merges: **0**;
- known critical automatic Work-vs-Version misclassifications: **0**;
- automatic direct-authority field updates on benchmark: >= 99% expected semantic correctness;
- every automatic canonical change: 100% explainable by rule version + Claims;
- every protected action: 100% audited;
- every HOLD item remains non-canonical unless a separate eligible claim supports the fact.

# 11. Revisit rule

Automation may become more aggressive only when:
1. the relevant cohort has sufficient gold cases;
2. measured precision meets the risk threshold;
3. a policy/rule version change is reviewed;
4. rollback/replay is tested.

V1 defaults conservative by design.