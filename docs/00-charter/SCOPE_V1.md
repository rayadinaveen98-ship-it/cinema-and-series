# V1 Scope

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

V1 is a trustworthy cinema/series database foundation, not a social entertainment super-app.

## V1 must model

### Core entities
- Movie / feature / short / special / other supported title types
- Series
- Season
- Episode
- Person
- Company / organization
- Credit
- Character / role association where supported
- Language
- Country / territory / market
- Genre and keyword taxonomy
- Title alias / localized name / native-script name / transliteration
- External identifier
- Relationship between works
- Release event
- Certification
- Production state and state history
- Media/artwork asset
- Source
- Source snapshot / observation
- Claim
- Canonical fact or canonical projection
- Change/audit history

## V1 must support

### Identity
- Cinema and Series canonical IDs
- External-ID mapping
- Candidate duplicate detection
- Merge review path
- Split/recovery path for incorrect merges

### Provenance
- Source-level traceability for imported material
- Field/claim-level evidence for important metadata
- Conflict preservation
- Source authority classification
- Retrieval/observation timestamps

### Localization
- Original/native title
- Alternate/localized titles
- Romanized/transliterated titles
- Original language
- additional/dubbed languages where applicable
- territory-aware names/releases

### Release model
- festival/premiere events
- theatrical events
- territory-specific events
- digital/streaming events where data rights permit
- physical-media/re-release/restoration events where available
- announced vs actual release dates
- reschedule history

### Production lifecycle
- discovered/candidate
- announced
- pre-production
- filming
- post-production
- completed
- release scheduled
- released
- on hold
- shelved
- cancelled
- unknown

### Relationships
At minimum the model must be capable of representing:
- sequel / prequel
- spin-off
- remake
- reboot
- adaptation
- franchise/universe membership
- alternate cut/version
- anthology relationships
- crossovers

### Search
- exact and fuzzy title search
- alias search
- native-script search
- transliteration-aware strategy for priority Indian languages
- person search
- filtering by language, country/market, date/year, title type, and core credits

### Administration and quality
- ingestion/source health visibility
- new-title candidate review
- duplicate review
- conflict review
- canonical override with reason
- missing-metadata/coverage reporting
- audit trail

## V1 quality requirement

The first production milestone is not defined by a target number of titles. It is defined by evidence that the system can correctly represent and reconcile a deliberately difficult validation corpus spanning:

- historical and modern cinema;
- multiple Indian languages;
- Hollywood and other world cinemas;
- films and episodic television;
- originals, remakes, dubs, adaptations, sequels, anthologies, and alternate versions;
- released, upcoming, delayed, shelved, and cancelled works;
- conflicting release dates and identities.

The exact corpus and pass criteria will be frozen in the QA specification.
