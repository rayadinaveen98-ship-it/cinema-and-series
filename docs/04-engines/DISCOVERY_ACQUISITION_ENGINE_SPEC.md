# Discovery + Acquisition Engine Specification

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Objective

Continuously identify potentially useful cinema/series information and retrieve it only through approved, policy-aware source adapters.

Discovery and acquisition are intentionally separated:

- **Discovery** answers: *what might have changed or what might exist?*
- **Acquisition** answers: *what evidence can we legally/technically obtain from an approved source?*

## Discovery objects

A discovery is a lead, not truth. It may represent:
- possible new work;
- possible new person/company;
- title reveal/working-title change;
- production-state change;
- cast/crew announcement;
- release-date announcement/change;
- certification event;
- festival selection/premiere;
- streaming/digital availability event;
- relationship clue (remake, sequel, adaptation, franchise);
- artwork/media candidate;
- possible correction to existing metadata.

Each discovery records:
- discovery_id;
- source/source class;
- discovered_at;
- source locator/reference;
- candidate entity type;
- rough extracted names/IDs;
- discovery reason;
- dedupe fingerprint;
- priority;
- policy status;
- processing state.

## Discovery states

`NEW -> DEDUPED -> ELIGIBLE -> ACQUISITION_QUEUED -> PROCESSED`

Possible exits:

`IGNORED`, `REJECTED_POLICY`, `DUPLICATE_DISCOVERY`, `STALE`, `ERROR`.

## Priority model

Priority should consider:
- officially announced new projects;
- near-term release dates;
- high-change upcoming productions;
- source authority;
- conflict with current canonical data;
- title/entity importance only as an operational factor, never as a reason to ignore long-tail cinema permanently;
- age of unresolved discovery;
- user/admin escalation.

## Acquisition adapters

Every source has an adapter implementing a normalized contract, conceptually:

- identify source and policy version;
- fetch by allowed mechanism;
- preserve response/source metadata;
- compute checksum/fingerprint;
- emit snapshot reference;
- classify fetch result;
- expose retryability and rate-limit information.

Adapters must not understand CAS canonical business rules beyond the minimum needed to fetch and label source material.

## Adapter prerequisites

A source may not run in production acquisition unless its Source Registry record has:
- production approval status;
- documented access method;
- current terms/license review;
- commercial-use status if applicable;
- attribution requirements;
- rate-limit/quota policy;
- fields/use-cases allowed;
- media/artwork rules separately documented;
- operational owner/fallback behavior.

## Snapshot policy

Where legally/technically permitted, acquisition creates an immutable snapshot containing or referencing:
- source_id;
- retrieval timestamp;
- source publication/update timestamp if known;
- URL/resource identifier;
- request parameters relevant to reproducibility;
- HTTP/API metadata where relevant;
- checksum;
- payload/object reference;
- adapter version;
- policy/license version used;
- success/failure classification.

If raw retention is not permitted, retain the minimum compliant evidence/reference needed to support claims and audit processing.

## Idempotency

Repeated fetching of unchanged source material should not create uncontrolled duplicate snapshots/claims. Use source-specific fingerprints/checksums and idempotency keys while preserving genuine time-series observations when change detection matters.

## Change detection

Adapters may emit a change signal when:
- checksum changes;
- structured revision/version changes;
- important monitored fields change;
- a previously missing resource appears/disappears;
- an upstream ID redirects/merges/splits;
- access/policy state changes.

## Polling / cadence

Cadence is source- and entity-specific. Examples:
- fast-changing upcoming titles: frequent scheduled checks;
- released catalogue records: slower refresh;
- historical archives: incremental/backfill cadence;
- official announcement feeds: event-driven when available;
- certification/release sources: increased cadence near expected release windows.

Exact schedules remain OPEN until source benchmarking and cost/rate-limit analysis are complete.

## Failure handling

Classify failures:
- transient network;
- rate limit;
- authentication/credential;
- source schema drift;
- parser-incompatible content change;
- removed resource;
- policy/terms suspension;
- permanent unsupported response.

Retries must use backoff and must not hammer providers. Policy/terms failures must disable/suspend the adapter rather than retry blindly.

## Discovery is not scraping permission

A discovery may come from a publicly visible page or secondary reference, but that does not authorize bulk ingestion/republication. Discovery can trigger research or lookup in another approved source.

## Control Room views required

- source health dashboard;
- adapter status and last successful run;
- discovery stream;
- acquisition jobs;
- failed/retrying/dead-letter jobs;
- rate-limit/quota usage;
- source schema-drift alerts;
- policy-suspended sources;
- per-source change volume;
- candidate discoveries awaiting downstream identity/reconciliation.

## Acceptance principle

The Discovery/Acquisition layer succeeds when it can find and retrieve evidence at scale **without becoming a hidden path around licensing, provenance or canonicalization rules**.
