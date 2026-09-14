# Control Room Admin Workflows

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Workflow principles

1. Humans review exceptions, not routine high-confidence imports.
2. Every material action is auditable.
3. Destructive-looking identity actions must be reversible where practical.
4. Editors create evidence-backed decisions; they do not erase source history.
5. The UI must show consequences before merge/split/override actions.
6. Rights/policy decisions are separate from metadata correctness.

---

## WF-01 — New title discovered

### Trigger
Discovery Engine identifies a possible new movie/series/special/episode.

### Flow
1. Create discovery lead.
2. Check source policy eligibility.
3. Acquire approved evidence.
4. Parse and normalize candidate facts.
5. Identity Engine searches existing CAS entities.
6. If high-confidence existing match: attach claims to existing entity.
7. If high-confidence new entity: create canonical CAS identity shell and claims under automated rules.
8. If ambiguous: create Identity Review item.
9. Canonicalization selects supported initial facts.
10. Quality Engine checks minimum identity integrity.

### Human review only when
- identity is ambiguous;
- source evidence conflicts;
- work/version/remake/dub classification is unclear;
- policy blocks automation.

---

## WF-02 — Working title becomes official title

1. New official title evidence arrives.
2. Identity Engine links evidence to existing untitled/working-title project.
3. Create new title claim with type `official/current`.
4. Preserve previous working title as historical/alias title.
5. Canonicalization updates display title if authority/rules permit.
6. Record effective date and canonical change history.
7. Do not create a second Work merely because the marketing title changed.

If identity linkage is uncertain, route to CR-301.

---

## WF-03 — Release date changes

1. Release Engine receives new claim.
2. Match the claim to the correct release event: territory + version + format/platform.
3. Compare against current scheduled/actual event state.
4. Preserve old scheduled date in event history.
5. If authoritative and non-conflicting, update canonical scheduled date automatically.
6. If sources disagree materially, create CR-303 Release Verification item.
7. Once actual release is evidenced, retain scheduled history separately from actual date.

Never overwrite the only historical evidence of postponement.

---

## WF-04 — Duplicate title review

### Reviewer sees
- both CAS entities side by side;
- native/localized titles;
- years/release events;
- languages/territories;
- directors/cast/company overlap;
- external IDs;
- source claims;
- relationship/version information;
- machine match reasons;
- merge consequences.

### Actions
- Merge: same entity.
- Keep separate: distinct entities.
- Link relationship instead: e.g. remake/version/adaptation.
- Need more evidence.

### Merge requirements
- preview all moved claims/credits/releases/assets/relationships;
- choose survivor CAS ID according to merge policy;
- maintain redirect/alias from retired ID;
- store merge event and operator/reason;
- support later split/recovery.

---

## WF-05 — Incorrect merge recovery

1. Open prior merge event.
2. Display original pre-merge entity state and later additions.
3. Identify which claims/relationships/releases belong to each restored entity.
4. Preview split result.
5. Execute controlled split with new/restored identity mapping.
6. Re-run canonicalization and search projections.
7. Record full recovery audit event.

Split tools are privileged and never a blind one-click action.

---

## WF-06 — Conflicting canonical fact

Example: runtime, release date, birth date, credit, original language.

1. Conflict Engine groups competing claims for one predicate/context.
2. Reviewer sees source authority, dates, exact values and evidence references.
3. System shows current canonical rule/recommendation.
4. Reviewer may:
   - accept recommended claim;
   - choose another admissible claim;
   - mark unresolved/conflicting;
   - request more evidence;
   - reject a malformed/incorrect claim;
   - create an editor-backed correction claim with evidence/reason.
5. Reconciliation runs again.
6. Canonical change is logged.

A reviewer cannot delete inconvenient evidence merely to remove the conflict.

---

## WF-07 — Dub vs remake vs version classification

1. Identity/Relationship Engine flags ambiguous records.
2. Reviewer compares production identity, cast/crew, language production facts, footage/work lineage and source descriptions.
3. Choose:
   - same Work + dubbed Version;
   - same Work + alternate Version/cut;
   - separate Work linked by `remake_of`;
   - separate adaptation/reboot/etc.;
   - unresolved.
4. Reassign releases/credits/aliases only after preview.
5. Rebuild graph/search projections.

This workflow is mandatory for Indian multi-language edge cases.

---

## WF-08 — Person/company identity review

1. Candidate external identity arrives.
2. Compare name/aliases, career timeline, credits, companies, geography and external IDs.
3. Auto-link only above validated threshold with no contradiction.
4. Otherwise reviewer merges/keeps separate/requests evidence.
5. Stage names/pseudonyms remain aliases unless evidence supports separate public identities under a defined rule.

---

## WF-09 — Production lifecycle update

1. New status evidence arrives.
2. Validate allowed transition or record exceptional transition with reason.
3. Preserve prior lifecycle state/event.
4. Update current production projection.
5. Detect stale states (e.g. filming for implausibly long period).
6. Conflicting official status signals create review work.

Rumor does not become `ANNOUNCED` without admissible evidence.

---

## WF-10 — Artwork candidate review

1. Media Engine discovers/fetches candidate under source policy.
2. Run checksum/duplicate/resolution/format checks.
3. Display source, provenance, rightsholder/license/usage basis and attribution requirements.
4. Reviewer actions:
   - approve for defined usage;
   - reject rights/quality;
   - quarantine pending rights verification;
   - mark duplicate;
   - choose primary display asset among approved assets.
5. Log decision.

Metadata record remains valid even if no artwork is approved.

---

## WF-11 — Source incident / suspension

1. Detect outage, schema drift, abnormal error rate, policy/terms change or data-quality regression.
2. Create incident with severity.
3. Operator may throttle, pause or suspend adapter.
4. Existing canonical catalogue remains available.
5. Claims already ingested remain auditable subject to policy requirements.
6. Validate fix/new policy before re-enabling.
7. Backfill/reprocess missed interval safely.

---

## WF-12 — Targeted reprocessing

Use when parser/normalizer/canonicalization rules improve.

1. Define exact source/entity/time cohort.
2. Preview number of snapshots/claims/entities affected.
3. Queue reprocessing with rule/parser version.
4. Do not reacquire source unless necessary.
5. Compare before/after canonical impact.
6. Escalate unexpected large changes.
7. Record job and version in audit log.

---

## WF-13 — Manual correction

Manual correction is permitted but never as an unexplained direct overwrite.

1. Open entity/field.
2. Add editor-backed claim.
3. Supply reason and evidence/reference when available.
4. Mark claim authority/type appropriately.
5. Run normal canonicalization.
6. Preserve previous canonical value and all source claims.

---

## WF-14 — Validation corpus case

1. Load benchmark case with expected identity/relationships/releases/search behavior.
2. Run current pipeline/rules.
3. Record pass/fail by dimension.
4. Link failures to engine/rule issue.
5. Prevent V1 freeze while critical benchmark failures remain above accepted threshold.

## Definition of good operations

The Control Room should make it possible to process thousands or millions of automated changes while keeping human review focused on the small fraction that materially affects identity, truth, legality or user trust.
