import { Fragment, useEffect, useMemo, useState } from "react";

type Movie = {
  id: string;
  wikidataQid?: string;
  title: string;
  nativeTitle?: string;
  language: string;
  countryCode?: string;
  releaseDate: string;
  verificationStatus: "verified" | "supported" | "unconfirmed";
  releaseSource?: string;
  releaseSourceName?: string;
};

type CatalogueStats = {
  total: number;
  verified: number;
  supported: number;
  unconfirmed: number;
  activeSources: number;
};

type FacetValue = { value: string; count: number };
type CatalogueFacets = { years: FacetValue[]; languages: FacetValue[]; countries: FacetValue[] };
type Pagination = { limit: number; offset: number; total: number; hasMore: boolean };
type PeriodCounts = { upcoming: number; next7Days: number; next30Days: number };

type ApiResponse = {
  movies: Movie[];
  source: "d1" | "preview";
  generatedAt: string;
  catalogueUpdatedAt?: string;
  stats?: CatalogueStats;
  facets?: CatalogueFacets;
  pagination?: Pagination;
  periodCounts?: PeriodCounts;
};

const fallback: Movie[] = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", countryCode: "IN", releaseDate: "2026-09-18", verificationStatus: "unconfirmed", releaseSource: "preview" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", countryCode: "IN", releaseDate: "2026-09-19", verificationStatus: "supported", releaseSource: "preview" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", countryCode: "IN", releaseDate: "2026-09-25", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", countryCode: "IN", releaseDate: "2026-10-02", verificationStatus: "unconfirmed", releaseSource: "preview" },
];

const fallbackStats: CatalogueStats = { total: 4, verified: 1, supported: 1, unconfirmed: 2, activeSources: 0 };
const fallbackFacets: CatalogueFacets = {
  years: [{ value: "2026", count: 4 }],
  languages: [
    { value: "Kannada", count: 1 },
    { value: "Malayalam", count: 1 },
    { value: "Tamil", count: 1 },
    { value: "Telugu", count: 1 },
  ],
  countries: [{ value: "IN", count: 4 }],
};
const fallbackPagination: Pagination = { limit: 60, offset: 0, total: 4, hasMore: false };
const fallbackPeriods: PeriodCounts = { upcoming: 4, next7Days: 1, next30Days: 4 };

const countryNames: Record<string, string> = {
  IN: "India", US: "United States", GB: "United Kingdom", KR: "South Korea", JP: "Japan",
  FR: "France", DE: "Germany", IT: "Italy", ES: "Spain", CN: "China", HK: "Hong Kong",
  TW: "Taiwan", CA: "Canada", AU: "Australia", NZ: "New Zealand", BR: "Brazil", MX: "Mexico",
  AR: "Argentina", TR: "Turkey", IR: "Iran", PK: "Pakistan", BD: "Bangladesh", LK: "Sri Lanka",
  NP: "Nepal", ID: "Indonesia", TH: "Thailand", PH: "Philippines", NG: "Nigeria", EG: "Egypt",
};

function parseDate(value: string) {
  return new Date(`${value}T00:00:00+05:30`);
}

function dateKey(date: Date) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(date).map(({ type, value }) => [type, value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function addDaysKey(value: string, days: number) {
  return dateKey(new Date(parseDate(value).getTime() + days * 86_400_000));
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "long", year: "numeric" }).format(parseDate(value));
}

function shortDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short" }).format(parseDate(value));
}

function monthLabel(value: string) {
  return new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric" }).format(parseDate(value));
}

function monthKey(value: string) {
  return value.slice(0, 7);
}

function dateParts(value: string) {
  const date = parseDate(value);
  return {
    day: new Intl.DateTimeFormat("en-IN", { day: "2-digit" }).format(date),
    month: new Intl.DateTimeFormat("en-IN", { month: "short" }).format(date).toUpperCase(),
    year: new Intl.DateTimeFormat("en-IN", { year: "numeric" }).format(date),
  };
}

function todayKey() {
  return dateKey(new Date());
}

function formatFreshness(value?: string) {
  if (!value) return "syncing catalogue";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "catalogue live";
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function statusLabel(status: Movie["verificationStatus"]) {
  if (status === "verified") return "Officially verified";
  if (status === "supported") return "Supported date";
  return "Open-data tracking";
}

function periodLabel(period: string) {
  if (period === "upcoming") return "Upcoming releases";
  if (period === "7d") return "Next 7 days";
  if (period === "30d") return "Next 30 days";
  if (period === "all") return "All tracked films";
  return `${period} releases`;
}

function sourceLabel(source?: string) {
  if (!source || source === "wikidata") return "Wikidata candidate";
  if (source === "preview") return "Preview source";
  if (source === "official") return "Official source";
  return source.split("_").map((word) => word[0]?.toUpperCase() + word.slice(1)).join(" ");
}

function movieSourceLabel(movie?: Movie) {
  if (!movie) return "Source pending";
  return movie.releaseSourceName?.trim() || sourceLabel(movie.releaseSource);
}

function countryLabel(code?: string) {
  if (!code) return "Country pending";
  return countryNames[code] ?? code;
}

export default function App() {
  const [movies, setMovies] = useState<Movie[]>(fallback);
  const [hero, setHero] = useState<Movie | undefined>(fallback[2]);
  const [stats, setStats] = useState<CatalogueStats>(fallbackStats);
  const [facets, setFacets] = useState<CatalogueFacets>(fallbackFacets);
  const [pagination, setPagination] = useState<Pagination>(fallbackPagination);
  const [periodCounts, setPeriodCounts] = useState<PeriodCounts>(fallbackPeriods);
  const [source, setSource] = useState<ApiResponse["source"]>("preview");
  const [catalogueUpdatedAt, setCatalogueUpdatedAt] = useState<string>();
  const [activeLanguage, setActiveLanguage] = useState("All");
  const [activeCountry, setActiveCountry] = useState("All");
  const [activePeriod, setActivePeriod] = useState("upcoming");
  const [officialOnly, setOfficialOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const today = todayKey();
  const sevenDayEnd = addDaysKey(today, 6);
  const thirtyDayEnd = addDaysKey(today, 29);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(searchQuery.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  function buildCatalogueUrl(offset: number) {
    const params = new URLSearchParams({ limit: "60", offset: String(offset) });
    if (activePeriod === "all") {
      params.set("scope", "all");
    } else if (/^\d{4}$/.test(activePeriod)) {
      params.set("scope", "all");
      params.set("year", activePeriod);
    } else {
      params.set("scope", "upcoming");
      params.set("from", today);
      if (activePeriod === "7d") params.set("to", sevenDayEnd);
      else if (activePeriod === "30d") params.set("to", thirtyDayEnd);
      else params.set("to", addDaysKey(today, 730));
    }
    if (debouncedSearch) params.set("q", debouncedSearch);
    if (activeLanguage !== "All") params.set("language", activeLanguage);
    if (activeCountry !== "All") params.set("country", activeCountry);
    if (officialOnly) params.set("official", "1");
    return `/api/movies?${params.toString()}`;
  }

  function applyResponse(data: ApiResponse, append: boolean) {
    setMovies((current) => append ? [...current, ...data.movies.filter((movie) => !current.some((item) => item.id === movie.id))] : data.movies);
    if (data.stats) setStats(data.stats);
    if (data.facets) setFacets(data.facets);
    if (data.pagination) setPagination(data.pagination);
    if (data.periodCounts) setPeriodCounts(data.periodCounts);
    setSource(data.source);
    setCatalogueUpdatedAt(data.catalogueUpdatedAt);

    const isDefaultUpcoming = activePeriod === "upcoming" && activeLanguage === "All" && activeCountry === "All" && !officialOnly && !debouncedSearch;
    if (isDefaultUpcoming && data.movies.length) {
      setHero(data.movies.find((movie) => movie.verificationStatus === "verified") ?? data.movies[0]);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetch(buildCatalogueUrl(0), { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Movie API unavailable");
        return response.json() as Promise<ApiResponse>;
      })
      .then((data) => applyResponse(data, false))
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [activeCountry, activeLanguage, activePeriod, debouncedSearch, officialOnly]);

  const years = useMemo(() => facets.years.slice(0, 25), [facets.years]);
  const languages = useMemo(() => ["All", ...facets.languages.slice(0, 24).map((item) => item.value)], [facets.languages]);
  const countries = useMemo(() => ["All", ...facets.countries.slice(0, 20).map((item) => item.value)], [facets.countries]);
  const yearCounts = useMemo(() => new Map(facets.years.map((item) => [item.value, item.count])), [facets.years]);

  useEffect(() => {
    if (activeLanguage !== "All" && !facets.languages.some((item) => item.value === activeLanguage)) setActiveLanguage("All");
  }, [activeLanguage, facets.languages]);

  useEffect(() => {
    if (activeCountry !== "All" && !facets.countries.some((item) => item.value === activeCountry)) setActiveCountry("All");
  }, [activeCountry, facets.countries]);

  function loadMore() {
    if (loadingMore || !pagination.hasMore) return;
    setLoadingMore(true);
    fetch(buildCatalogueUrl(movies.length))
      .then((response) => {
        if (!response.ok) throw new Error("Movie API unavailable");
        return response.json() as Promise<ApiResponse>;
      })
      .then((data) => applyResponse(data, true))
      .catch(() => undefined)
      .finally(() => setLoadingMore(false));
  }

  const heroParts = hero ? dateParts(hero.releaseDate) : null;

  return (
    <main className="page-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="topbar">
        <a className="brand" href="/" aria-label="Cinema and Series home">
          <span className="brand-mark">C</span>
          <span>Cinema <em>&</em> Series</span>
        </a>
        <div className="topbar-meta">
          <span className={`live-dot ${source === "d1" ? "is-live" : ""}`} />
          {source === "d1"
            ? `${stats.activeSources} official sources · updated ${formatFreshness(catalogueUpdatedAt)}`
            : loading ? "Connecting…" : "Preview catalogue"}
        </div>
      </header>

      <section className="hero">
        <div className="hero-kicker">INDIA-FIRST · GLOBAL CATALOGUE</div>
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Next verified signal</p>
            <h1>{hero?.title ?? "Cinema, beautifully timed."}</h1>
            {hero && <p className="hero-date">{formatDate(hero.releaseDate)}</p>}
            <p className="hero-summary">A global movie catalogue with an India-first release desk. Open data builds breadth across countries and languages; {stats.activeSources || "official"} first-party feeds strengthen upcoming dates that matter.</p>
            <div className="hero-actions">
              <a href="#releases" className="primary-action">Browse the catalogue</a>
              <span className={`verification-pill ${hero?.verificationStatus ?? "unconfirmed"}`}>{hero ? statusLabel(hero.verificationStatus) : "Tracking"}</span>
            </div>
          </div>

          <div className="release-signal" aria-label={hero ? `Next tracked release: ${hero.title}` : "Release calendar"}>
            <div className="signal-topline">
              <span>Next signal</span>
              <span className={`signal-status ${hero?.verificationStatus ?? "unconfirmed"}`}>
                {hero?.verificationStatus === "verified" ? "Official" : "Tracking"}
              </span>
            </div>
            <div className="signal-date">
              <span>{heroParts?.day ?? "--"}</span>
              <div><strong>{heroParts?.month ?? "---"}</strong><small>{heroParts?.year ?? "----"}</small></div>
            </div>
            <div className="signal-rule" />
            <p className="signal-title">{hero?.title ?? "Release date pending"}</p>
            <div className="signal-meta">
              <span>{hero ? `${hero.language || "Language pending"} · ${countryLabel(hero.countryCode)}` : "Metadata pending"}</span>
              <span>{hero?.verificationStatus === "verified" ? `Official · ${movieSourceLabel(hero)}` : movieSourceLabel(hero)}</span>
            </div>
          </div>
        </div>

        <div className="signal-grid" aria-label="Catalogue status">
          <div className="metric"><span>Tracked</span><strong>{stats.total}</strong><small>movie titles</small></div>
          <div className="metric"><span>Next 30 days</span><strong>{periodCounts.next30Days}</strong><small>near-term releases</small></div>
          <div className="metric accent"><span>Official</span><strong>{stats.verified}</strong><small>verified dates</small></div>
          <div className="metric"><span>Sources</span><strong>{stats.activeSources}</strong><small>first-party feeds</small></div>
        </div>
      </section>

      <section className="catalogue-dock" aria-label="Catalogue controls">
        <div className="search-wrap">
          <span aria-hidden="true">⌕</span>
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search the full movie catalogue…"
            aria-label="Search movie titles"
          />
          {searchQuery && <button onClick={() => setSearchQuery("")} aria-label="Clear search">Clear</button>}
        </div>

        <div className="filter-row" aria-label="Choose release period and confidence">
          <button className={activePeriod === "upcoming" ? "chip active" : "chip"} onClick={() => setActivePeriod("upcoming")}>
            Upcoming · {periodCounts.upcoming}
          </button>
          <button className={activePeriod === "7d" ? "chip active" : "chip"} onClick={() => setActivePeriod("7d")}>
            Next 7 days · {periodCounts.next7Days}
          </button>
          <button className={activePeriod === "30d" ? "chip active" : "chip"} onClick={() => setActivePeriod("30d")}>
            Next 30 days · {periodCounts.next30Days}
          </button>
          {years.map(({ value: year, count }) => (
            <button key={year} className={activePeriod === year ? "chip active" : "chip"} onClick={() => setActivePeriod(year)}>
              {year} · {count ?? yearCounts.get(year) ?? 0}
            </button>
          ))}
          <button className={activePeriod === "all" ? "chip active" : "chip"} onClick={() => setActivePeriod("all")}>
            All · {stats.total}
          </button>
          <button className={officialOnly ? "chip active" : "chip"} onClick={() => setOfficialOnly((value) => !value)}>
            Official only · {stats.verified}
          </button>
        </div>

        <div className="filter-row language-row" aria-label="Filter by language">
          {languages.map((language) => (
            <button key={language} className={language === activeLanguage ? "chip active" : "chip"} onClick={() => setActiveLanguage(language)}>
              {language}
            </button>
          ))}
        </div>

        <div className="filter-row language-row" aria-label="Filter by country">
          {countries.map((country) => (
            <button key={country} className={country === activeCountry ? "chip active" : "chip"} onClick={() => setActiveCountry(country)}>
              {country === "All" ? "All countries" : countryLabel(country)}
            </button>
          ))}
        </div>
      </section>

      <section id="releases" className="release-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Catalogue desk</p>
            <h2>{searchQuery ? `Results for “${searchQuery}”` : officialOnly ? `Official · ${periodLabel(activePeriod)}` : periodLabel(activePeriod)}</h2>
          </div>
          <p>{pagination.total} matching · {stats.verified} officially verified</p>
        </div>

        <div className="release-list">
          {movies.map((movie, index) => {
            const newMonth = index === 0 || monthKey(movie.releaseDate) !== monthKey(movies[index - 1].releaseDate);
            return (
              <Fragment key={movie.id}>
                {newMonth && (
                  <div className="month-divider">
                    <span>{monthLabel(movie.releaseDate)}</span>
                    <span>catalogue slice</span>
                  </div>
                )}
                <article className={`release-card ${movie.verificationStatus === "verified" ? "is-verified" : ""}`}>
                  <div className="date-block">
                    <span>{shortDate(movie.releaseDate).split(" ")[0]}</span>
                    <small>{shortDate(movie.releaseDate).split(" ")[1]}</small>
                  </div>
                  <div className="card-copy">
                    <div className="card-topline">
                      <span>{movie.language || "Language pending"} · {countryLabel(movie.countryCode)}</span>
                      <span className={`status ${movie.verificationStatus}`}>{statusLabel(movie.verificationStatus)}</span>
                    </div>
                    <h3>{movie.title}</h3>
                    {movie.nativeTitle && movie.nativeTitle !== movie.title && <p className="native-title">{movie.nativeTitle}</p>}
                    <p className="source-line">
                      {movie.verificationStatus === "verified" ? `Official source · ${movieSourceLabel(movie)}` : `Discovery source · ${movieSourceLabel(movie)}`}
                    </p>
                  </div>
                  <div className="card-index">{String(index + 1).padStart(2, "0")}</div>
                </article>
              </Fragment>
            );
          })}

          {!movies.length && !loading && (
            <div className="empty-state">
              <p className="eyebrow">No matching films yet</p>
              <h2>Nothing in this slice.</h2>
              <p>Try another date window, year, language, country, confidence level, or search term while the catalogue backfill continues.</p>
            </div>
          )}
        </div>

        {pagination.hasMore && (
          <button className="load-more" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? "Loading…" : "Show 60 more"} <span>{Math.max(0, pagination.total - movies.length)} remaining</span>
          </button>
        )}
      </section>

      <section className="calendar-banner">
        <div>
          <p className="eyebrow">Two-layer data model</p>
          <h2>Open data gives us breadth. Official evidence gives us confidence.</h2>
        </div>
        <div className="banner-copy">
          <p>Wikidata expands the catalogue across languages, countries and film history. Studio websites and verified official channels remain the higher-trust layer for upcoming release dates, while conflicting evidence stays preserved instead of disappearing.</p>
          <div className="confidence-key">
            <span><i className="key-dot verified" /> Official</span>
            <span><i className="key-dot supported" /> Supported</span>
            <span><i className="key-dot unconfirmed" /> Tracking</span>
          </div>
        </div>
      </section>

      <footer>
        <span>Cinema & Series</span>
        <span>Global catalogue · India-first release desk · {stats.activeSources || "growing"} official sources</span>
      </footer>
    </main>
  );
}
