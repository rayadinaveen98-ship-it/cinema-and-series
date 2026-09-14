# Validation Corpus Seed v0.1

**Status: ACTIVE / PARTIAL**  
**Milestone: Research Foundation v0.1**

This is the first evidence-backed tranche of the ~1,000-case validation corpus. It is intentionally biased toward hard identity/version/release/history cases rather than popular titles.

Evidence here is for **benchmark expectation design**, not automatic production-ingestion permission. Source licensing rules remain governed separately by the Source Registry and Licensing Matrix.

## Evidence labels

- **A** — first-party / official / legal record directly competent for the claim.
- **B** — institutional/archive/film-preservation or similarly strong specialist source.
- **C** — reputable secondary/reference source, acceptable for benchmark discovery but preferably corroborated before final gold-label freeze.

---

## VC-0001 — Raja Harishchandra (1913)

**Dimensions:** historical cinema, silent film, archival coverage, early identity.  
**Expected modeling:** one historical Work; release year 1913; silent-film attributes must not require modern metadata fields; missing/partial surviving media must not invalidate the Work.  
**Evidence:**
- B — NFDC-NFAI digitized/restored films list includes `Raja Harishchandra`, Silent, 1913, D.G. Phalke: https://nfai.nfdcindia.com/pdf/Digitized%20and%20Restored%20Films_16-12-2016.pdf
- A/B — Directorate/NFDC National Film Awards catalogue describes Phalke directing India's first feature film, Raja Harishchandra, in 1913.

**Test:** historical entities must remain valid even when modern fields/artwork/complete credits are unavailable.

## VC-0002 — Alam Ara (1931)

**Dimensions:** lost film, first sound-film history, asset absence.  
**Expected modeling:** canonical Work exists even though the film itself is lost; `asset/media availability` must be independent of Work existence. The schema may require a future archival/preservation-status concept rather than abusing release/status fields.  
**Evidence:**
- B — Film Heritage Foundation: https://filmheritagefoundation.co.in/alam-ara-1931-hindi-urdu-124-mins/
- B — Film Heritage Foundation lost-heritage overview: https://filmheritagefoundation.co.in/indian-cinema-a-lost-heritage/

**Test:** no-poster/no-print/no-playback must not block identity, credits, release/history or search.

## VC-0003 — Vikram Vedha (2017 Tamil) -> Vikram Vedha (Hindi remake)

**Dimensions:** same title, different language, remake identity, same directors.  
**Expected modeling:** two distinct Works. Hindi Work has `remake_of` relationship to 2017 Tamil Work; identical title and returning directors must not trigger merge.  
**Evidence:**
- A — Reliance Entertainment 2018 media release explicitly announces a Hindi remake of the Tamil blockbuster: https://www.relianceentertainment.com/wp-content/uploads/Media_Release_Vikram.Vedha_15.03.18.pdf

**Test:** identity engine must prefer production/work lineage over title/director similarity.

## VC-0004 — Jersey (2019 Telugu) vs Jersey (2022 Hindi remake) vs Hindi-dubbed Telugu Jersey

**Dimensions:** remake vs dub, same title, same director, legal evidence, release history.  
**Expected modeling:** Telugu 2019 and Hindi 2022 are separate Works linked `remake_of`; the Hindi-dubbed version of the Telugu Work is a Version/manifestation of the 2019 Work, not the 2022 remake.  
**Evidence:**
- A — Bombay High Court record discusses Hindi remake rights and separately notes the Telugu film's Hindi dubbed version: https://indiankanoon.org/doc/50714159/

**Test:** this is a mandatory V1 dub-vs-remake benchmark. A system that collapses the dub and remake fails the case.

## VC-0005 — Premam (2015 Malayalam) -> Premam (2016 Telugu)

**Dimensions:** same title, cross-language remake, reused cast members.  
**Expected modeling:** separate Works linked by remake relationship; partial cast overlap must not cause merge.  
**Evidence:**
- C — reference page for 2016 Telugu film describes it as a remake of the 2015 Malayalam film: https://en.wikipedia.org/wiki/Premam_(2016_film)

**Gold-label note:** seek first-party/rights-holder corroboration before final corpus freeze.

## VC-0006 — Arjun Reddy -> Kabir Singh

**Dimensions:** remake with same director, changed cast/language.  
**Expected modeling:** separate Works; `Kabir Singh remake_of Arjun Reddy`. Same filmmaker must not collapse identities.  
**Evidence:**
- C — reference record notes Vanga remade Arjun Reddy in Hindi as Kabir Singh: https://en.wikipedia.org/wiki/Arjun_Reddy

**Gold-label note:** upgrade evidence before final freeze.

## VC-0007 — Arjun Reddy -> Varmaa / Adithya Varma

**Dimensions:** shelved/reworked remake production, related distinct Works, lifecycle.  
**Expected modeling:** production-history model must represent a remake attempt that was shelved/reworked and a later remake release without erasing the abandoned production history.  
**Evidence:**
- C — same Arjun Reddy reference documents Varmaa being shelved/relaunched as Adithya Varma and later Varmaa itself receiving a release: https://en.wikipedia.org/wiki/Arjun_Reddy

**Test:** lifecycle and identity history must survive cancellation/relaunch complexity.

## VC-0008 — Star Wars (1977) -> Star Wars: A New Hope title evolution

**Dimensions:** title history, same Work, re-release.  
**Expected modeling:** original 1977 Work remains one Work; later official title `Star Wars: A New Hope` is title history, not a new film. A later restored theatrical run is a new Version/ReleaseEvent as appropriate, not a new Work.  
**Evidence:**
- A — Lucasfilm states the classic 1977 theatrical release was later renamed `Star Wars: A New Hope`: https://www.starwars.com/news/star-wars-50th-anniversary-theatrical-release
- A — Lucasfilm production page: https://www.lucasfilm.com/productions/episode-iv/

**Test:** working/historical/current title identity must be time-aware.

## VC-0009 — Star Wars 2027 50th-anniversary restored re-release

**Dimensions:** restoration/re-release, same Work, future release event.  
**Expected modeling:** same underlying 1977 Work; restored presentation may create a Version; February 19, 2027 is a distinct theatrical ReleaseEvent.  
**Evidence:**
- A — StarWars.com official announcement: https://www.starwars.com/news/star-wars-50th-anniversary-theatrical-release

**Test:** `re-release != new Work` and future ReleaseEvent must coexist with historical 1977 events.

## VC-0010 — Doctor Who 1963 / 2005 revival

**Dimensions:** long-running TV identity, hiatus, revival, series boundary.  
**Expected modeling:** **OPEN GOLD DECISION** — corpus must force a documented V1 rule on whether classic and revived television runs use separate Series entities linked as continuation/revival or one umbrella Series with eras. Either way, episodes/seasons and search must preserve continuity without ID ambiguity.  
**Evidence:**
- A — official Doctor Who history records first episode on 23 Nov 1963 and Ninth Doctor return on 26 Mar 2005: https://www.doctorwho.tv/news-and-features/13-doctor-who-dates-that-you-need-to-know
- A — official site calls 2005 the show's return/revival and distinguishes the Classic Era: https://www.doctorwho.tv/news-and-features/20-years-of-new-who-how-series-1-remains-a-great-starting-point-for-new-doctor

**Test:** this case must be resolved before V1 freeze because it affects series identity architecture.

## VC-0011 — Black Mirror: Bandersnatch

**Dimensions:** interactive film/special connected to anthology series, mixed movie/TV classification.  
**Expected modeling:** standalone Work with explicit relationship to Black Mirror; the type system must not force everything related to a series into a normal numbered Episode. Interactive nature should be representable as metadata/format capability if retained in V1.  
**Evidence:**
- A — Netflix official title page labels Bandersnatch separately and classifies it across movie/TV/anthology descriptors: https://www.netflix.com/in/title/80988062

**Test:** work type and series relationship must support specials outside normal season/episode hierarchy.

## VC-0012 — The Office (UK) -> The Office (US)

**Dimensions:** TV format adaptation, same title, different series identity.  
**Expected modeling:** separate Series entities, US version linked as adaptation/remake of British original; same title must not merge.  
**Evidence:**
- C — Independent reporting on NBC commissioning an American remake after buying rights from the BBC/co-creators: https://www.independent.co.uk/news/media/american-tv-network-to-remake-the-office-despite-failure-of-pilot-563974.html

**Gold-label note:** seek BBC/NBC first-party archive confirmation before final freeze.

## VC-0013 — Dune (1984) vs Dune (2021)

**Dimensions:** two films adapted from same literary source, adaptation-vs-remake semantics.  
**Expected modeling:** two distinct Works. Both link to Frank Herbert's novel via `adaptation_of`; do **not** automatically infer `2021 remake_of 1984` merely because both adapt the same source.  
**Evidence:**
- B — AFI Catalog states 1984 Dune is based on Frank Herbert's novel: https://catalog.afi.com/Film/67647-DUNE
- A — Legendary production announcement states 2021 Dune is an adaptation of Frank Herbert's novel: https://www.legendary.com/dune-start-of-production/

**Test:** shared source material is not sufficient evidence for remake lineage.

## VC-0014 — A Star Is Born lineage (1937 / 1954 / 1976 / 2018)

**Dimensions:** repeated remake lineage, same title, multiple eras.  
**Expected modeling:** each film is a distinct Work; explicit remake/lineage relationships may connect versions. Search must disambiguate by year/cast while allowing grouped exploration.  
**Evidence:**
- C — reference summary identifies the 1954, 1976 and 2018 remakes of the 1937 film: https://en.wikipedia.org/wiki/A_Star_Is_Born_(1937_film)

**Gold-label note:** replace/augment with studio/archive evidence before final freeze.

## VC-0015 — Mr. Arkadin / Confidential Report multiple cuts

**Dimensions:** alternate cuts/versions, alternate title, same underlying Work.  
**Expected modeling:** one core Work with multiple Version records; alternate release title `Confidential Report` can be version/territory title context rather than forcing a separate Work.  
**Evidence:**
- B — Criterion documents multiple versions/cuts including Corinth, Confidential Report and comprehensive version: https://www.criterion.com/films/767-the-complete-mr-arkadin

**Test:** version-rich works must not create duplicate film identities.

## VC-0016 — The Last Emperor theatrical vs television version

**Dimensions:** mislabeled director's cut, version provenance, runtime conflict.  
**Expected modeling:** one Work with theatrical and television Versions; source labels must be preserved because a longer version historically marketed as a `director's cut` may not actually be the director-preferred version.  
**Evidence:**
- B — Criterion production notes explain the 165-minute theatrical/director-approved version and 218-minute television version: https://www.criterion.com/current/posts/720-final-cut

**Test:** runtime/cut labels must be claim-backed, not inferred from `longer = director's cut`.

## VC-0017 — Blade Runner (1982) Final Cut

**Dimensions:** alternate cut/version, later director-approved presentation.  
**Expected modeling:** Final Cut is a Version of the 1982 Work, not a new Work.  
**Evidence:**
- B/C — Criterion notes a 2007 `Final` cut of Ridley Scott's Blade Runner: https://www.criterion.com/current/posts/5477-the-daily-goings-on-farrokhzad-wenders-and-more

**Gold-label note:** add Warner/Ridley Scott first-party source before final freeze.

## VC-0018 — Apocalypse Now Final Cut

**Dimensions:** later cut/version, restoration/re-release.  
**Expected modeling:** Final Cut remains a Version of the 1979 Work with its own release/restoration events, not a new Work.  
**Evidence:**
- B — Criterion coverage records Francis Ford Coppola presenting his Final Cut of Apocalypse Now: https://www.criterion.com/current/posts/6486-il-cinema-ritrovato-2019

**Gold-label note:** add studio/American Zoetrope first-party evidence before final freeze.

## VC-0019 — Dune (1984) theatrical vs television edit

**Dimensions:** alternate edit, pseudonymous credits, same Work.  
**Expected modeling:** television edit is a Version of the 1984 Work. Version-specific credited-as/director/screenplay presentation may differ while canonical person identity remains David Lynch where evidence supports authorship/disavowal context.  
**Evidence:**
- B — AFI Catalog documents the later television edit and `Alan Smithee` / `Judas Booth` credits: https://catalog.afi.com/Catalog/moviedetails/67647

**Test:** credited-as names and version-specific credits must not create duplicate people or separate Works.

## VC-0020 — Historical archive records where surviving material is fragmentary

**Dimensions:** archive backfill, incomplete preservation, long-tail cinema.  
**Expected modeling:** CAS must support historical records with varying survival/completeness and must not score them as invalid merely because surviving footage/modern metadata is incomplete.  
**Evidence:**
- B — Film Heritage Foundation notes that only a small fraction of India's silent films survive and provides preservation context: https://filmheritagefoundation.co.in/preserving-our-film-heritage/
- B — NFDC-NFAI film-search/archive resources: https://nfai.nfdcindia.com/film-search.php

**Test:** quality metrics must distinguish `historically unknowable/lost` from `our ingestion is incomplete`.

---

# Findings already exposed by this seed

## F-01 — Preservation/survival status may need explicit modeling
`Alam Ara` and silent-film cases show that Work existence, asset availability and surviving-film status are different concepts. Before freeze, decide whether V1 needs fields/entities such as `preservation_status`, `survival_status`, `known_fragment_status` or an archival note/claim model.

## F-02 — Series revival identity needs a locked rule
`Doctor Who` demonstrates that Series identity across hiatus/relaunch/numbering conventions cannot be left to provider behavior.

## F-03 — Version-specific credited-as data matters
`Dune (1984)` television edit demonstrates that a Version can expose different credit strings/pseudonyms without changing underlying Person identity.

## F-04 — Adaptation and remake are not synonyms
`Dune 1984/2021` must not be linked as remake solely because both adapt the same book.

## F-05 — Human-friendly title grouping must not collapse canonical identity
`Vikram Vedha`, `Jersey`, `Premam`, `The Office` and `A Star Is Born` show that identical titles are common across distinct Works.

# Next corpus tranche

Expand from 20 to at least 100 cases covering:
- simultaneous multilingual productions;
- dubbed Indian theatrical versions;
- anthology films/series;
- anime original vs reboot vs remake;
- split films and combined releases;
- festival-only films;
- unreleased/cancelled/shelved productions;
- restored/reconstructed silent films;
- episode numbering/order disputes;
- pseudonyms and same-name people;
- territory-specific censorship/cuts;
- streaming-service season repartitioning;
- regional Indian title transliteration and native scripts.

This document is **not complete** until the full evidence-labeled corpus and expected results are frozen and reviewed.
