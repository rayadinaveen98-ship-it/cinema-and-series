# Production Lifecycle Model — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series must represent films/series that are being developed, announced, produced, delayed, shelved, cancelled, completed and released without treating rumors as facts or losing history when status changes.

## Core principle

**Lifecycle is an event history. `current_status` is a derived projection.**

A mutable enum alone is insufficient because it cannot explain how a project moved from announced -> filming -> on hold -> resumed -> completed.

## Lead vs canonical Work

### Lead
A possible project discovered from insufficient evidence.

Lead sources may include:
- reputable trade report with unnamed sources;
- casting discussions;
- rights/development reports;
- social chatter;
- working-title references.

A Lead belongs to a discovery/research queue and is not automatically a public canonical Work.

### Canonical future Work threshold

Create/promote a canonical Work when there is sufficient evidence of a distinct audiovisual project, normally one of:
- competent first-party announcement;
- official platform/studio slate;
- regulator/production/film-commission evidence where reliable and permitted;
- multiple strong independent sources plus concrete production evidence;
- human review approving a historically documented project.

The exact automation threshold remains WORKING and must be tested.

## Lifecycle states

### DISCOVERED
A project has sufficient evidence to exist as a database entity but details/status remain incomplete.

### ANNOUNCED
A competent source publicly announces the project.

### DEVELOPMENT
Project is in active creative/business development but not yet sufficiently evidenced as pre-production.

### PRE_PRODUCTION
Preparation for production is materially underway.

### FILMING
Principal photography/active animation/production is underway.

For animation/non-live-action works, adapters may map source terminology into a more general `IN_PRODUCTION` event while preserving source wording.

### POST_PRODUCTION
Principal production is complete/substantially complete and editing/VFX/sound/post processes are underway.

### COMPLETED
A finished deliverable/version is credibly complete, regardless of whether a release is scheduled.

### RELEASE_SCHEDULED
At least one qualifying future ReleaseEvent is actively scheduled with sufficient evidence.

This is not mutually exclusive with post-production/completed in real life. Therefore lifecycle should use **dimensions/events**, while the UI can derive a simplified primary state.

### RELEASED
At least one qualifying public ReleaseEvent has occurred.

### ON_HOLD
Active progress is paused with potential continuation.

### SHELVED
The project is not currently proceeding toward release/production, but there is no definitive cancellation or a completed work may remain unreleased.

### CANCELLED
Competent evidence indicates the project in its then-current form will not proceed/release.

### STATUS_UNKNOWN
Existing evidence cannot establish current state.

## Why lifecycle cannot be a simple linear state machine

Real projects can:
- announce a date before filming;
- film, pause, restart;
- complete but remain unreleased;
- premiere at festival while awaiting commercial distribution;
- have one season released while next season is filming;
- be cancelled then revived years later;
- change title/director/cast/company;
- be re-developed into a materially different project.

Therefore store `ProductionEvent` history and derive product-facing states.

## ProductionEvent types

Initial vocabulary:
- PROJECT_DISCOVERED
- PROJECT_ANNOUNCED
- GREENLIT where explicitly evidenced
- DEVELOPMENT_ACTIVE
- PRE_PRODUCTION_STARTED
- CAST_ANNOUNCED
- DIRECTOR_ANNOUNCED
- PRODUCTION_COMPANY_ANNOUNCED
- PRINCIPAL_PHOTOGRAPHY_STARTED
- PRODUCTION_STARTED
- PRODUCTION_PAUSED
- PRODUCTION_RESUMED
- PRINCIPAL_PHOTOGRAPHY_COMPLETED
- POST_PRODUCTION_STARTED
- WORK_COMPLETED
- TITLE_CHANGED
- RELEASE_DATE_ANNOUNCED — also represented in ReleaseEvent domain; cross-link rather than duplicate truth
- PROJECT_ON_HOLD
- PROJECT_SHELVED
- PROJECT_CANCELLED
- PROJECT_REVIVED
- STATUS_CORRECTED

Avoid encoding every press update as a new taxonomy item. Source-specific wording is preserved separately.

## ProductionEvent conceptual fields

- `production_event_id`
- `work_id`
- event type
- event date/time + precision
- effective period nullable
- involved Person/Organization/Territory nullable
- source wording/note where rights permit
- evidence claims
- supersedes/corrects prior event nullable
- event status

## Product-facing primary status derivation

The UI may show one simplified status badge, derived by policy.

Illustrative precedence for unreleased film:
1. CANCELLED
2. SHELVED
3. ON_HOLD
4. RELEASE_SCHEDULED if completed/post and active date exists
5. COMPLETED
6. POST_PRODUCTION
7. FILMING
8. PRE_PRODUCTION
9. DEVELOPMENT
10. ANNOUNCED
11. DISCOVERED
12. UNKNOWN

This precedence is not yet LOCKED and must be validated against series/animation edge cases.

## Release state is separate

Production state and release state should not be collapsed.

Example:

```text
Production: POST_PRODUCTION
Release: India theatrical scheduled 2027-01-09
```

Or:

```text
Production: COMPLETED
Release: no confirmed release
```

Or:

```text
Production: RELEASED (season 1)
Series: renewed / season 2 filming
```

Series require season-level future-production records where evidence is season-specific.

## Project title changes

Title change must preserve history:

```text
Working title -> old announced title -> final title
```

Use Name records with types/validity plus ProductionEvents/Claims.

Do not create a new Work solely because the title changed.

## Cast/crew changes

Pre-release personnel announcements are claims/credit states.

A person can move through:
- ANNOUNCED
- REPORTED
- CONFIRMED
- WITHDREW/REPLACED
- FINAL_CREDITED
- NOT_CREDITED

Never delete an announced cast history merely because the final film changes.

## Director/company changes

Same principle as cast. Whether a major creative reset creates a new Work is an identity-resolution question, not an automatic lifecycle rule.

## Cancellation and revival

### Same Work revival
Use same Work if evidence indicates continuation/revival of the same project identity despite pause/cancellation.

### New Work
Create a new Work if the abandoned project is later independently rebooted/redeveloped into a materially distinct production. Link through relationship/history where relevant.

Identity review is mandatory for ambiguous long-gap revivals.

## Shelved completed films

A completed film can be SHELVED/unreleased. Therefore:
- `completed = true` and `released = false` can coexist;
- shelved status does not mean production never happened;
- later release creates new ReleaseEvent and status history.

## Rumor handling

Rumor is an evidence state, not a production lifecycle state.

Do not publish:
`Status: RUMORED`
inside the canonical production state model.

Instead:
- candidate Lead remains outside public catalogue; or
- a public `Unverified development report` layer could be added later as a newsroom feature, clearly separated from canonical database truth.

## Source authority by lifecycle event

### Strong direct evidence
- producer/studio/platform announcement;
- official slate;
- official production start/completion announcement;
- verified final credits/release;
- credible regulatory/film-office record where suitable.

### Strong secondary evidence
- major trade reporting with concrete production detail;
- multiple independent reputable sources.

### Weak evidence
- generic entertainment portals copying rumors;
- fan accounts;
- anonymous social posts.

Weak evidence can create Leads, not canonical status.

## Freshness

Future lifecycle data can become stale quickly.

Suggested monitoring:
- active filming/post/release-near projects: daily/event-driven where practical;
- announced distant projects: weekly/event-driven;
- on-hold/shelved: monthly/quarterly source recheck;
- released historical projects: stable/event-driven corrections.

The monitoring schedule belongs to operational source policy later.

## Series-specific lifecycle

Series should separate:
- overall Series status;
- Season status;
- Episode release state.

Possible Series projection concepts:
- ANNOUNCED
- IN_PRODUCTION
- RETURNING
- ENDED
- CANCELLED
- ON_HOLD
- UNKNOWN

Renewal is an event/claim, not proof a season is already filming.

A cancelled series retains all released seasons/episodes.

## Validation cases

1. officially announced film with no date;
2. movie announced, director changes, same project continues;
3. project starts filming then pauses;
4. shelved completed movie later sold/released;
5. announced film formally cancelled;
6. cancelled project revived with same team/title;
7. cancelled project rebooted years later as different production;
8. rumor never officially confirmed;
9. series renewed but next season not yet in production;
10. season filming while earlier season already released;
11. animation project where "principal photography" does not apply;
12. historical unfinished film;
13. production title changes twice;
14. announced actor replaced before filming;
15. release scheduled while post-production is ongoing.

## Quality checks

Detect:
- RELEASED with no qualifying occurred ReleaseEvent;
- FILMING based only on weak rumor evidence;
- CANCELLED event silently removed after revival;
- final title overwriting old title history;
- impossible state dates (filming completed before filming began) unless evidence conflict is explicitly flagged;
- series-level status incorrectly copied to every season;
- scheduled release treated as proof of completion/release.

## Lock criteria

Move to LOCKED only when:
- lifecycle events survive validation corpus;
- current-state derivation policy is deterministic and tested;
- Lead promotion rules prevent rumor pollution;
- series/season lifecycle distinction works;
- cancellation/revival identity rules integrate with Identity Resolution;
- source monitoring/freshness rules are feasible.
