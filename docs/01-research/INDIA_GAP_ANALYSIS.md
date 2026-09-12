# India Gap Analysis — Research Foundation v0.1

**Status: WORKING**  
**Research date: 2026-09-12**

## Executive conclusion

The India opportunity is not "Bollywood coverage". The real challenge is representing Indian cinema as a multilingual, multi-industry, multi-version ecosystem where language, territory, dubbing, remakes, certification, release strategy, music credits, and regional history all matter.

Several existing products already solve pieces of this well. Moviebuff in particular demonstrates strong India-specific metadata; BookMyShow is strong for live theatrical discovery; OTTplay is strong for streaming discovery; NFDC-NFAI, Indiancine.ma and Cinemaazi are valuable historical/archival resources. The gap is the absence of one audited product that combines this depth with global coverage, source transparency, lifecycle history, and conflict-aware canonicalization.

## 1. India is not one cinema namespace

A schema that models only `country = India` and a single language field is inadequate.

Cinema and Series must independently represent:

- production country/countries;
- original language(s);
- simultaneously shot language versions;
- dubbed languages;
- market/territory;
- native-script title;
- romanized/transliterated title;
- alternate marketing title;
- release language;
- distributor by territory;
- certification by version/territory;
- soundtrack language and localized music assets where relevant.

### Required principle

**Language != country != market != version != release event.**

## 2. Original work vs multi-language production vs dub vs remake

This is one of the highest-risk identity problems for Indian cinema.

### Dubbed version
A dubbed version normally remains the same underlying audiovisual work, with a different language track and possibly localized titles/credits/marketing/release dates.

### Remake
A remake is a separately produced audiovisual work and receives its own canonical Work/Title identity, linked with `remake_of` or equivalent.

### Simultaneously produced multilingual work
Some Indian productions are shot in more than one language, sometimes with different takes, dialogue, supporting performers, edits, or release strategies. We must not force every such case into either "one title with a dub" or "two unrelated films". The data model needs a deliberate multilingual-production relationship and version policy.

### Bilingual/multilingual marketing claim
"Bilingual", "multilingual" and "pan-India" are marketing terms, not sufficient technical identity evidence. They must never determine canonical identity by themselves.

## 3. Native-script title + romanization

Indian users frequently search using:

- native script;
- English/Latin transliteration;
- phonetic misspellings;
- shortened titles;
- actor/director shorthand;
- dubbed/localized titles.

A Telugu film should be discoverable through both its Telugu-script title and common Latin-script forms. Search normalization must preserve original text while supporting transliteration-aware matching.

### Required fields

- `original_title`
- `original_title_script`
- `display_title`
- `localized_titles[]`
- `romanizations[]`
- `alternate_titles[]`
- title usage/territory/language/type

No transliteration should silently overwrite the native title.

## 4. Release dates are unusually easy to misrepresent

Indian releases often involve:

- festival premiere;
- domestic wide release;
- limited release;
- state/territory differences;
- multiple language versions;
- overseas premieres one day earlier/later;
- paid previews;
- postponed releases;
- re-releases;
- restored versions;
- OTT release after theatrical;
- satellite premiere;
- dubbed release months or years later.

A single `release_date` field cannot preserve this truth.

### India-specific release model requirement

A `ReleaseEvent` should capture at minimum:

- work/version identity;
- territory/country;
- sub-territory when materially useful;
- language version;
- release type;
- platform/venue/distributor;
- scheduled date;
- actual date;
- status (`announced`, `scheduled`, `postponed`, `cancelled`, `released`);
- source claim(s);
- confidence/evidence level.

## 5. CBFC should be modeled as structured regulatory data

India's Central Board of Film Certification currently lists the ratings:

- U
- UA 7+
- UA 13+
- UA 16+
- A
- S

The public Search Film interface exposes fields including film name, language, category, regional office, certificate number/date, certified length, producer/applicant, plot summary, and cast/credit details when available.

### Important source constraint

CBFC is an official high-authority source for certification facts, but the public search is CAPTCHA-gated and the site marks its content as all rights reserved. We did not identify a public bulk API. Therefore:

- CBFC is a **high-authority verification source**;
- production automation must not scrape around CAPTCHA/technical controls;
- bulk ingestion requires a permitted access route, agreement, open dataset, or carefully documented manual/admin workflow;
- certificate facts must be version-aware because altered/certified versions may differ.

## 6. Indian craft credits deserve first-class representation

Global consumer databases often prioritize top cast/director/writer. Indian film culture frequently cares deeply about additional roles.

Cinema and Series should make these structurally visible rather than burying them in untyped text:

- director;
- story writer;
- screenplay writer;
- dialogue writer;
- producer / co-producer / executive producer;
- cinematographer / director of photography;
- editor;
- music director / composer;
- background score composer when distinct;
- lyricist;
- playback singer;
- choreographer;
- action/stunt director;
- production designer / art director;
- costume designer;
- sound designer / re-recording mixer;
- VFX supervisor/studio;
- DI/colorist where reliable;
- publicity/design credits where meaningful.

Moviebuff demonstrates that India-oriented users can be served with detailed departments and even track-level lyricist/playback-singer metadata on some titles. Cinema and Series must at least match this depth when sources support it.

## 7. Music is part of film identity in India

For many Indian films, songs are not ancillary metadata; they are central cultural objects.

Long term, the model should support:

`Film -> Soundtrack/Album -> Track -> Composition/Lyrics/Playback Credits`

MusicBrainz is a potential open structured identity/source candidate for parts of this domain because its core database is CC0, though supplementary data has different licensing. This is not automatically V1 scope, but the data model should avoid blocking it.

## 8. Remake/adaptation graphs are strategically important

Indian cinema has extensive cross-language remake/adaptation networks. A user should be able to distinguish:

- original work;
- official remake;
- adaptation of the same literary source;
- dubbed version;
- sequel;
- spiritual sequel;
- reboot;
- spin-off;
- copied/inspired-by claim that lacks authoritative evidence.

### Rule

Relationships themselves are claims and require provenance.

We must not encode internet folklore such as "unofficial remake" as canonical without evidence and an appropriate relationship certainty/type.

## 9. Historical Indian cinema is fragmented across specialist sources

### NFDC-NFAI
Official archival institution and high-value authority for holdings, preservation and historical research.

### Indiancine.ma
Annotated research archive with more than 80,000 unique film links and a strong early-cinema focus. It explicitly says even a 15,000-title preservation goal would cover only a fraction of Indian feature-film production, which illustrates the scale and fragmentation of the historical problem.

### Cinemaazi
A regional, multilingual film-history project intended to chronicle tens of thousands of films and thousands of people, while acknowledging that historical data may be incomplete where credible sources are scarce.

### Consequence

Historical Indian cinema should have:

- uncertainty fields;
- approximate/partial dates;
- disputed credits;
- source notes;
- archive-holding relationships;
- lost/partially lost status;
- restoration/version records;
- provenance per claim.

"Unknown" is valid data. Guessing is not.

## 10. Current theatrical truth differs from catalogue truth

BookMyShow is valuable because it exposes what is actually listed/bookable in Indian cities and supports extensive language navigation. This is a different truth from a database's announced release date.

We should distinguish:

- `announced theatrical date`;
- `confirmed distributor date`;
- `tickets live`;
- `first observed showtime`;
- `actual release observed`.

A ticketing provider should never be our only historical authority, but it can be a powerful near-release corroboration signal if licensed/permitted.

## 11. Current OTT truth is highly temporal

A title can be:

- available with subscription;
- rent/buy;
- free with ads;
- bundled through a channel;
- present in another country but not India;
- removed temporarily;
- available in one dubbed language but not another.

OTT availability therefore belongs to a temporal `AvailabilityOffer` model rather than a static text field.

Preferred long-term sourcing is a licensed availability provider (for example, a JustWatch partnership) plus direct-platform evidence where appropriate.

OTTplay is useful market research but its terms prohibit scraping/copying and make it unsuitable as an assumed production-ingestion source.

## 12. Upcoming films require evidence tiers

Indian film news is highly rumor-driven. We must prevent rumor pages from becoming canonical titles too early.

Suggested lifecycle:

`LEAD -> DISCOVERED -> OFFICIALLY_ANNOUNCED -> PRE_PRODUCTION -> FILMING -> POST_PRODUCTION -> COMPLETED -> RELEASE_SCHEDULED -> RELEASED`

Alternative states:

`ON_HOLD`, `SHELVED`, `CANCELLED`, `STATUS_UNKNOWN`.

### Evidence tiers for future titles

1. **Official** — producer/studio/platform/distributor/creator announcement from a competent first party.
2. **Strongly corroborated** — multiple reputable independent trade/news sources with concrete production evidence.
3. **Unverified lead** — rumor/casting chatter/unnamed-source reporting; stays outside canonical catalogue until threshold is met.

## 13. Production-company identity is messy

Indian credits often contain:

- banner names;
- presenter names;
- individual producers;
- co-production entities;
- distribution labels;
- music labels;
- satellite/OTT partners;
- regional distributors.

These should not be flattened into one `studio` string.

Company role must be explicit:

- production company;
- presenter;
- financier;
- distributor;
- sales agent;
- broadcaster/network;
- streaming platform;
- music label;
- VFX/post-production vendor;
- other credited organization.

## 14. People identity and credit aliases

Indian performers/crew may be credited under:

- stage names;
- initials;
- mononyms;
- spelling variants;
- patronymic forms;
- transliterations;
- changed names.

`Person` and `Credit` need separate name concepts:

- canonical person name;
- aliases;
- native-script names;
- `credited_as` for a specific work;
- source-specific spelling.

Never merge two people solely because names match.

## 15. Certification, runtime and version must be linked

Runtime can differ between:

- festival cut;
- CBFC-certified theatrical version;
- overseas version;
- censored/altered cut;
- OTT version;
- director's cut;
- restored version.

Therefore runtime belongs to a manifestation/version context where evidence supports it, not only to the abstract work.

## 16. Historical date precision

Vintage Indian records may only support:

- year only;
- month/year;
- approximate year;
- conflicting dates.

The schema needs date precision, e.g.:

- exact date;
- month precision;
- year precision;
- circa/range;
- unknown.

Do not turn `1957` into an invented `1957-01-01`.

## 17. Regional browsing must be richer than language chips

Consumer UX should ultimately support cinema traditions/markets without hard-coding inaccurate equivalences.

Examples:

- Telugu cinema
- Tamil cinema
- Malayalam cinema
- Kannada cinema
- Hindi cinema
- Bengali cinema
- Marathi cinema
- Punjabi cinema
- Gujarati cinema
- Odia cinema
- Assamese cinema
- Bhojpuri cinema
- Manipuri cinema
- Tulu cinema
- Konkani cinema
- and others

But these are discovery facets, not replacements for normalized country/language/company/territory data.

## 18. What existing India products already do well

We must explicitly learn rather than underestimate competitors.

### Moviebuff
- native-script names;
- detailed craft departments;
- technical specs;
- certification;
- release events;
- some dub relationships;
- track/music metadata.

### BookMyShow
- language-first theatrical discovery;
- current showtime reality;
- city/cinema context.

### OTTplay
- India-specific OTT discovery and recommendation.

### NFDC-NFAI / Indiancine.ma / Cinemaazi
- historical preservation, archival context, regional cinema scholarship.

### Gap that remains
No audited product in this research phase appears to combine all of the following as the central product architecture:

**global catalogue + India-deep semantics + historical archives + upcoming-production lifecycle + source provenance + conflict preservation + canonical identity reconciliation + measured coverage.**

This is the gap Cinema and Series should pursue.

## India-specific V1 acceptance principles

Before V1 can freeze, the schema must successfully represent test cases covering:

1. a straightforward modern Hindi theatrical film;
2. a Telugu film with multiple dubbed releases;
3. a genuinely multilingual production;
4. a film remade across several Indian languages;
5. a pre-independence Indian film with incomplete metadata;
6. a lost/partially lost film;
7. a restored/re-released classic;
8. an upcoming film with date changes;
9. a shelved/cancelled project;
10. an OTT original film;
11. an Indian streaming series with seasons/episodes;
12. a title with new UA 7+/13+/16+ certification;
13. a film where theatrical/OTT runtimes differ;
14. a title with native-script and multiple romanized spellings;
15. a soundtrack requiring music director/lyricist/playback singer relationships.

## Locked direction proposed from this analysis

The following should move toward **LOCKED** status during data-model design:

- Native script is first-class.
- Transliteration is additive, never destructive.
- Language/country/market/version/release are separate concepts.
- Dub != remake.
- Multilingual productions need explicit modeling.
- Release dates are events, not one scalar field.
- CBFC certification is version-aware regulatory metadata.
- Historical uncertainty is modeled rather than guessed away.
- Craft credits use structured jobs/departments.
- Relationships require provenance.
- Future projects use an evidence-backed lifecycle.
- Current theatrical and OTT availability are temporal observations.

## Evidence base

This analysis used current official/public materials from CBFC and the Ministry of Information & Broadcasting, NFDC-NFAI, Indiancine.ma, Cinemaazi, Moviebuff, BookMyShow, OTTplay, and relevant global database/provider documentation. Source access/licensing decisions are tracked separately so that research usefulness is not confused with permission to ingest.
