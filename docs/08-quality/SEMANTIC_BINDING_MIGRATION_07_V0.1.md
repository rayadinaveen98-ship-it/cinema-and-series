# Semantic Binding Migration 07 v0.1

## Accepted CI
GitHub Actions run `34849971208` is GREEN.

## Scope
`validation/semantic/bindings-016.jsonl` and `reference-state-014.jsonl` migrate **15 gold music/credit cases / 30 corpus assertions** spanning:

- film-score vs song-level credit scope;
- composition vs recording identity;
- track-specific authorship;
- RRR/Naatu Naatu song credit scope;
- multilingual soundtrack recordings;
- score-cue vs song release packaging;
- translated soundtrack lyricist changes;
- vocal vs instrumental recording identity;
- multilingual Baahubali soundtrack releases;
- ANIMAL multi-composer/creator relationships;
- composer/lyricist/vocalist role separation;
- translated soundtrack localizations;
- recording-scoped playback singers;
- independent music vs audiovisual release histories;
- lyricist metadata vs full-lyric publication rights.

## Metrics
Before:
- runtime-ready: 337
- needs binding: 140
- reference cases: 96
- reference assertions: 243 PASS

After:
- runtime-ready: **368 / 481**
- needs binding: **109**
- manual/specialized: **4**
- reference cases: **111**
- reference assertions: **274 / 274 PASS**

## Cumulative movement from starting semantic baseline
- runtime-ready: **197 -> 368** (+171)
- binding debt: **280 -> 109** (-171)
- reference cases: **56 -> 111** (+55)
- reference assertions: **154 -> 274 PASS** (+120)

## Locked semantics reinforced
1. Credit scope is explicit: film, song/musical work, recording and release are not interchangeable.
2. A musical work and a concrete recording have different identities.
3. Translated/localized soundtrack releases do not create duplicate film Works.
4. Soundtrack/score packaging cannot restructure the audiovisual Work.
5. Playback/vocalist credits remain recording-scoped.
6. Music release dates and film theatrical dates are separate ReleaseEvent domains.
7. Reusable credit metadata does not imply rights to reproduce full lyric text.

No corpus assertion, evidence status or risk level was weakened to reach this state.
