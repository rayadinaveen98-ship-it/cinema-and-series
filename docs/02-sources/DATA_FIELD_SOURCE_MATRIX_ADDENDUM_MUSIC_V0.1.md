# Data Field Source Matrix — Music/Soundtrack Addendum v0.1

**Status: WORKING**  
**Supersedes the older `track-level later if data exists` wording for the conceptual V1 capability.**

This addendum exists because validation cases VC-0101..VC-0115 demonstrated that Indian-cinema fidelity requires a bounded first-class soundtrack model. It will be merged into the main Data Field Source Matrix before V1 freeze.

## V1 capability vs completeness
V1 **must support** track-level music data structurally, but every film is not required to have a complete soundtrack before the title can exist or be considered core-metadata complete.

Music completeness is measured separately.

| Field/domain | Priority | Preferred evidence/source path | Secondary/fallback | Notes |
|---|---:|---|---|---|
| Film/episode score composer | P1 | A final credits / official score credits | B MusicBrainz where applicable; D/C | Ordinary AV Credit; distinguish score from songs |
| Film-level music director | P1 for India when credited | A final credits | D/C/B | Preserve source wording; do not blindly normalize to `score composer` |
| MusicalWork identity | P2 data coverage / P1 model capability | B MusicBrainz CC0 core + A official soundtrack/credit source | B Wikidata / H review | CAS ID remains primary; MBID external only |
| Song title | P2 coverage / P1 model capability | A soundtrack/film credits + MusicBrainz core | Wikidata/D licensed source | Name model supports script/language/localized variants |
| Song composer/songwriter | P2 coverage / P1 model capability | A liner/official credits + MusicBrainz core relationships | Wikidata/D/C | Attach to MusicalWork, not automatically film-wide |
| Lyricist | P2 coverage / P1 model capability | A soundtrack/film credits + MusicBrainz core where present | Wikidata/D/C | Track-specific; no lyric text implied |
| Playback vocalist / singer | P2 coverage / P1 model capability | A soundtrack/film credits + MusicBrainz recording relationships | Wikidata/D/C | Attach to MusicRecording where appropriate |
| MusicRecording identity | P2 coverage / P1 model capability | MusicBrainz core recordings/ISRC + A official release | Wikidata/H | Distinct from MusicalWork composition |
| ISRC | P2 | MusicBrainz core / label evidence | licensed music provider | External identifier only |
| ISWC | P2 | MusicBrainz core / rights society evidence where permitted | H | MusicalWork external identifier |
| Track duration | P2 | official music release / MusicBrainz recording/release | licensed provider | Recording/release-specific; not AV runtime |
| Soundtrack album/release identity | P2 | MusicBrainz core + A label/official release | Wikidata/licensed provider | Bounded CAS support; not full music-discography requirement |
| Soundtrack release date/territory | P2 | A label / MusicBrainz core | licensed provider | Never populate AV ReleaseEvent |
| Music label | P2 | A release credits + MusicBrainz core | Wikidata/D/C | Organization role, not authorship |
| Language-specific song recording | P2 | A soundtrack release + MusicBrainz | H | Link to AV Version when supported; do not create AV Work |
| Instrumental/reprise/remix relation | P2 | A official release + MusicBrainz relationships | H | Recording/version relationship |
| Full lyrics text | OUT OF V1 unlicensed path | licensed lyric/rightsholder provider only | none | Metadata licence does not authorize lyric text copying |
| Audio playback/file | OUT OF V1 | licensed streaming/rightsholder integration only | none | CAS is not a music streaming service |
| Album artwork | UX-only / P2 | rights-cleared provider/open licence | placeholder | Asset Engine rights gate mandatory |

## MusicBrainz policy
MusicBrainz is **GREEN only for fields verified as CC0 core data** under the reviewed licence. Supplementary NC/SA data must not leak into commercial canonical storage unless a compatible licence/contract is obtained.

Current official documentation confirms core entities include artists, labels, releases, recordings, musical works and relationships, with core data under CC0. Cover art is separate and not granted merely because metadata is CC0.

## Failure/fallback behavior
If MusicBrainz is incomplete for a film:
1. AV title remains valid;
2. film-level music credits can still come from final credits/official sources;
3. missing song metadata remains `unknown/not ingested`, not fabricated;
4. later evidence can add MusicalWorks/Recordings without changing AV Work ID;
5. source conflicts use ordinary Claims/CanonicalDecision behavior.

## Freeze tasks
Before V1 freeze:
- merge this addendum into main matrix;
- add music entities to the integrated Entity Model;
- classify VC-0101..VC-0115 into manifest format;
- test at least 50 Indian music-credit cases across languages/eras under corpus quota;
- verify MusicBrainz exact core-field membership used by any future adapter;
- keep lyrics/audio/artwork rights outside metadata assumptions.
