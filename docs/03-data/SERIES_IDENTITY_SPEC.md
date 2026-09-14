# Series Identity Specification

**Status: WORKING**  
**Origin:** Validation Corpus finding F-02

## Problem

Long-running television can stop for years, return with new season numbering, change networks/platforms, reboot continuity, retain continuity, or be marketed as a new series while still belonging to the same narrative/program lineage.

A single `series_title + year` rule is not sufficient.

`Doctor Who` is the benchmark that exposed this requirement: the original television run began in 1963, ended its classic run in 1989, and returned in 2005 as a revival/continuation with new series numbering.

## Working V1 rule

Cinema and Series will distinguish **Series identity** from **franchise/program lineage**.

### Series
A specific produced television/episodic run with its own durable CAS identity, season/episode hierarchy and production identity.

### Lineage / franchise grouping
A broader relationship layer that can connect related Series entities without merging their season/episode hierarchies.

## Default split indicators

A revival/relaunch SHOULD usually receive a separate Series identity when several of these are true:
- long production/broadcast hiatus;
- season numbering restarts;
- production entity/network/platform structure materially changes;
- marketing/cataloguing treats it as a new/revived series;
- episode numbering restarts or provider ecosystems consistently identify a separate run;
- cast/creative reset is substantial;
- the new run needs an independent release/season hierarchy to avoid ambiguity.

No single signal is decisive by itself.

## Default keep-together indicators

A continuing season should usually remain under the same Series identity when:
- production is continuous or normally seasonal;
- numbering continues coherently;
- it is marketed as another season of the same show;
- cast/creative changes occur within normal series evolution;
- network/platform migration occurs without a relaunch/reset;
- no independent run identity is needed for season/episode integrity.

A platform/network change alone does not create a new Series.

## Relationship vocabulary

Working relationship types for separate Series entities:
- `continuation_of`
- `revival_of`
- `reboot_of`
- `remake_of`
- `adaptation_of`
- `spin_off_of`
- `same_franchise`

Exact relationship taxonomy must stay consistent with the broader Work relationship model.

## Doctor Who benchmark decision

**WORKING GOLD EXPECTATION:**

- The classic television run and the 2005 revival use separate Series identities for catalogue/season integrity.
- They are connected through a strong `revival_of` / `continuation_of` lineage relationship and shared franchise/program grouping.
- Public UX can present them together under the broader Doctor Who franchise/program while preserving distinct season numbering and CAS IDs.

This avoids both bad extremes:
1. flattening decades of incompatible season numbering into one ambiguous Series record;
2. treating the revival as unrelated to the original program.

Evidence:
- Official Doctor Who history: https://www.doctorwho.tv/news-and-features/13-doctor-who-dates-that-you-need-to-know
- Official 2005 revival retrospective: https://www.doctorwho.tv/news-and-features/20-years-of-new-who-how-series-1-remains-a-great-starting-point-for-new-doctor

## Reboot vs revival

### Revival
Returns a prior series/program with meaningful continuity or lineage preserved.

### Reboot
Restarts/reinterprets the property with substantially reset continuity or premise.

Both normally remain separate Series identities from the earlier run.

## Remake/adaptation

A country/language remake such as The Office (UK -> US) is a separate Series identity linked by `remake_of`/`adaptation_of`; identical title is irrelevant to identity.

## Season numbering

Season/series numbers are **presentation/order metadata**, not primary identity.

Each Season gets its own CAS ID and may carry:
- official number;
- display number;
- provider-specific numbering mappings;
- title/name;
- specials grouping;
- production code/order where available.

This allows providers to disagree about whether something is `Season 0`, `Specials`, `Series 14`, etc. without forcing CAS identity changes.

## Episode ordering

Episode identity is separate from display order. CAS should be able to retain:
- broadcast order;
- production order;
- streaming/platform order;
- DVD/home-video order where important.

One ordering may be canonical for a given context, but alternate order schemes are not duplicate Episodes.

## Specials

Specials may:
- belong to a Season;
- belong directly to a Series;
- be standalone Works linked to the Series;

The model should choose based on production/catalogue identity and evidence, not force every special into `Season 0`.

## Anthology complications

Anthology series still retain a Series identity even when cast/story continuity resets every episode/season. If an installment is also marketed/released as a standalone film, the Work/Version/relationship model must represent that separately rather than duplicating metadata blindly.

## Control Room review

Ambiguous revival/reboot/continuation cases route to Relationship/Identity Review with:
- old/new production timeline;
- season/episode numbering;
- official marketing language;
- production/network/company history;
- continuity notes where evidence is relevant;
- provider IDs only as supporting evidence, never decisive truth.

## Decision state

**WORKING ACCEPTED:** Series run identity is separate from franchise/program lineage. Long-gap revivals/reboots may be separate Series linked explicitly instead of being flattened or disconnected.

This rule must be challenged with additional corpus cases before V1 freeze.
