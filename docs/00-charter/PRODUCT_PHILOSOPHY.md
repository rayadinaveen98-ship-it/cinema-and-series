# Product Philosophy

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Foundational principles

### 1. Database before interface
A beautiful application cannot compensate for weak identity, incomplete provenance, duplicate works, incorrect releases, or source dependence. Product UI is downstream of the data model.

### 2. Evidence before assumption
Important metadata should be traceable to observations or sources. Uncertainty is data and must be modeled rather than hidden.

### 3. Canonical identity belongs to Cinema and Series
Every durable entity receives a Cinema and Series canonical identifier. IMDb, TMDB, Wikidata, TVDB, JustWatch, platform, festival, and other IDs are mappings, never primary identity.

### 4. Claims before destructive overwrites
The system should preserve competing source claims and select a canonical value through explicit rules. New ingestion cannot silently erase prior evidence.

### 5. Accuracy before quantity
One million poorly reconciled records are less valuable than a smaller corpus whose identity, releases, and provenance are trustworthy.

### 6. Coverage is measurable
Do not promise literal completeness. Measure coverage by territory, language, era, title type, and metadata dimension.

### 7. Indian cinema receives first-class modeling
Language, country, market, production origin, original language, dubbed language, release territory, native title, transliteration, remake relationship, and availability are separate concepts.

### 8. Release is an event
A work may have festival, theatrical, territory-specific, dubbed, digital, physical, re-release, restoration, and platform release events. Never reduce this to one global date.

### 9. Production is a lifecycle
Announced, pre-production, filming, post-production, completed, scheduled, released, on-hold, shelved, cancelled, and unknown states require history rather than one mutable label.

### 10. Artwork is not ordinary metadata
Every artwork asset needs source, provenance, usage basis/license information where applicable, retrieval metadata, and review state.

### 11. AI assists; evidence decides
AI may parse, normalize, propose matches, summarize conflicts, or prioritize review. It must not create unsupported canonical facts or silently merge uncertain entities.

### 12. History matters
Important canonical changes must be auditable and, when possible, recoverable. The product should be able to explain what changed and why.

### 13. Architecture should scale by extraction, not by premature complexity
Begin with strong modular boundaries and independent workers. Extract services only when scale or operational needs justify it.

### 14. Information is the luxury
The consumer design should feel like a premium cinematic archive, not a Netflix clone and not a generic database dashboard. Discovery should reveal relationships and evidence rather than merely maximize card clicks.

## Product behavior under uncertainty

When sources disagree, Cinema and Series should prefer:

1. preserving all relevant observations;
2. identifying source authority and recency;
3. selecting a canonical value only when rules justify it;
4. exposing a review queue where confidence is insufficient;
5. keeping conflict history rather than deleting it.

## Definition of success

Cinema and Series succeeds when users and maintainers can trust the identity of a work, understand its versions and relationships, inspect how and where it was released, and know why the database currently believes each important fact.
