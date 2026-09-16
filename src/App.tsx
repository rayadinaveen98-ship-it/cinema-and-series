import { Fragment, useEffect, useMemo, useState } from "react";

type Movie = {
  id: string;
  wikidataQid?: string;
  title: string;
  nativeTitle?: string;
  language: string;
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

type ApiResponse = {
  movies: Movie[];
  source: "d1" | "preview";
  generatedAt: string;
  catalogueUpdatedAt?: string;
  stats?: CatalogueStats;
};

const fallback: Movie[] = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", releaseDate: "2026-09-18", verificationStatus: "unconfirmed", releaseSource: "preview" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", releaseDate: "2026-09-19", verificationStatus: "supported", releaseSource: "preview" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", releaseDate: "2026-09-25", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", releaseDate: "2026-10-02", verificationStatus: "unconfirmed", releaseSource: "preview" },
];

const fallbackStats: CatalogueStats = { total: 4, verified: 1, supported: 1, unconfirmed: 2, activeSources: 0 };

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
  if (period === "all") return "All tracked releases";
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

export default function App() {
  const [movies, setMovies] = useState<Movie[]>(fallback);
  const [stats, setStats] = useState<CatalogueStats>(fallbackStats);
  const [source, setSource] = useState<ApiResponse["source"]>("preview");
  const [catalogueUpdatedAt, setCatalogueUpdatedAt] = useState<string>();
  const [activeLanguage, setActiveLanguage] = useState("All");
  const [activePeriod, setActivePeriod] = useState("upcoming");
  const [officialOnly, setOfficialOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [visibleCount, setVisibleCount] = useState(60);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/movies?scope=all", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Movie API unavailable");
        return response.json() as Promise<ApiResponse>;
      })
      .then((data) => {
        if (data.movies.length) setMovies(data.movies);
        if (data.stats) setStats(data.stats);
        setSource(data.source);
        setCatalogueUpdatedAt(data.catalogueUpdatedAt);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const today = todayKey();
  const sevenDayEnd = addDaysKey(today, 6);
  const thirtyDayEnd = addDaysKey(today, 29);
  const years = useMemo(
    () => Array.from(new Set(movies.map((movie) => movie.releaseDate.slice(0, 4)))).sort(),
    [movies],
  );
  const upcomingCount = useMemo(() => movies.filter((movie) => movie.releaseDate >= today).length, [movies, today]);
  const sevenDayCount = useMemo(
    () => movies.filter((movie) => movie.releaseDate >= today && movie.releaseDate <= sevenDayEnd).length,
    [movies, sevenDayEnd, today],
  );
  const thirtyDayCount = useMemo(
    () => movies.filter((movie) => movie.releaseDate >= today && movie.releaseDate <= thirtyDayEnd).length,
    [movies, thirtyDayEnd, today],
  );
  const yearCounts = useMemo(() => {
    const counts = new Map<string, number>();
    movies.forEach((movie) => counts.set(movie.releaseDate.slice(0, 4), (counts.get(movie.releaseDate.slice(0, 4)) ?? 0) + 1));
    return counts;
  }, [movies]);

  const periodMovies = useMemo(() => {
    if (activePeriod === "all") return movies;
    if (activePeriod === "upcoming") return movies.filter((movie) => movie.releaseDate >= today);
    if (activePeriod === "7d") return movies.filter((movie) => movie.releaseDate >= today && movie.releaseDate <= sevenDayEnd);
    if (activePeriod === "30d") return movies.filter((movie) => movie.releaseDate >= today && movie.releaseDate <= thirtyDayEnd);
    return movies.filter((movie) => movie.releaseDate.startsWith(`${activePeriod}-`));
  }, [activePeriod, movies, sevenDayEnd, thirtyDayEnd, today]);

  const confidenceMovies = useMemo(
    () => officialOnly ? periodMovies.filter((movie) => movie.verificationStatus === "verified") : periodMovies,
    [officialOnly, periodMovies],
  );

  const languages = useMemo(
    () => ["All", ...Array.from(new Set(confidenceMovies.map((movie) => movie.language || "Unknown"))).sort()],
    [confidenceMovies],
  );

  const filtered = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase();
    return confidenceMovies.filter((movie) => {
      const languageMatch = activeLanguage === "All" || (movie.language || "Unknown") === activeLanguage;
      const searchMatch = !query || movie.title.toLocaleLowerCase().includes(query) || movie.nativeTitle?.toLocaleLowerCase().includes(query);
      return languageMatch && searchMatch;
    });
  }, [activeLanguage, confidenceMovies, searchQuery]);

  const hero = useMemo(
    () => movies.find((movie) => movie.releaseDate >= today && movie.verificationStatus === "verified")
      ?? movies.find((movie) => movie.releaseDate >= today)
      ?? movies[0],
    [movies, today],
  );

  const visibleMovies = filtered.slice(0, visibleCount);
  const heroParts = hero ? dateParts(hero.releaseDate) : null;

  useEffect(() => {
    if (!languages.includes(activeLanguage)) setActiveLanguage("All");
  }, [activeLanguage, languages]);

  useEffect(() => {
    setVisibleCount(60);
  }, [activeLanguage, activePeriod, officialOnly, searchQuery]);

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
        <div className="hero-kicker">INDIA · RELEASE INTELLIGENCE</div>
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Next verified signal</p>
            <h1>{hero?.title ?? "Cinema, beautifully timed."}</h1>
            {hero && <p className="hero-date">{formatDate(hero.releaseDate)}</p>}
            <p className="hero-summary">A quiet, source-aware release calendar for Indian cinema. Open data builds the map; {stats.activeSources || "official"} first-party feeds strengthen the dates that matter.</p>
            <div className="hero-actions">
              <a href="#releases" className="primary-action">Browse the calendar</a>
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
              <span>{hero?.language || "Language pending"}</span>
              <span>{hero?.verificationStatus === "verified" ? `Official · ${movieSourceLabel(hero)}` : movieSourceLabel(hero)}</span>
            </div>
          </div>
        </div>

        <div className="signal-grid" aria-label="Catalogue status">
          <div className="metric"><span>Tracked</span><strong>{stats.total}</strong><small>curated dates</small></div>
          <div className="metric"><span>Next 30 days</span><strong>{thirtyDayCount}</strong><small>near-term releases</small></div>
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
            placeholder="Search a movie title…"
            aria-label="Search movie titles"
          />
          {searchQuery && <button onClick={() => setSearchQuery("")} aria-label="Clear search">Clear</button>}
        </div>

        <div className="filter-row" aria-label="Choose release period and confidence">
          <button className={activePeriod === "upcoming" ? "chip active" : "chip"} onClick={() => setActivePeriod("upcoming")}>
            Upcoming · {upcomingCount}
          </button>
          <button className={activePeriod === "7d" ? "chip active" : "chip"} onClick={() => setActivePeriod("7d")}>
            Next 7 days · {sevenDayCount}
          </button>
          <button className={activePeriod === "30d" ? "chip active" : "chip"} onClick={() => setActivePeriod("30d")}>
            Next 30 days · {thirtyDayCount}
          </button>
          {years.map((year) => (
            <button key={year} className={activePeriod === year ? "chip active" : "chip"} onClick={() => setActivePeriod(year)}>
              {year} · {yearCounts.get(year) ?? 0}
            </button>
          ))}
          <button className={activePeriod === "all" ? "chip active" : "chip"} onClick={() => setActivePeriod("all")}>
            All · {movies.length}
          </button>
          <button className={officialOnly ? "chip active" : "chip"} onClick={() => setOfficialOnly((value) => !value)}>
            Official only · {stats.verified}
          </button>
        </div>

        <div className="filter-row language-row" aria-label="Filter by language">
          {languages.map((language) => (
            <button
              key={language}
              className={language === activeLanguage ? "chip active" : "chip"}
              onClick={() => setActiveLanguage(language)}
            >
              {language}
            </button>
          ))}
        </div>
      </section>

      <section id="releases" className="release-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Release desk</p>
            <h2>{searchQuery ? `Results for “${searchQuery}”` : officialOnly ? `Official · ${periodLabel(activePeriod)}` : periodLabel(activePeriod)}</h2>
          </div>
          <p>{filtered.length} matching · {stats.verified} officially verified</p>
        </div>

        <div className="release-list">
          {visibleMovies.map((movie, index) => {
            const newMonth = index === 0 || monthKey(movie.releaseDate) !== monthKey(visibleMovies[index - 1].releaseDate);
            return (
              <Fragment key={movie.id}>
                {newMonth && (
                  <div className="month-divider">
                    <span>{monthLabel(movie.releaseDate)}</span>
                    <span>{filtered.filter((item) => monthKey(item.releaseDate) === monthKey(movie.releaseDate)).length} releases</span>
                  </div>
                )}
                <article className={`release-card ${movie.verificationStatus === "verified" ? "is-verified" : ""}`}>
                  <div className="date-block">
                    <span>{shortDate(movie.releaseDate).split(" ")[0]}</span>
                    <small>{shortDate(movie.releaseDate).split(" ")[1]}</small>
                  </div>
                  <div className="card-copy">
                    <div className="card-topline">
                      <span>{movie.language || "Language pending"}</span>
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

          {!filtered.length && (
            <div className="empty-state">
              <p className="eyebrow">No matching releases yet</p>
              <h2>Nothing in this slice.</h2>
              <p>Try another date window, year, language, confidence level, or search term while the source refresh continues to expand the calendar.</p>
            </div>
          )}
        </div>

        {visibleCount < filtered.length && (
          <button className="load-more" onClick={() => setVisibleCount((count) => count + 60)}>
            Show 60 more <span>{filtered.length - visibleCount} remaining</span>
          </button>
        )}
      </section>

      <section className="calendar-banner">
        <div>
          <p className="eyebrow">Source-aware by design</p>
          <h2>Open data finds it. Official evidence confirms it.</h2>
        </div>
        <div className="banner-copy">
          <p>Wikidata remains our discovery layer. Studio websites and verified official channels can promote a date to verified, while conflicting evidence stays preserved instead of disappearing.</p>
          <div className="confidence-key">
            <span><i className="key-dot verified" /> Official</span>
            <span><i className="key-dot supported" /> Supported</span>
            <span><i className="key-dot unconfirmed" /> Tracking</span>
          </div>
        </div>
      </section>

      <footer>
        <span>Cinema & Series</span>
        <span>India release desk · {stats.activeSources || "growing"} official sources</span>
      </footer>
    </main>
  );
}