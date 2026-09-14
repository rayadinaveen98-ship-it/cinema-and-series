# Organization Identity & Corporate History Model

**Status: WORKING**  
**Derived from validation cases:** VC-0054..VC-0058

## Problem
Film-company history is full of acquisitions, mergers, joint ventures, renames, labels, subsidiaries and platform consolidations. Destructive renaming would corrupt historical credits and make provenance false.

Cinema and Series must distinguish **organization identity** from **ownership/name history**.

## Core rule
Historical credits are time-bound facts. They retain the organization credited/competent at that time even if that organization is later renamed, acquired, merged or dissolved.

## Organization entity
A durable identity for a company, studio, label, broadcaster, platform operator, distributor, production house, archive or other relevant organization.

Working attributes:
- organization_id
- organization_kind(s)
- canonical/current display name
- status (`active`, `inactive`, `dissolved`, `merged`, `unknown`)
- jurisdiction/country where relevant
- external identifiers
- title/name history
- source claims

## Temporal organization relationships
Working relationship vocabulary:
- `owned_by`
- `acquired_by`
- `formed_from`
- `merged_into`
- `merged_with`
- `renamed_to`
- `formerly_known_as`
- `parent_of`
- `subsidiary_of`
- `joint_venture_of`
- `operates_brand`
- `successor_to`
- `predecessor_of`

Relationships should support:
- effective_from
- effective_to
- source/evidence
- confidence/dispute state

## Do not collapse these cases

### Acquisition
Amazon acquires MGM.
- MGM remains a historically meaningful Organization.
- ownership relation changes.
- prior MGM credits remain MGM.

### New company formed by combination
WarnerMedia + Discovery -> Warner Bros. Discovery.
- WBD receives its own identity.
- predecessor/formation relationships preserve lineage.
- old titles are not retroactively credited to WBD merely because WBD later owns assets.

### Merger / JV in India
Viacom18 + Star India -> JioStar.
- JioStar is modeled as resulting organization.
- historical Star India and Viacom18 credits remain historically accurate.

### Platform/service consolidation
JioCinema + Disney+ Hotstar availability/service history -> JioHotstar.
- streaming-service/platform identities are temporal distribution entities.
- a title observed on Disney+ Hotstar in 2023 remains historically recorded there even after later platform consolidation.

## Name changes
A true rename may preserve one Organization ID with time-bounded OrganizationName records.

A merger that creates a legally/operationally new company must not be represented as a simple rename unless competent evidence establishes continuity.

## Credits and rights
Credit/production/distribution/rightsholder relationships must record:
- the organization identity involved;
- role (`producer`, `distributor`, `studio`, `network`, `platform`, etc.);
- time/territory/version context where applicable;
- source provenance.

Corporate ownership is not itself proof that the parent company was the credited producer/distributor of every subsidiary title.

## Identity-resolution caution
Name similarity is weak evidence for organizations because:
- labels can share parent names;
- companies can reuse legacy brands;
- entities can change legal names;
- acquisition can preserve the acquired brand;
- multiple regional subsidiaries can coexist.

Automatic merges should therefore require strong registration/external-ID/official-corporate evidence.

## V1 acceptance criteria
- historical studio credit survives later merger/acquisition;
- Organization can have time-bounded names;
- Organization-to-Organization relations are temporal and provenance-backed;
- availability platform changes do not mutate old Release/Availability observations;
- parent ownership does not rewrite child-company credits.
