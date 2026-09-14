# MusicBrainz Adapter Contract — Cinema and Series V1

**Status: LOCKED FOR V1 IMPLEMENTATION**  
**Date: 2026-09-14**

## Purpose

This contract defines exactly which MusicBrainz data Cinema and Series may ingest into production and how that data maps into the bounded V1 music model.

MusicBrainz is an **open music metadata source**, not CAS identity authority and not a music-streaming service.

# 1. Approved production source

Approved initial production input:
- `mbdump.tar.bz2` — the MusicBrainz **core** database dump explicitly published under CC0;
- targeted `/ws/2` Web Service lookups for bounded verification/enrichment within MusicBrainz usage policy and rate limits.

Official documentation reviewed:
- `https://musicbrainz.org/doc/About/Data_License`
- `https://musicbrainz.org/doc/MusicBrainz_Database`
- `https://musicbrainz.org/doc/MusicBrainz_Database/Download`
- `https://musicbrainz.org/doc/MusicBrainz_API`

# 2. Fail-closed licensing allowlist

Only dump files explicitly documented as compatible with our intended production use may enter the production adapter.

Approved baseline:
- `mbdump.tar.bz2` (CC0 core).

Explicitly **not** production-ingested without separate approval/licence:
- `mbdump-derived.tar.bz2`;
- `mbdump-edit.tar.bz2`;
- `mbdump-editor.tar.bz2`;
- `mbdump-stats.tar.bz2`;
- `mbdump-cover-art-archive.tar.bz2`;
- `mbdump-event-art-archive.tar.bz2`;
- supplementary annotations/tags/ratings/search indexes/derived statistics;
- Live Data Feed replication packets under the non-commercial/share-alike path unless a commercial agreement explicitly permits our use.

If MusicBrainz changes dump composition/licensing, the adapter stops rather than assuming compatibility.

# 3. V1 entity envelope

The core adapter may create candidate Claims/mappings for data needed by:
- `MusicalWork`;
- `MusicRecording`;
- Artist/Person/Organization identity signals;
- soundtrack `ReleaseGroup` / `Release` identity;
- track/medium structure;
- work-recording relationships;
- composer/lyricist/performer/vocal and other relationship types where represented in approved core relationship tables;
- label/area/date/language metadata where present in core;
- MBIDs, ISRC/ISWC and other approved identifiers/URLs from core data.

CAS remains free to model fewer MusicBrainz concepts than MusicBrainz itself; provider schema must not leak directly into public CAS APIs.

# 4. Core semantic distinction

The adapter must preserve the MusicBrainz distinction that aligns with CAS:
- **MusicalWork** = composition/song-level creative work;
- **MusicRecording** = distinct recorded audio realization;
- **Release/track** = publication/carrier context for a recording.

Do not collapse a composition and every recording of it into one entity.

A film soundtrack release is also not the film itself.

# 5. Film/series linkage

MusicBrainz data does not automatically know which audiovisual Work in CAS a song/recording belongs to in the semantic way our product requires.

Links to Film/Series/Episode/Version must therefore come from:
- explicit approved external relationships/identifiers;
- authoritative soundtrack/film credits;
- CAS editorial adjudication;
- corroborated identity rules.

Title similarity alone must never attach a soundtrack to a film.

# 6. Relationship mapping

MusicBrainz relationship types are versioned provider concepts. The adapter maps only allowlisted relationship UUIDs/types into CAS music contribution predicates.

Examples of CAS targets:
- composed_by;
- lyrics_by;
- performed_by;
- vocals_by;
- recording_of;
- arrangement/adaptation relation where semantically safe;
- label/release relationships.

Unknown relationship types remain raw/Observation data until explicitly mapped.

# 7. External IDs and merges

MBIDs are external identifiers only.

Rules:
- CAS Person/MusicalWork/MusicRecording IDs use CAS UUIDv7;
- MBID merge/redirect history does not change CAS IDs;
- canonical MusicBrainz redirect/mapping updates the ExternalIdentifier mapping/history;
- conflicting MBID-to-CAS mappings trigger review;
- no CAS entity merge occurs solely because MusicBrainz merged provider entities.

MusicBrainz documentation explicitly warns that canonical MBIDs can change after merges, reinforcing this requirement.

# 8. Refresh model

Initial production strategy:
- download/verify CC0 core snapshot on a regular cadence aligned with MusicBrainz dump publication (currently generated multiple times per week; V1 may process at least weekly initially);
- store dump date/checksum/adapter version;
- run idempotent delta-by-snapshot reconciliation inside CAS;
- use targeted Web Service requests only for bounded lookups/verification.

We do **not** require commercial Live Data Feed access for V1 baseline.

# 9. Web Service policy

When using `/ws/2`:
- send an identifying User-Agent;
- obey the documented default limit of approximately one request per second unless a different agreement exists;
- retry 503/throttling responses with backoff;
- never use the API as an uncontrolled high-volume crawler when a dump is the appropriate path.

# 10. Genre/tag boundary

MusicBrainz user tags/genre associations belong to supplementary/derived data and are not part of the approved CC0 baseline.

CAS must not quietly import MusicBrainz genre/tag associations through an alternate endpoint and thereby bypass the licensing boundary.

Film genres remain governed by CAS's own audiovisual taxonomy/source strategy.

# 11. Cover art boundary

MusicBrainz core data does not grant CAS rights to cover art.

Cover Art Archive imagery and related mappings require separate asset-rights review. The MusicBrainz adapter may expose an external reference for admin discovery only where policy allows; publication still goes through the Asset Engine.

# 12. Lyrics boundary

The V1 model can store:
- song title;
- language;
- lyricist credit;
- identifiers/relationships;
- rights-cleared metadata.

It must not ingest/copy full copyrighted lyric text merely because a music source mentions or links to it.

# 13. Quality/trust behavior

MusicBrainz core is community maintained. Its data becomes Claims/evidence and passes through identity/canonicalization.

Strong film-credit or official soundtrack evidence may override or contextualize MusicBrainz where conflicts exist.

The adapter must preserve disambiguation text/relationship context useful for identity without promoting provider wording into unsupported CAS truth.

# 14. Adapter Definition of Done

The production adapter must prove:
- checksum/licence-file allowlist enforcement;
- excluded dump files cannot enter production ingestion accidentally;
- resumable/idempotent snapshot import;
- Artist/Work/Recording/Release relationships retain provider IDs and provenance;
- MBID redirect/merge safety;
- film-to-soundtrack linking requires explicit evidence/rule, not title-only matching;
- no direct canonical writes;
- reprocessing is deterministic under adapter version;
- Web Service rate-limit/User-Agent policy is enforced;
- music validation cohort passes.

# 15. Failure/provider-loss behavior

If MusicBrainz becomes unavailable:
- CAS music IDs and accepted Claims survive subject to policy;
- refresh state becomes stale/degraded;
- no CAS Film/Person/MusicalWork identity is deleted because an MBID disappears;
- future reconciliation resumes after source recovery/review.

The initial MusicBrainz integration is therefore useful but **replaceable and non-authoritative by architecture**.
