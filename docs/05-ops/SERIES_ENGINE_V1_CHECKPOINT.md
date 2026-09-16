# Series Engine V1 — Production Checkpoint

Date: 2026-09-16

## Production totals

- Movie catalogue titles: **8,150**
- SeriesRun titles: **2,500**
- Combined catalogue titles: **10,650**
- Exact-day movie rows: **2,736**

The movie count remained 8,150 across the first SeriesRun import. Series data is stored in dedicated `series_titles`, `series_seasons`, and `series_episodes` structures and does not overload movie rows.

## First SeriesRun bootstrap

GitHub Actions run: `Series Catalogue` run 1 (`35122736727`)

- Acquired/imported SeriesRuns: **2,500**
- SeriesRuns with Wikidata QID: **2,458**
- SeriesRuns with an explicit first-air year: **2,348**
- Country codes represented: **16**
- Language labels represented in this first slice: **4**
- Production D1 database after import: **4.60 MB**

### Country distribution

| Country | Titles |
|---|---:|
| India | 699 |
| United Kingdom | 506 |
| United States | 342 |
| Canada | 159 |
| China | 155 |
| Spain | 150 |
| South Korea | 129 |
| Japan | 108 |
| France | 69 |
| Australia | 59 |
| Brazil | 36 |
| Germany | 33 |
| Mexico | 32 |
| Pakistan | 13 |
| Turkey | 7 |
| Bangladesh | 3 |

### Language distribution

| Language label | Titles |
|---|---:|
| Unknown | 2,255 |
| Hindi | 220 |
| Malayalam | 23 |
| Kannada | 2 |

## Identity and precision quality

- Wikipedia page ID is the stable fallback identity.
- Wikidata QID is captured in the same MediaWiki discovery request whenever available; the first bootstrap achieved 2,458/2,500 QID coverage.
- First-air year is stored only when an explicit debut-year category supports it. Static language/web/miniseries categories never invent a year or exact air date.
- Obvious episode-list, season-number, and series-number pages are rejected as SeriesRun identities.
- Franchise/program lineage remains separate from SeriesRun identity per the existing series identity specification.

## Known V1 limitation / next series-quality slice

All 2,500 rows in the first bootstrap currently classify as generic `series`. The bootstrap reached its 2,500-title ceiling through broad television-series/debut categories before web-series/miniseries classification contributed production rows. This is a classification/coverage limitation, not a movie-vs-series identity problem.

Next quality work should therefore:

1. run dedicated web-series/miniseries classification/enrichment lanes;
2. expand Indian-language series category coverage beyond the first Hindi/Malayalam/Kannada slice, especially Telugu and Tamil;
3. enrich lifecycle state, season count, and episode count without changing SeriesRun identity;
4. add provider presentation mappings later as a separate layer rather than mutating canonical season structure.

## Live product

Production Worker: `https://cinema-and-series.rayadinaveen98.workers.dev`

Endpoints introduced with Series Engine V1:

- `/api/series`
- `/api/catalogue-stats`

The responsive Series shelf is part of the shared web experience and therefore appears in the Android WebView shell as well.
