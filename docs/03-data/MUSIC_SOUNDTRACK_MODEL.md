# Music & Soundtrack Model

**Status: WORKING**  
**Milestone: Research Foundation v0.1**

## Why Cinema and Series needs this
For many film industries—especially Indian cinema—music credits are core film metadata rather than peripheral trivia. A single film can have different composers for score and songs, multiple lyricists, many playback singers, language-specific song versions and soundtrack releases that do not map cleanly to one film-level `Music` credit.

V1 must support meaningful **track-level film music credits** without turning Cinema and Series into a general-purpose streaming/music service.

## Scope decision

### V1 MUST support
- film/episode-level score composer and music-department credits;
- soundtrack/song titles when trustworthy data is available;
- per-song composer/songwriter/lyricist credits;
- per-recording playback vocalist/performer credits;
- language/script/localized song titles;
- song/recording external IDs such as MusicBrainz identifiers, ISRC/ISWC where sourced;
- relationship of a song/recording to a Film/Series/Episode/Version;
- multiple language recordings/versions of a song without treating them as unrelated by default;
- provenance for every music fact.

### V1 DOES NOT require
- audio streaming/playback;
- synchronized lyrics text;
- full global discography completeness for every musician;
- user music playlists;
- music recommendation engine;
- royalty/accounting data;
- scraping Spotify/Apple Music or other consumer streaming apps;
- album-cover publication without a separate rights basis.

## Core entities

### MusicalWork
Represents the underlying musical composition/song as an intellectual/creative work.

Conceptual attributes:
- `musical_work_id`
- localized/native names through Name model
- language(s) where meaningful
- ISWC/external identifiers when known
- type (`SONG`, `THEME`, `SCORE_CUE`, `INSTRUMENTAL`, `OTHER`)
- provenance/identity status

A MusicalWork can have multiple recordings.

### MusicRecording
Represents a specific recorded performance/audio realization.

Conceptual attributes:
- `music_recording_id`
- `musical_work_id` nullable when unresolved
- title/name context
- language/audio-language context
- duration observations
- ISRC/external IDs where known
- recording/version kind (`ORIGINAL_FILM_RECORDING`, `DUB_LANGUAGE_RECORDING`, `REMIX`, `REPRISE`, `LIVE`, `OTHER`)
- evidence

This distinction follows a durable music-metadata principle: composition identity and recorded-audio identity are not the same thing.

### MusicContribution
Links Person/Organization to MusicalWork or MusicRecording with a normalized job and original source wording.

Important jobs include:
- composer / music composer
- songwriter
- lyricist
- playback singer / vocalist
- performer / instrumentalist
- arranger / orchestrator
- conductor
- music producer
- recording/mix/mastering roles where product value justifies them

`credited_as` behavior follows `CREDITED_NAME_PERSON_IDENTITY_MODEL.md`.

### AudiovisualMusicUsage
Links MusicalWork and/or MusicRecording to an audiovisual Work/Version/Episode.

Conceptual fields:
- AV Work/Version/Episode ID
- MusicalWork/Recording ID
- usage kind (`FEATURED_SONG`, `ORIGINAL_SONG`, `THEME`, `BACKGROUND_SCORE_CUE`, `SOURCE_MUSIC`, `END_CREDITS`, `OTHER`)
- sequence/order where officially meaningful
- language/version context
- source/evidence

V1 does not need frame-accurate cue sheets.

### SoundtrackRelease — bounded support
A soundtrack album/single release can be represented or externally mapped when required to source track order, label, catalog number or release date.

Full music-release modeling is not a V1 completeness requirement. When rich release identity is needed, MusicBrainz can remain the authoritative external mapping while CAS stores only the facts required for cinema discovery and provenance.

## Film-level vs track-level credits

### Film-level Credit
Use ordinary AV `Credit` for roles such as:
- score composer for the film;
- music director when the source credits the whole film;
- music supervisor;
- soundtrack producer at film level.

### Track-level MusicContribution
Use MusicalWork/Recording-level credits for:
- lyricist of one song;
- singer of one recording;
- composer of one song when soundtrack has multiple composers;
- performer/arranger specific to one track.

Do not infer track-level credit from a film-level role.

## Language-version rules

A translated/dubbed-language film song may represent:
1. the same MusicalWork with a new MusicRecording and translated/adapted lyrics;
2. a derivative MusicalWork when composition/lyrics identity materially changes;
3. an unrelated replacement song in that Version.

This is evidence-driven. Do not merge solely because melody/title positioning is similar.

For multilingual Indian productions, attach the relevant MusicRecording to the appropriate AV Version/Release context where evidence allows.

## Lyrics policy
Lyricist identity is metadata; lyric text is copyrighted creative content.

V1 stores:
- lyricist credit;
- song title/language;
- external/legal link where allowed.

V1 does **not** ingest or republish full lyrics without an explicit licensed/rightsholder path.

## Source strategy

### MusicBrainz — priority open candidate
MusicBrainz core data is CC0 and includes artists, labels, release groups, releases, recordings, musical works and relationships. It is suitable for test ingestion of fields verified to be in the CC0 core. Supplementary data remains excluded unless a compatible licence exists.

### Wikidata
Useful for cross-IDs, song/work identity, people and multilingual naming where populated.

### First-party film/music-label credits
Official soundtrack releases, liner-note equivalents, film end credits and rights-holder announcements are high-value evidence where access/reuse terms permit.

### CBFC / film certification evidence
May support film-level music/credit facts when exposed, but it is not assumed to provide full per-song metadata.

### Moviebuff/Cinemaazi and similar India sources
Useful reference/discovery where licensed/terms permit; no unauthorized production scraping.

## Search and product behavior
A user should eventually be able to discover:
- films where a person composed the score;
- films containing songs sung by a playback singer;
- songs in a specific film with their lyricists/singers;
- language versions of a song when known.

Search results must distinguish Person, AV Work and song/music entities clearly.

## Quality rules
- `music director` must not be normalized blindly to `score composer` if the source meaning is ambiguous;
- `composer`, `lyricist` and `playback vocalist` are distinct roles;
- soundtrack release artist is not automatically the film composer;
- label ownership/distribution is not creative authorship;
- missing track-level data does not invalidate otherwise complete film metadata;
- per-song completeness is measured separately from core AV-credit completeness.

## V1 acceptance criteria
1. one film can contain many MusicalWorks/Recordings;
2. one song recording can have many playback singers;
3. different songs in one film can have different lyricists/composers;
4. film score composer remains representable even when there is no track list;
5. multilingual song recordings can link to one AV Work through different Versions;
6. full lyrics are not required or copied;
7. MusicBrainz IDs remain external mappings, never CAS primary IDs;
8. music metadata has the same claim/provenance discipline as film metadata.

## Freeze implication
`MusicalWork`, `MusicRecording`, `MusicContribution` and `AudiovisualMusicUsage` are now **WORKING V1 conceptual entities**. The validation corpus must test them before the entity model is frozen. If evidence shows the scope is too broad, reduction requires an explicit documented decision rather than silently dropping Indian music-credit fidelity during implementation.
