# Release Event Model — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Purpose

Cinema and Series rejects the idea that a movie or episode has one universal `release_date`. Release is a temporal, territorial, versioned event domain.

This model must correctly represent worldwide premieres, Indian multilingual releases, postponements, festival screenings, re-releases, streaming launches, restorations and uncertain historical dates.

## Core invariant

**A Work may have zero, one or many ReleaseEvents. A ReleaseEvent is never the Work's identity.**

## ReleaseEvent identity

Create a durable ReleaseEvent when the occurrence/planned occurrence has independent meaning that must survive updates.

Conceptual identity dimensions:
- Work
- Version where relevant
- territory/market
- release type
- venue/platform/distributor context
- event sequence/identity

Two claims about different dates for the *same planned event* normally belong to one ReleaseEvent with scheduling history, not two independent events.

A theatrical release followed years later by a re-release is two ReleaseEvents.

## Required conceptual fields

- `release_event_id`
- `work_id`
- `version_id` nullable
- `territory_id`
- sub-territory/market nullable
- `release_type`
- venue ID/text nullable
- distributor organization ID nullable
- platform/broadcaster ID nullable
- release-language context nullable
- event status
- announced-at nullable
- scheduled date/time + precision nullable
- actual date/time + precision nullable
- local timezone nullable
- accessibility/public/private qualification where needed
- evidence/Claims
- audit timestamps

## Status model

- `DISCOVERED`
- `ANNOUNCED`
- `SCHEDULED`
- `POSTPONED`
- `CANCELLED`
- `OCCURRED`
- `PARTIALLY_OCCURRED` — rare, e.g. some territories/venues proceed while planned wider rollout changes; prefer splitting events where clearer
- `UNCERTAIN`

Status history is evidence-backed and auditable.

## Date model

A release date value must preserve precision:
- exact date/time
- day
- month
- year
- range
- approximate/circa
- unknown

Historical records must never convert a year-only date into January 1.

### Scheduled vs actual

`scheduled_date` answers: *when was this event planned to happen?*

`actual_date` answers: *when is there evidence it did happen?*

A scheduled date passing does not automatically set `actual_date`.

## Rescheduling

Example:

```text
Event CASR1: India theatrical release

2026-01-05: official claim -> scheduled 2026-08-07
2026-04-10: official claim -> postponed
2026-04-10: official claim -> scheduled 2026-08-14
2026-08-14: observed/official evidence -> occurred 2026-08-14
```

The product can display:

`Released 14 Aug 2026 · originally scheduled 7 Aug 2026`

No historical date is overwritten/deleted.

## Release type taxonomy

### Premiere/screening
- WORLD_PREMIERE
- INTERNATIONAL_PREMIERE
- NATIONAL_PREMIERE
- FESTIVAL_SCREENING
- PREMIERE_SCREENING
- PRESS_INDUSTRY_SCREENING where product value justifies
- ARCHIVAL_SCREENING
- RESTORATION_SCREENING

### Theatrical
- THEATRICAL_WIDE
- THEATRICAL_LIMITED
- THEATRICAL_GENERAL
- PAID_PREVIEW
- RE_RELEASE_THEATRICAL

### Broadcast/home
- TELEVISION_BROADCAST
- STREAMING_SUBSCRIPTION
- STREAMING_FREE_AD_SUPPORTED
- DIGITAL_RENTAL
- DIGITAL_PURCHASE
- PHYSICAL_MEDIA

Avoid excessive taxonomy until real corpus requires it. Provider-specific types are preserved in observations.

## Premiere semantics

`World premiere` is not simply `MIN(all known release dates)`.

A world-premiere claim should be supported by:
- official festival/producer/distributor statement;
- reliable archival/primary evidence;
- or a deterministic rule only when evidence coverage is sufficient and the UI labels it as earliest-known release rather than world premiere.

Distinguish:
- `WORLD_PREMIERE` — asserted/documented status;
- `EARLIEST_CONFIRMED_RELEASE` — derived database fact.

## Territory semantics

Release territory is mandatory for market release events unless the event is inherently global and evidence supports that.

Territory can be:
- country;
- subnational market where materially required;
- global/multi-territory group only when source event truly applies uniformly.

Do not create `Worldwide` as a shortcut for unknown territories.

## India-specific rules

### Language/version releases
One Work can have distinct Telugu, Tamil, Hindi, Malayalam, Kannada or other language ReleaseEvents when dates/distributors/versions differ.

If all language versions launch together and no meaningful event-specific metadata differs, one multi-language ReleaseEvent may be acceptable only if queries can still represent language availability accurately.

### Overseas dates
US/UAE/GCC/UK/Australia premieres/releases must not overwrite India theatrical dates.

### Paid premieres/previews
A paid preview the evening before general theatrical release is a separate event/type if relevant. It should not automatically redefine marketing release date without policy.

### Bookability as evidence
A ticketing listing can support near-term/current release observation through an approved provider path, but tickets-live is not itself identical to release occurrence.

### CBFC date
Certification date is a Certification fact, not a ReleaseEvent.

## Festival events

A festival event can contain:
- festival organization
- edition/year
- programme/section
- screening venue
- screening timestamp
- premiere designation
- Work/Version
- territory
- selection/award relationships separately

Selection is not release occurrence unless a screening actually happens.

## Series/episode releases

Episode ReleaseEvents must support:
- broadcaster/platform
- territory
- release pattern
- exact/approx date
- weekly release
- batch release
- split parts
- broadcast vs streaming dates

A globally marketed streaming date may still have timezone/date differences. Store source date semantics and timezone when relevant.

## Streaming launch vs availability

A streaming premiere is a ReleaseEvent.

Ongoing current availability is an `AvailabilityOffer`.

Example:
- Netflix premiere on 2026-05-01 -> ReleaseEvent
- Netflix India currently has title on 2026-09-12 -> AvailabilityOffer observation

If the title leaves and returns, the original release event remains; offers change.

## Re-release/restoration

A re-release creates a new ReleaseEvent linked to existing Work and appropriate Version.

A restoration can produce:
- Version = 4K restoration
- ReleaseEvent = restoration premiere at festival
- ReleaseEvent = restored theatrical release in territory A
- later AvailabilityOffer = streaming restoration

Do not create a new Work.

## Physical media

If included later, distinguish:
- territory/region
- format (Blu-ray/UHD/DVD/etc.)
- Version
- release date
- distributor/label

Technical SKU-level commerce is not core V1.

## Cancellation and non-occurrence

A cancelled scheduled event remains in history with `CANCELLED` status.

Do not delete it.

A postponed event with no new date remains `POSTPONED` and may have unknown next scheduled date.

## Duplicate event resolution

Two source records may describe the same ReleaseEvent.

Match signals:
- same Work/Version
- same territory
- same type
- same/similar venue/platform/distributor
- dates within plausible reschedule relationship
- source lineage

When uncertain, keep separate candidate events and review rather than merging destructively.

## Derived release projections

Client convenience values should be derived from ReleaseEvents under explicit policies:

- `primary_release_year`
- `first_release_date`
- `india_theatrical_date`
- `next_upcoming_release`
- `latest_re_release`
- `streaming_premiere_date`
- `released_status`

Each projection has a versioned derivation rule.

Example `primary_release_year` policy may differ by WorkKind and historical evidence. It must be documented before freeze.

## Event evidence labels

Release UI can show:
- OFFICIAL
- CONFIRMED
- STRONGLY_SUPPORTED
- CONFLICTING
- UNVERIFIED

Unverified rumor release dates should not populate ordinary calendar UI.

## Data-quality checks

Detect:
- actual date before impossible production milestones;
- same ReleaseEvent with mutually incompatible territories/versions;
- scheduled event marked occurred with no occurrence evidence;
- cancelled event still presented as upcoming;
- streaming availability incorrectly represented as permanent release;
- world premiere later than a stronger earlier confirmed public screening;
- re-release overwriting original year;
- certification date used as release date;
- year-only source falsely given day precision.

## Required validation cases

1. straightforward one-country theatrical film;
2. Indian film with one-day-earlier overseas premiere;
3. film postponed multiple times;
4. Telugu original plus later Hindi dub theatrical release;
5. simultaneous multilingual release;
6. festival premiere months before commercial theatrical release;
7. restoration 50 years later;
8. paid previews before general release;
9. Netflix global series batch release;
10. weekly broadcast series;
11. title scheduled but never released;
12. historical film with only year known;
13. disputed premiere date;
14. streaming premiere, removal, return;
15. director's cut released years later.

## Lock criteria

Move to LOCKED only when:
- validation corpus represents all cases above;
- canonical release projections are documented;
- identity model can deduplicate source release records;
- India multilingual release examples work without duplicate Works;
- streaming launch and availability are cleanly separate;
- performance plan can query upcoming/calendar views efficiently from PostgreSQL projections.
