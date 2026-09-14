# Validation Corpus — Tranche 04 v0.1

**Status: ACTIVE / PARTIAL**  
**Cases: VC-0101..VC-0115**  
**Primary focus:** Indian/film music and soundtrack semantics

This tranche validates the V1 `MUSIC_SOUNDTRACK_MODEL.md`. It deliberately tests distinctions that a film-level `music director` string cannot represent.

---

## VC-0101 — Slumdog Millionaire: score credit vs song credit
**Dimensions:** film-level score, track-level song, contributor-role scope.  
**Expected CAS outcome:** A.R. Rahman's film-level `Original Score` contribution is distinct from his song-level music contribution on `Jai Ho`; one does not replace the other.  
**Evidence:**
- A — Academy 2009 ceremony records A.R. Rahman as Original Score winner and separately credits `Jai Ho` Music by A.R. Rahman, Lyric by Gulzar: https://www.oscars.org/oscars/ceremonies/2009
**Assertion:** film Credit and MusicalWork contribution must coexist.

## VC-0102 — Jai Ho: composer/lyricist vs recording vocalists
**Dimensions:** MusicalWork vs MusicRecording, multiple vocalists.  
**Expected CAS outcome:** `Jai Ho` has composition-level music/lyric credits while a particular recording has several vocalists; singers are not inferred to be composers or lyricists.  
**Evidence:**
- A — Academy records Music by A.R. Rahman and Lyric by Gulzar: https://www.oscars.org/oscars/ceremonies/2009
- B — MusicBrainz soundtrack release records the Jai Ho recording with multiple vocalists and composition relationships: https://musicbrainz.org/release/dc01d08c-89c5-48c8-bfe0-5311387d584e
**Assertion:** contributor role and entity scope are independent.

## VC-0103 — O Saya and Jai Ho have different song-level authorship inside one film
**Dimensions:** track-specific credits, no blanket film-level lyricist inference.  
**Expected CAS outcome:** `O Saya` and `Jai Ho` are separate MusicalWorks/recordings with different authorship claims even though both belong to the same film soundtrack.  
**Evidence:**
- A — Academy lists `Jai Ho` music by Rahman/lyric by Gulzar and `O Saya` music and lyric by Rahman and Maya Arulpragasam: https://www.oscars.org/oscars/ceremonies/2009
**Assertion:** one film may contain tracks with different lyricists/writers.

## VC-0104 — RRR: Naatu Naatu song authorship vs film/score identity
**Dimensions:** Indian song-level composer/lyricist, film relation.  
**Expected CAS outcome:** `Naatu Naatu` is a MusicalWork/recording associated with RRR; M.M. Keeravaani is song music contributor and Chandrabose lyricist for this song. This does not imply every RRR cue/song has Chandrabose as lyricist.  
**Evidence:**
- A — Academy 2023 ceremony: `Naatu Naatu` from RRR; Music by M.M. Keeravaani; Lyric by Chandrabose: https://www.oscars.org/oscars/ceremonies/embed/2023
- A — Academy awards database search for Keeravaani preserves the historical credit wording: https://awardsdatabase.oscars.org/search/getresults?query=%7B%22Nominee%22%3A%22Keeravaani%22%2C%22Sort%22%3A%221-Nominee-Alpha%22%2C%22AwardShowNumberFrom%22%3A0%2C%22AwardShowNumberTo%22%3A0%2C%22Search%22%3A30%7D
**Assertion:** song credit attaches to the song, not indiscriminately to all film music.

## VC-0105 — RRR soundtrack contains multilingual realizations of a cue
**Dimensions:** soundtrack language realizations, same soundtrack/film lineage.  
**Expected CAS outcome:** Telugu/Hindi/Tamil/Kannada/Malayalam entries of `Together We Rock` can be represented as related MusicRecordings/language realizations, all associated with the same AV Work/Version lineage; they are not separate films.  
**Evidence:**
- B — MusicBrainz RRR Vol. 7 lists language-specific `Together We Rock` tracks in five languages: https://musicbrainz.org/release/d56b1890-d951-4bfb-b014-32df433f4c02
**Assertion:** soundtrack language versioning is distinct from AV Work identity.

## VC-0106 — RRR songs vs background-score cue releases
**Dimensions:** songs vs score cues, soundtrack release packaging.  
**Expected CAS outcome:** soundtrack album/release grouping can contain or separate score cues from songs; album packaging must not redefine the film's Work identity.  
**Evidence:**
- B — MusicBrainz RRR Vol. 4 lists score-style cues and credits M.M. Keeravaani as composer: https://musicbrainz.org/release/7eea5380-3d3d-4e1e-99a2-17ef42cfbff3
- B — MusicBrainz RRR Telugu soundtrack release: https://musicbrainz.org/release/07614c20-570d-45ee-8829-72c5ac2dd6a1/aliases
**Assertion:** soundtrack release structure and AV Work structure remain separate.

## VC-0107 — Roja Tamil vs Hindi soundtrack translation
**Dimensions:** translated song versions, lyricist changes, shared composition lineage.  
**Expected CAS outcome:** Tamil soundtrack and Hindi soundtrack are language releases related to the same film/music lineage. A translated song may retain composition relationship while changing lyrics/lyricist and recording vocal context.  
**Evidence:**
- B — MusicBrainz Tamil Roja lists A.R. Rahman composition and Vairamuthu lyrics for tracks: https://musicbrainz.org/release/30649153-1500-410f-9ecc-0199647f6d88
- B — MusicBrainz Hindi Roja lists P.K. Mishra as lyricist and marks Hindi release group as a translated version of Tamil Roja: https://musicbrainz.org/release/07770007-2281-4e1a-8fe8-bfc3bfb5f4da
**Assertion:** translated lyrics can create different contribution claims without forcing unrelated musical identity.

## VC-0108 — Roja: same film composition can have vocal and instrumental recordings
**Dimensions:** MusicalWork vs multiple recordings.  
**Expected CAS outcome:** instrumental and vocal recordings can relate to the same underlying composition while retaining distinct MusicRecording IDs and durations/performers.  
**Evidence:**
- B — MusicBrainz Hindi Roja release includes instrumental variants alongside vocal songs: https://musicbrainz.org/release/07770007-2281-4e1a-8fe8-bfc3bfb5f4da
**Assertion:** recording identity is not composition identity.

## VC-0109 — Baahubali soundtrack language releases
**Dimensions:** multilingual film soundtrack, language-specific singers/titles.  
**Expected CAS outcome:** Tamil and Hindi soundtrack releases attach to Baahubali: The Beginning without becoming separate AV Works; individual recordings/titles can differ by language.  
**Evidence:**
- B — MusicBrainz Tamil soundtrack release: https://musicbrainz.org/release/d03d3641-40e9-4a86-a286-92588e86faf4
- B — MusicBrainz Hindi soundtrack release: https://musicbrainz.org/release/5c4e1657-0c2a-427d-aa0d-da6fb65ac7bc
**Assertion:** soundtrack localization follows language/version model but remains independent of film identity.

## VC-0110 — ANIMAL: soundtrack has multiple composers/contributors
**Dimensions:** multi-composer soundtrack, invalid single `music_director` assumption.  
**Expected CAS outcome:** film soundtrack can associate many MusicalWorks/recordings with different composer/creator credits; no single person is inferred as composer of every track from album-level branding.  
**Evidence:**
- B — MusicBrainz ANIMAL release group lists multiple credited creators/composers and individual associated singles: https://musicbrainz.org/release-group/157f76af-a5d2-4ea0-8bfd-c65758066531
**Assertion:** music-credit model is many-to-many and track-scoped.

## VC-0111 — Arjan Vailly track-specific composer, lyricist and vocalist
**Dimensions:** track-level role separation.  
**Expected CAS outcome:** `Arjan Vailly` recording/work stores Manan Bhardwaj as composer, Bhupinder Babbal as lyricist and recording performer/vocal artist according to evidence; these roles are not collapsed.  
**Evidence:**
- B — MusicBrainz single/soundtrack record: https://musicbrainz.org/release/56d25921-9537-4a87-abfa-bbb768f441b0
**Assertion:** per-song role fidelity is required.

## VC-0112 — ANIMAL translated soundtrack editions
**Dimensions:** soundtrack localization, translated release group.  
**Expected CAS outcome:** Telugu/Tamil soundtrack editions are related language releases/recordings; they do not create new AV Work identities and can contain localized song metadata.  
**Evidence:**
- B — MusicBrainz ANIMAL deluxe/release group records translated soundtrack versions including Telugu/Tamil editions: https://musicbrainz.org/release/471e9b1f-1920-45a4-9023-9c5c33dd6318
**Assertion:** music release localization is modeled independently from film Work duplication.

## VC-0113 — Ala Vaikunthapurramuloo: one soundtrack, multiple playback singers
**Dimensions:** tracklist, per-track performers.  
**Expected CAS outcome:** one film soundtrack relation contains multiple recordings with distinct artist/vocalist credits such as Sid Sriram, Anurag Kulkarni/Mangli, Armaan Malik and others; singers are linked to recordings, not flattened into a single film-level vocalist list only.  
**Evidence:**
- B — MusicBrainz soundtrack tracklist: https://musicbrainz.org/release/5d185fe9-94f5-4666-95a4-ff02fb01d5ee
**Assertion:** track-level vocalist attribution must be representable.

## VC-0114 — soundtrack release date is not film theatrical release date
**Dimensions:** music release vs audiovisual ReleaseEvent.  
**Expected CAS outcome:** a SoundtrackRelease has its own issue date/territory and cannot overwrite the film's theatrical release date.  
**Evidence:**
- B — MusicBrainz Pushpa soundtrack records a worldwide soundtrack release event on 2021-08-13: https://musicbrainz.org/release/cd9a9d1b-d2d5-4b1c-8fbc-e2bc74584e4b/details
- B — MusicBrainz Baahubali Tamil soundtrack records a 2015-06-24 music release event: https://musicbrainz.org/release/d03d3641-40e9-4a86-a286-92588e86faf4
**Assertion:** music-product release event and film ReleaseEvent are distinct domains.

## VC-0115 — lyricist metadata vs copyrighted lyric text
**Dimensions:** rights boundary, metadata vs creative text.  
**Expected CAS outcome:** CAS can store `lyricist`, title, language and external identifiers while containing no requirement to ingest full lyric text. Lyrics content requires a separate licensed-rights path and must never be inferred as permitted because metadata is CC0/open.  
**Evidence:**
- A — Academy records lyricist metadata for `Jai Ho` and `Naatu Naatu` without supplying a reusable lyrics corpus: https://www.oscars.org/oscars/ceremonies/2009 and https://www.oscars.org/oscars/ceremonies/embed/2023
- B — MusicBrainz licensing distinguishes reusable core metadata from other content/licences: https://musicbrainz.org/doc/About/Data_License
**Assertion:** metadata rights do not grant lyric-text publication rights.

---

# Findings from Tranche 04

## F-20 — V1 needs composition and recording identity, not only film-level music credits
Indian soundtrack use cases require at least `MusicalWork` and `MusicRecording` conceptual identities.

## F-21 — music contributor roles are scope-specific
Score composer, song composer, lyricist and playback singer are distinct roles attached at different levels.

## F-22 — soundtrack language versions mirror—but do not equal—film Version identity
A Hindi soundtrack release or translated recording does not create a Hindi remake Work.

## F-23 — soundtrack release chronology is independent
Album/single release dates cannot populate or alter AV theatrical/streaming ReleaseEvents.

## F-24 — lyrics metadata and lyric text have different rights profiles
V1 can model lyricist credits without becoming a lyrics-republication product.

# Progress
- Previous evidence-seeded cases: 100
- Tranche 04: 15
- **Total evidence-seeded hard cases: 115 / ~1,000**

The next expansion should emphasize underrepresented quota areas rather than more music cases until the first 115 are classified into primary cohorts and evidence grades.
