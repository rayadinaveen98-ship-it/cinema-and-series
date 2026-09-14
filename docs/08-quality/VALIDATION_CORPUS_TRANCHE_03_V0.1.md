# Validation Corpus — Tranche 03 v0.1

**Status: ACTIVE / PARTIAL**  
**Cases: VC-0061..VC-0100**  
**Milestone: Research Foundation v0.1**

This tranche completes the first **100-case evidence-seeded benchmark**. It targets combined/split works, restorations/reconstructions, cancelled/unreleased productions, censorship/cut history, specials, pseudonyms/person-name identity and international co-production/country semantics.

Evidence grades remain A/B/C. C-grade cases are intentionally retained as research seeds and must be upgraded or adjudicated before final gold-corpus freeze.

---

## VC-0061 — Kill Bill Vol. 1 / Vol. 2 / The Whole Bloody Affair
**Dimensions:** project split into released films, later combined presentation.  
**Expected CAS outcome:** Vol. 1 and Vol. 2 retain distinct released Work identities. `The Whole Bloody Affair` is a combined/compilation presentation linked to both and may require a `combined_version_of` / compilation Work decision rather than destructive merge.  
**Evidence:**
- A-adjacent — AMC official theatrical trailer says The Whole Bloody Affair unites Volume 1 and Volume 2 into a single epic with additional anime material: https://www.youtube.com/watch?v=OrPwePSAULE
**Status:** OPEN GOLD boundary (combined Version vs compilation Work).

## VC-0062 — Gangs of Wasseypur Part 1 / Part 2
**Dimensions:** long production split for release, two public film identities.  
**Expected CAS outcome:** two distinct released Works linked as parts of one larger production/story cycle; combined festival/presentation context must not merge their IDs.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Gangs_of_Wasseypur
**Gold note:** add Cannes/producer source.

## VC-0063 — Nymphomaniac Vol. I / Vol. II / director's cuts
**Dimensions:** two released volumes + longer cuts.  
**Expected CAS outcome:** Volume I and II remain distinct released Works; each may have theatrical/director Version records.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Nymphomaniac_(film)
**Gold note:** upgrade with Zentropa/distributor documentation.

## VC-0064 — The Disappearance of Eleanor Rigby: Him / Her / Them
**Dimensions:** same story/project recut from perspectives into multiple releases.  
**Expected CAS outcome:** schema must support closely related alternate narrative Works/Versions without collapsing title history.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/The_Disappearance_of_Eleanor_Rigby
**Status:** OPEN GOLD Work-vs-Version adjudication.

## VC-0065 — The Other Side of the Wind
**Dimensions:** unfinished production completed decades later, delayed first release.  
**Expected CAS outcome:** one Work with production history beginning in 1970, long `unfinished/on_hold` period, later completion/restoration and 2018 ReleaseEvent. Do not create a new 2018 Work because completion happened later.  
**Evidence:**
- A — Netflix says it was shot beginning in 1970, remained unfinished for decades and Netflix financed completion/restoration: https://about.netflix.com/en/news/netflix-acquiring-legendary-filmmaker-orson-welles-last-film-the-other-side-of-the-wind
- A — Netflix Media Center documents production 1970–1976 and later completion: https://media.netflix.com/en/only-on-netflix/80085566

## VC-0066 — Napoléon (1927) restoration/reconstruction history
**Dimensions:** fragmented source elements, multiple historical cuts, restoration reconstruction.  
**Expected CAS outcome:** original 1927 Work survives across many historical Versions; restoration is a Version/restoration event, not a new Work. Source elements and reconstruction rationale belong in preservation/version provenance.  
**Evidence:**
- B — BFI restoration history: https://www.bfi.org.uk/sight-and-sound/features/monumental-reckoning-how-abel-gances-napoleon-was-restored-full-glory
- B — BFI restored presentation: https://player.bfi.org.uk/rentals/film/watch-napoleon-pt-1-1927-online

## VC-0067 — The Apu Trilogy restorations
**Dimensions:** damaged negatives, restoration, three Works.  
**Expected CAS outcome:** Pather Panchali, Aparajito and Apur Sansar remain separate Works; restoration creates/restores Versions/assets, not replacement Works.  
**Evidence:**
- B — Criterion documents original negatives damaged by fire and later 4K restorations: https://www.criterion.com/current/posts/3550-restoring-the-apu-trilogy

## VC-0068 — Kummatty (1979) restoration
**Dimensions:** Indian archive restoration, source prints, preservation event.  
**Expected CAS outcome:** same 1979 Work + restored Version/assets + restoration/preservation event and institutions.  
**Evidence:**
- B — Film Heritage Foundation restoration project: https://filmheritagefoundation.co.in/kummatty-1979-restoration-project/

## VC-0069 — Thamp̄ (1978) restoration
**Dimensions:** no surviving original camera negative, restoration from surviving materials.  
**Expected CAS outcome:** Work exists independently of original-negative survival; preservation status can state missing OCN while restoration Version remains usable.  
**Evidence:**
- B — Film Heritage Foundation: https://filmheritagefoundation.co.in/thamp-1978-restoration-project/

## VC-0070 — Ishanou (1990) restoration
**Dimensions:** restoration from surviving 16mm negative + prints, Cannes restoration premiere.  
**Expected CAS outcome:** original Work + restored Version; restoration source elements tracked separately from release identity.  
**Evidence:**
- B — Film Heritage Foundation: https://filmheritagefoundation.co.in/ishanou-1990-restoration-project/

## VC-0071 — Batgirl — completed/near-completed but cancelled from release
**Dimensions:** cancelled unreleased film, production state vs release state.  
**Expected CAS outcome:** Work remains in database with `cancelled/unreleased` lifecycle state; absence of ReleaseEvent does not invalidate Work/cast/crew/production metadata.  
**Evidence:**
- C quoting studio statement — Warner Bros. Discovery decision not to release Batgirl: https://comicbook.com/dc/news/batgirl-cancelled-warner-brothers-shares-statement/
- C — WBD CEO comments: https://www.tvinsider.com/1055035/batgirl-canceled-hbo-max-warner-bros-discovery-statement/
**Gold note:** preserve WBD earnings-call transcript/primary filing if available.

## VC-0072 — Scoob! Holiday Haunt — cancelled before release
**Dimensions:** unreleased/cancelled production.  
**Expected CAS outcome:** separate Work with cancelled/unreleased state; must not be silently deleted merely because it never entered distribution.  
**Evidence:**
- C quoting studio statement alongside Batgirl: https://comicbook.com/dc/news/batgirl-cancelled-warner-brothers-shares-statement/

## VC-0073 — Time Machine (Indian unfinished film)
**Dimensions:** incomplete/shelved Indian production.  
**Expected CAS outcome:** Work can exist with `unfinished/shelved` history and partial credits even without final cut/release.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Time_Machine_(unfinished_film)
**Gold note:** seek Shekhar Kapur/producer archive evidence.

## VC-0074 — Marudhanayagam
**Dimensions:** high-profile Indian production halted for years, possible future revival claims.  
**Expected CAS outcome:** one Work with time-aware production-state claims; new revival announcement must update lifecycle, not create a duplicate Work.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Marudhanayagam
**Gold note:** build from Kamal Haasan/Raaj Kamal first-party timeline before freeze.

## VC-0075 — Paanch
**Dimensions:** certification/distribution problems, unreleased theatrically.  
**Expected CAS outcome:** Work identity and certification/release attempts remain even if ordinary theatrical ReleaseEvent is absent.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Paanch
**Gold note:** archival/CBFC/producer evidence needed.

## VC-0076 — Udta Punjab certification dispute
**Dimensions:** CBFC requested excisions, court intervention, final certification.  
**Expected CAS outcome:** one Work; proposed excisions/certification decisions are claims/events. If materially different certified edits circulate, they may be Version records. Legal/certification history must not become separate Work identity.  
**Evidence:**
- A/legal — Bombay High Court record includes CBFC excision/modification decision: https://indiankanoon.org/doc/116968980/
- A/legal — subsequent litigation references High Court certification outcome: https://indiankanoon.org/doc/178322470/

## VC-0077 — The Shining — US vs European theatrical cut
**Dimensions:** territory-specific cut/runtime.  
**Expected CAS outcome:** one Work with territory-specific theatrical Versions/ReleaseEvents; runtime is version-specific, not a single global scalar.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/The_Shining_(film)
**Gold note:** replace with Warner/BBFC/archival cut documentation.

## VC-0078 — Once Upon a Time in America — US shortened cut vs longer international versions
**Dimensions:** distributor recut, nonlinear restructuring, territory Version.  
**Expected CAS outcome:** one Work with multiple Versions tied to release territories/distributors.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Once_Upon_a_Time_in_America
**Gold note:** add studio/restoration/archive evidence.

## VC-0079 — Cinema Paradiso — theatrical vs longer director's cut
**Dimensions:** alternate cut with substantial additional story material.  
**Expected CAS outcome:** one Work, multiple Versions with version-specific runtime and content notes.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Cinema_Paradiso
**Gold note:** upgrade with distributor/Arrow/Criterion-like source.

## VC-0080 — Love, Death & Robots — provider `Volumes`
**Dimensions:** provider installment terminology, anthology, episode groups.  
**Expected CAS outcome:** Netflix `Volume 1..4` labels are preserved exactly but CAS must not globally assume `Volume == Season`. Episodes remain stable identities under provider-defined installment groupings.  
**Evidence:**
- A — Netflix title page labels the series `4 Volumes` and lists episode groups: https://www.netflix.com/title/80174608

## VC-0081 — Doctor Who Christmas/New Year specials
**Dimensions:** specials outside ordinary season hierarchy.  
**Expected CAS outcome:** special Episode/TV Special Works can link to the Series run without requiring a normal Season slot; chronology and broadcast order remain expressible.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/List_of_Doctor_Who_Christmas_and_New_Year%27s_specials
**Gold note:** replace with DoctorWho.tv episode-guide evidence.

## VC-0082 — Sherlock: The Abominable Bride
**Dimensions:** standalone special between ordinary series runs.  
**Expected CAS outcome:** special belongs to Sherlock Series identity but is not forced into a fabricated standard season episode number if official numbering treats it separately.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/The_Abominable_Bride
**Gold note:** add BBC archive source.

## VC-0083 — Euphoria special episodes between Seasons 1 and 2
**Dimensions:** bridge specials, nonstandard season placement.  
**Expected CAS outcome:** stable Episode/Special identities linked to Series and chronology; UI may group as Specials without mutating Season 1/2 membership.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Euphoria_(American_TV_series)#Specials
**Gold note:** add HBO episode pages.

## VC-0084 — Alan Smithee — shared professional pseudonym
**Dimensions:** pseudonymous credit, non-unique credited name.  
**Expected CAS outcome:** a credit string `Alan Smithee` must not automatically resolve to one durable Person. CreditDisplayName/pseudonym may map to different actual people depending on evidence and context.  
**Evidence:**
- A — Directors Guild interview describes removal of a director's name and use of the pseudonym Alan Smithee: https://www.dga.org/craft/dgaq/issues/1102-summer-2011/dga-interview-gil-cates
**Assertion:** credited-as string != unique Person identity.

## VC-0085 — Roderick Jaynes — one pseudonym for Joel + Ethan Coen
**Dimensions:** one credited editor identity represents multiple real people.  
**Expected CAS outcome:** `Roderick Jaynes` can be preserved as credited-as/pseudonym while canonical contribution links to Joel Coen and Ethan Coen as supported; system must permit one credit display identity to represent multiple people.  
**Evidence:**
- A — Academy database explicitly says Roderick Jaynes is a pseudonym for Joel Coen and Ethan Coen: https://awardsdatabase.oscars.org/Search/GetResults?query=%7B%22Nominee%22%3A%22Coen%22%2C%22Sort%22%3A%221-Nominee-Alpha%22%2C%22Search%22%3A%22Basic%22%7D
- B — BFI states `Roderick Jaynes [i.e. Joel Coen, Ethan Coen]`: https://www.bfi.org.uk/sight-and-sound/reviews/film-week-inside-llewyn-davis

## VC-0086 — Michael Keaton / Michael Douglas name collision
**Dimensions:** stage name adopted because another performer used a name.  
**Expected CAS outcome:** Person identity survives legal/birth/professional-name differences; no merge with actor Michael Douglas.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Michael_Keaton
**Gold note:** upgrade with reputable biographical/interview source.

## VC-0087 — Emma Stone / Emily Stone
**Dimensions:** professional name, same-name collision.  
**Expected CAS outcome:** one Person with name history/aliases; search for birth/professional name resolves same Person without conflating another Emily Stone.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Emma_Stone
**Gold note:** upgrade with first-party/interview evidence.

## VC-0088 — Rajinikanth / Shivaji Rao Gaekwad
**Dimensions:** Indian stage name and birth name.  
**Expected CAS outcome:** one Person; stage/professional name canonical for public display, birth name retained as evidence-backed alternate name.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Rajinikanth
**Gold note:** upgrade with official biography/award source.

## VC-0089 — Mammootty / Muhammad Kutty Panaparambil Ismail
**Dimensions:** stage name / legal-name identity.  
**Expected CAS outcome:** one Person with time/context-aware names; title credits preserve credited-as string.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Mammootty
**Gold note:** upgrade with official biography.

## VC-0090 — The Lunchbox — multiple production countries
**Dimensions:** international co-production, country vs language vs setting.  
**Expected CAS outcome:** Work can have multiple production-country relationships; `country` must not be one scalar and must not be inferred from setting/language.  
**Evidence:**
- B — BFI lists India, France, Germany, USA, Italy: https://www.bfi.org.uk/film/c929c368-7bb5-5710-8197-7678f169f55b/the-lunchbox

## VC-0091 — Gandhi (1982)
**Dimensions:** multinational production identity for India-centered film.  
**Expected CAS outcome:** production countries may include USA, India and UK while story/setting is primarily India; these dimensions remain separate.  
**Evidence:**
- B — BFI lists USA, India, United Kingdom: https://www.bfi.org.uk/film/0d8de71d-68e9-5682-a0b0-cc6d9be9bba8/gandhi

## VC-0092 — The Namesake (2006)
**Dimensions:** multinational production, diaspora story, multiple countries.  
**Expected CAS outcome:** production-country relation is many-to-many and independent of language/setting/national marketing.  
**Evidence:**
- B — BFI lists USA, India, Japan: https://www.bfi.org.uk/film/d91e7ccc-c0f5-58eb-909f-732e85efbb75/the-namesake

## VC-0093 — All We Imagine as Light
**Dimensions:** multinational Indian film, festival record vs other catalogs.  
**Expected CAS outcome:** multiple production countries supported with source claims; festival metadata can be authoritative for its submitted version but may differ from other catalogs.  
**Evidence:**
- A/B — Cannes lists France, India, Netherlands, Luxembourg: https://www.festival-cannes.com/en/f/all-we-imagine-as-light/
- B — BFI/Sight & Sound may list a broader set in later catalog contexts: https://www.bfi.org.uk/sight-and-sound/polls/50-best-films-2024
**Assertion:** country list can be source-disputed/expanded over time.

## VC-0094 — Monsoon Wedding — country attribution disagreement
**Dimensions:** source disagreement on country/co-production attribution.  
**Expected CAS outcome:** country relationships are claim-backed; CAS may canonicalize a set but preserve differing source lists.  
**Evidence:**
- B — BFI record lists USA, Italy, Germany, France: https://www.bfi.org.uk/film/eca8b1b9-fc89-521c-8d8a-a46ef49095ed/monsoon-wedding
- C/industry knowledge seed often describes India-linked production; further production-company evidence required.
**Gold note:** intentionally retained as conflict case rather than assuming one source is complete.

## VC-0095 — Money Heist original broadcaster structure vs Netflix international structure
**Dimensions:** episode re-edit/repartition, provider numbering.  
**Expected CAS outcome:** same underlying Series/episode material may have provider-specific episode/version mapping. CAS must be able to represent original-broadcast installments and international re-edits without duplicate Series identity.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Money_Heist
- A — Netflix provider structure lists five Parts: https://www.netflix.com/tudum/money-heist
**Gold note:** obtain Antena 3/source episode structure evidence.

## VC-0096 — Arrested Development Season 4 / Fateful Consequences remix
**Dimensions:** same season footage reorganized into a different episode structure.  
**Expected CAS outcome:** same Series and core Season lineage; Remix is a distinct season-level Version/edition with alternate Episode segmentation/order, not a new Series.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Arrested_Development_(season_4)
**Gold note:** add Netflix official remix announcement.

## VC-0097 — Twin Peaks original series vs The Return
**Dimensions:** long-gap continuation/revival, provider calls vs season terminology.  
**Expected CAS outcome:** Series-run identity and franchise relationship must support a later continuation that may be marketed as a limited series or third season without relying only on provider labels.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Twin_Peaks_(season_3)
**Status:** compare against Doctor Who series-run rule before gold freeze.

## VC-0098 — Neon Genesis Evangelion: Death & Rebirth
**Dimensions:** recap/compilation + new material, relation to TV series and End of Evangelion.  
**Expected CAS outcome:** distinct film Work/compilation linked to source Series/episodes and related later film; not a simple Season or dub.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Neon_Genesis_Evangelion:_Death_%26_Rebirth
**Gold note:** add official Evangelion archive evidence.

## VC-0099 — Berserk: Golden Age film trilogy -> Memorial Edition TV recut
**Dimensions:** film trilogy re-edited into episodic television edition.  
**Expected CAS outcome:** film Works remain distinct; Memorial Edition is a derivative Series/Version structure linked to the trilogy, not three new remakes.  
**Evidence:**
- C — https://en.wikipedia.org/wiki/Berserk:_The_Golden_Age_Arc
**Gold note:** add official anime production sources.

## VC-0100 — historical metadata conflict must remain representable
**Dimensions:** benchmark meta-case.  
**Expected CAS outcome:** for any of VC-0001..VC-0099, when competent sources conflict on country, runtime, language classification, cut identity, title effective date or season grouping, CAS stores both claims, records source competence and either canonicalizes transparently or routes to review. No benchmark is allowed to force destructive source erasure.
**Evidence:** the first 99 cases collectively.
**Assertion:** the claims/provenance model must be capable of representing the corpus before implementation freeze.

---

# New findings from Tranche 03

## F-14 — Preservation and restoration need source-element provenance
A restoration should be able to state what surviving negative/print/sound elements were used and which institutions performed/authorized the restoration.

## F-15 — Release absence is not Work absence
Batgirl, Scoob! Holiday Haunt and unfinished Indian productions require durable Work identity even with zero public ReleaseEvents.

## F-16 — Credited name cannot be the Person primary key
Alan Smithee and Roderick Jaynes prove both directions of ambiguity: one pseudonym may represent multiple people, and a professional/birth name can represent one person across many names.

## F-17 — Country is a relationship/claim, not a scalar
The Lunchbox, Gandhi, The Namesake, All We Imagine as Light and Monsoon Wedding demonstrate multinational and source-disputed country attribution.

## F-18 — Combined/split presentations need explicit relationship types
Kill Bill, Gangs of Wasseypur, Nymphomaniac and Eleanor Rigby expose the need for `part_of`, `combined_from`, `split_from`, `compilation_of` and/or Version-level equivalents.

## F-19 — Season/episode structures can themselves have Versions
Money Heist and Arrested Development require provider/edit-specific episode segmentation without resetting Series identity.

---

# First benchmark milestone reached

- Seed tranche: 20
- Tranche 02: 40
- Tranche 03: 40
- **Total: 100 / ~1,000 evidence-seeded hard cases**

This is **not** the final gold corpus. The next stage is to adjudicate the 100, upgrade weak evidence, convert expected outcomes into machine-readable assertions, and expand systematically to ~1,000 without padding the set with easy duplicate examples.
