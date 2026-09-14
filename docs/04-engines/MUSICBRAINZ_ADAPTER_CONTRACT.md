# MusicBrainz Adapter Contract — V1

**Status: LOCKED FOR INITIAL IMPLEMENTATION**  
**Date: 2026-09-14**

## Mission

Use only MusicBrainz data that is safely within the CC0 core boundary to strengthen CAS music, soundtrack, recording and artist identity without importing non-commercial supplementary data by accident.

# Allowed production inputs

Initial production ingestion may use:
- `mbdump.tar.bz2` CC0 core database dump;
- `mbdump-cdstubs.tar.bz2` if a future use case is explicitly approved;
- targeted web-service lookups for core metadata under service/rate-limit policy;
- other datasets only when their licence is separately verified as CC0 and added to this contract.

# Explicitly excluded from unlicensed production

Do not ingest into the commercial canonical store from:
- `mbdump-derived.tar.bz2`;
- `mbdump-edit.tar.bz2`;
- `mbdump-editor.tar.bz2`;
- `mbdump-stats.tar.bz2`;
- cover/event art dumps;
- annotations, tags, genre associations, ratings, edit history or derived statistics that belong to supplementary data;
- Live Data Feed replication packets under the default CC BY-NC-SA terms.

A future commercial MetaBrainz agreement may supersede these restrictions through a new source-policy version.

# Core entity mapping

MusicBrainz entities remain external-source entities mapped into CAS concepts.

Working mapping:
- MB Artist -> CAS Person and/or Organization candidate identity;
- MB Work -> CAS MusicalWork candidate;
- MB Recording -> CAS MusicRecording candidate;
- MB Release Group / Release -> soundtrack/music-release evidence;
- MB Track/Medium -> release sequencing/container evidence;
- MB artist credit -> source credit text and identity relationships;
- MB relationships -> MusicContribution / external relationship candidates when the relationship data is in core.

No MBID becomes the CAS primary key.

# Film/series linkage

MusicBrainz records do not automatically know our audiovisual Work identity.

Linkage may be established through:
- explicit soundtrack/release relationships;
- approved external IDs/URLs;
- title + artist + date signals;
- CAS editorial adjudication;
- evidence from official soundtrack/film credits.

Ambiguous soundtrack-to-film matches stay `HUMAN_REVIEW` or unresolved.

# Song semantics

CAS separates:
- `MusicalWork` — composition/song identity;
- `MusicRecording` — a specific recorded performance/version;
- `MusicContribution` — composer, lyricist, singer, performer, arranger etc.;
- `AudiovisualMusicUsage` — relationship between an AV Work/Version/Episode and music.

A MusicBrainz Recording must not be collapsed into the MusicalWork simply because names match.

# Multilingual soundtrack behavior

Different-language recordings can:
- share one underlying MusicalWork when evidence supports the same composition;
- have distinct lyric contributions/translations;
- have different playback singers;
- belong to different soundtrack Releases.

The adapter must not infer translated-song equivalence from track order/name similarity alone.

# Person vs organization identity

MusicBrainz Artist can represent people, groups and other entities. The adapter must map type/context before proposing CAS Person/Organization identity.

Unknown/ambiguous artist type is not silently forced into Person.

# Merge/redirect behavior

MusicBrainz IDs may be merged or redirected over time.

Rules:
- preserve the old ExternalIdentifier mapping/history;
- record redirect/replacement relationships where detected;
- do not merge CAS entities automatically solely because MusicBrainz merged records;
- feed changes to Identity Review when CAS evidence disagrees.

# Refresh strategy

Initial V1 strategy:
- consume a current CC0 full dump;
- refresh from newly published CC0 full dumps at least weekly where available;
- compare snapshots to create changed observations/Claims;
- targeted web-service refresh for active conflicts/priority music entities;
- no commercial reliance on the non-commercial Live Data Feed.

The official MusicBrainz documentation states complete snapshots are generated twice weekly; operational schedules may consume the newest successful snapshot available.

# Provenance

Each imported music observation stores:
- MusicBrainz source ID/MBID;
- entity/table/relationship origin;
- dump date/version;
- adapter version;
- licence class (`MB_CORE_CC0`);
- source policy version;
- mapped CAS semantic field/relation;
- transformation rule version.

The adapter must make it impossible for supplementary rows to enter through the `MB_CORE_CC0` path.

# Licence boundary test

CI/adapter tests must maintain an allowlist of core dump/table families.

Unknown/new tables fail closed:
`UNKNOWN_MUSICBRAINZ_TABLE -> DO_NOT_INGEST`

Never assume a newly observed MusicBrainz dataset is CC0 because some MusicBrainz data is CC0.

# Artwork

MusicBrainz metadata approval does not approve cover art.
Cover Art Archive/Event Art remains outside this adapter and must go through the CAS Asset Engine with separate rights/licence review.

# Quality acceptance before production

The MusicBrainz adapter is production-ready only after:
1. core/supplementary separation tests pass;
2. at least 50 Indian film-music validation cases across languages/eras are exercised;
3. MusicalWork vs Recording identity is preserved;
4. composer/lyricist/playback-singer roles do not collapse;
5. multilingual recordings do not create false Work merges;
6. merged/redirected MBIDs preserve CAS identity history;
7. soundtrack-to-film ambiguous matches require review;
8. provider loss does not delete CAS music identities.
