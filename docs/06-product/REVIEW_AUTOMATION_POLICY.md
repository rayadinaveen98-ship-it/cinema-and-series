# Review Automation Policy

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Goal

The Control Room should not become a bottleneck. Routine, well-supported changes must flow automatically; ambiguous or high-impact changes must reach humans with the evidence already organized.

## Decision classes

### AUTO-APPLY
Allowed only when:
- production-approved source/policy permits the data use;
- identity is already known or match confidence exceeds a validated threshold;
- field-specific canonicalization rule is deterministic;
- no protected conflict exists;
- no destructive identity operation is required;
- operation is auditable and reversible;
- validation rules pass.

Examples:
- a trusted source confirms the same release date already supported by other claims;
- a known entity gains a non-conflicting external ID;
- an approved source supplies an additional alternate title;
- canonicalization reselects the same value after new corroborating evidence.

### AUTO-APPLY + WATCH
The system may apply but creates a monitored finding/event because the change deserves short-term observation.

Examples:
- upcoming release date changes from an authoritative source;
- production state advances normally;
- a primary title changes from working title to official title with strong linkage;
- large credit batch changes from a reliable source.

### HUMAN REVIEW
Required when any of the following applies:
- medium-confidence identity match;
- possible entity merge/split;
- dub/version/remake boundary ambiguity;
- authoritative sources conflict materially;
- relationship change alters work identity graph;
- manual override would supersede strong evidence;
- source reliability recently regressed;
- artwork/media rights status is ambiguous;
- change affects many downstream entities unexpectedly.

### HOLD
Do not publish or canonicalize when:
- source/policy status is not approved;
- evidence is rumor-only or unsupported for the proposed canonical state;
- parser/extraction confidence is below validated minimum;
- entity identity cannot be bounded safely;
- operation would discard unresolved provenance;
- source incident makes new observations suspect.

### REJECT
Reject when:
- source/use is explicitly prohibited;
- claim is demonstrably malformed/irrelevant;
- candidate is a known duplicate discovery with no new evidence;
- media is unusable under current rights policy;
- automated action violates a locked domain rule.

## Protected actions

These are never routine AUTO-APPLY in V1:
- merge two CAS entities when not already proven equivalent by a safe deterministic identity key;
- split a prior merge;
- convert one Work into multiple Works or vice versa;
- classify ambiguous dub/remake/version cases;
- delete evidence/history;
- activate a new production source;
- approve uncertain artwork rights;
- mass canonical override outside a reviewed rule migration.

## Risk score is explanatory, not magical

The platform may calculate internal risk/confidence inputs, but the UI must expose why an item was routed to review. Avoid opaque labels such as `80% confidence` without contributing factors.

Useful factors include:
- source authority for the field;
- independent corroboration;
- recency/effective date;
- identity evidence strength;
- contradiction count/severity;
- historical source reliability;
- affected entity count;
- reversibility;
- policy status.

## Review queue prioritization

Priority should combine:
1. integrity/policy severity;
2. user-facing impact;
3. near-term release timing;
4. age of unresolved item;
5. number of entities affected;
6. source/engine incident scope;
7. validation-corpus relevance.

Popularity may influence operational urgency but must not permanently starve long-tail/historical cinema quality work.

## Recommended review card

Each item should show:
- queue type + severity;
- entity identity/context;
- exact proposed change;
- current canonical value/state;
- competing evidence;
- source authority/freshness;
- machine recommendation with reasons;
- affected downstream objects;
- reversibility;
- available actions;
- audit/history link.

## Bulk actions

Bulk approval is allowed only for cohorts produced by the same validated deterministic rule and after impact preview. Identity merges, rights approvals and unresolved conflicts are excluded from blind bulk approval.

## Escalation

A reviewer can escalate an item to:
- source/policy review;
- domain-model review;
- parser/engine bug;
- architecture/ADR decision;
- unresolved research case.

The system should never force a reviewer to choose a false answer merely to clear a queue.

## Success metric

The desired operating ratio is **very high automated throughput with a small, high-value human review queue**. Exact percentages will be set only after validation corpus and source benchmark data exist.
