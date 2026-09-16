import { useEffect, useMemo, useState } from "react";

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
  posterUrl?: string;
  backdropUrl?: string;
  artworkSource?: string;
  artworkSourceUrl?: string;
};

type CatalogueStats = { total: number; verified: number; supported: number; unconfirmed: number; activeSources: number };
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
  { id: "preview-1", title: "RANABAALI", language: "Telugu", countryCode: "IN", releaseDate: "2026-10-16", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-2", title: "KING", language: "Hindi", countryCode: "IN", releaseDate: "2026-12-24", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-3", title: "Jailer 2", language: "Tamil", countryCode: "IN", releaseDate: "2026-10-15", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-4", title: "Spirit", language: "Telugu", countryCode: "IN", releaseDate: "2027-03-05", verificationStatus: "supported", releaseSource: "preview" },
];
const fallbackStats: CatalogueStats = { total: 4, verified: 3, supported: 1, unconfirmed: 0, activeSources: 0 };
const fallbackFacets: CatalogueFacets = {
  years: [{ value: "2026", count: 3 }, { value: "2027", count: 1 }],
  languages: [{ value: "Telugu", count: 2 }, { value: "Hindi", count: 1 }, { value: "Tamil", count: 1 }],
  countries: [{ value: "IN", count: 4 }],
};
const fallbackPagination: Pagination = { limit: 60, offset: 0, total: 4, hasMore: false };
const fallbackPeriods: PeriodCounts = { upcoming: 4, next7Days: 0, next30Days: 2 };

const countryNames: Record<string, string> = {
  IN: "India", US: "United States", GB: "United Kingdom", KR: "South Korea", JP: "Japan", FR: "France", DE: "Germany",
  IT: "Italy", ES: "Spain", CN: "China", HK: "Hong Kong", TW: "Taiwan", CA: "Canada", AU: "Australia", NZ: "New Zealand",
  BR: "Brazil", MX: "Mexico", AR: "Argentina", TR: "Turkey", IR: "Iran", PK: "Pakistan", BD: "Bangladesh", LK: "Sri Lanka",
  NP: "Nepal", ID: "Indonesia", TH: "Thailand", PH: "Philippines", NG: "Nigeria", EG: "Egypt",
};

function parseDate(value: string) { return new Date(`${value}T00:00:00+05:30`); }
function dateKey(date: Date) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" })
    .formatToParts(date).map(({ type, value }) => [type, value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}
function addDaysKey(value: string, days: number) { return dateKey(new Date(parseDate(value).getTime() + days * 86_400_000)); }
function todayKey() { return dateKey(new Date()); }
function formatDate(value: string) { return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" }).format(parseDate(value)); }
function yearOf(value: string) { return value.slice(0, 4); }
function countryLabel(code?: string) { return !code ? "Global" : countryNames[code] ?? code; }
function sourceLabel(source?: string) {
  if (!source || source === "wikidata") return "Wikidata";
  if (source === "official") return "Official source";
  if (source === "preview") return "Preview";
  return source.split("_").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}
function artworkSourceLabel(source?: string) {
  if (!source) return "Generated title artwork";
  if (source === "official_youtube") return "Official YouTube artwork";
  if (source === "official_social") return "Official social artwork";
  if (source === "official_website") return "Official website artwork";
  if (source === "wikimedia_commons") return "Wikimedia Commons";
  return sourceLabel(source);
}
function movieSourceLabel(movie?: Movie) { return movie?.releaseSourceName?.trim() || sourceLabel(movie?.releaseSource); }
function statusLabel(status: Movie["verificationStatus"]) {
  if (status === "verified") return "Verified";
  if (status === "supported") return "Supported";
  return "Tracking";
}
function toneClass(movie: Movie) {
  let total = 0;
  for (const char of movie.title) total += char.charCodeAt(0);
  return `tone-${total % 8}`;
}
function posterArtwork(movie: Movie) { return movie.posterUrl || movie.backdropUrl; }
function heroArtwork(movie: Movie) { return movie.backdropUrl || movie.posterUrl; }
function hasArtwork(movie: Movie) { return Boolean(posterArtwork(movie)); }

function PosterCard({ movie, onOpen, rank }: { movie: Movie; onOpen: (movie: Movie) => void; rank?: number }) {
  const artwork = posterArtwork(movie);
  return (
    <button className="poster-button" onClick={() => onOpen(movie)} aria-label={`Open details for ${movie.title}`}>
      {rank ? <span className="rank-number">{rank}</span> : null}
      <article className={`poster-card ${toneClass(movie)} ${artwork ? "has-artwork" : ""}`}>
        {artwork ? <img className="poster-artwork" src={artwork} alt="" loading="lazy" referrerPolicy="no-referrer" onError={(event) => { event.currentTarget.style.display = "none"; }} /> : null}
        <div className="poster-grain" />
        <div className="poster-status"><span className={movie.verificationStatus} />{statusLabel(movie.verificationStatus)}</div>
        <div className="poster-copy">
          <p>{movie.language || "Cinema"}</p>
          <h3>{movie.title}</h3>
          <div><span>{yearOf(movie.releaseDate)}</span><span>•</span><span>{countryLabel(movie.countryCode)}</span></div>
        </div>
        <div className="poster-hover">
          <span className="play-orb">ⓘ</span>
          <strong>{formatDate(movie.releaseDate)}</strong>
          <small>{movieSourceLabel(movie)}</small>
        </div>
      </article>
    </button>
  );
}

function MovieDetail({ movie, onClose, onFeature }: { movie: Movie; onClose: () => void; onFeature: (movie: Movie) => void }) {
  const artwork = heroArtwork(movie);
  const isVerified = movie.verificationStatus === "verified";
  const nativeTitle = movie.nativeTitle?.trim() && movie.nativeTitle.trim().toLocaleLowerCase() !== movie.title.trim().toLocaleLowerCase()
    ? movie.nativeTitle.trim()
    : undefined;

  return (
    <div className="detail-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className={`detail-dialog ${toneClass(movie)}`} role="dialog" aria-modal="true" aria-labelledby="movie-detail-title">
        <span className="detail-drag-handle" aria-hidden="true" />
        <button className="detail-close" type="button" onClick={onClose} aria-label="Close movie details">×</button>
        <div className="detail-visual">
          <div className="detail-artwork-fallback" aria-hidden="true"><span>{movie.title.slice(0, 1)}</span></div>
          {artwork ? <img className="detail-artwork" src={artwork} alt="" referrerPolicy="no-referrer" onError={(event) => { event.currentTarget.style.display = "none"; }} /> : null}
          <div className="detail-title-block">
            <div className="detail-eyebrow"><i /> Cinema & Series</div>
            <h2 id="movie-detail-title">{movie.title}</h2>
            {nativeTitle ? <p className="detail-native-title">{nativeTitle}</p> : null}
          </div>
        </div>
        <div className="detail-body">
          <div className="detail-primary">
            <div className="detail-meta">
              <b className={movie.verificationStatus}>{statusLabel(movie.verificationStatus)}</b>
              <span className="dot">•</span><span>{formatDate(movie.releaseDate)}</span>
              <span className="dot">•</span><span>{movie.language || "Unknown language"}</span>
              <span className="dot">•</span><span>{countryLabel(movie.countryCode)}</span>
            </div>
            <p className="detail-summary">
              {isVerified
                ? `This release date is verified against first-party evidence from ${movieSourceLabel(movie)}.`
                : movie.verificationStatus === "supported"
                  ? `This date is supported by the catalogue evidence currently available. First-party confirmation is still being monitored.`
                  : `This title is being tracked while stronger release evidence is collected. Treat the date as unconfirmed until verification improves.`}
            </p>
            <div className="detail-actions">
              <button className="detail-feature" type="button" onClick={() => onFeature(movie)}><span>▶</span> Feature this title</button>
              {movie.artworkSourceUrl ? <a className="detail-source-link" href={movie.artworkSourceUrl} target="_blank" rel="noreferrer noopener">Artwork source ↗</a> : null}
            </div>
          </div>
          <aside className="detail-evidence" aria-label="Movie evidence summary">
            <div className="detail-evidence-row">
              <span>Release status</span>
              <strong>{statusLabel(movie.verificationStatus)}</strong>
              <small>{isVerified ? "First-party date confirmation captured" : "Evidence monitoring remains active"}</small>
            </div>
            <div className="detail-evidence-row">
              <span>Release evidence</span>
              <strong>{movieSourceLabel(movie)}</strong>
              <small>{isVerified ? "Used to verify the listed release date" : "Current catalogue source"}</small>
            </div>
            <div className="detail-evidence-row">
              <span>Visual provenance</span>
              <strong>{artworkSourceLabel(movie.artworkSource)}</strong>
              <small>{movie.artworkSource ? "Artwork provenance tracked separately from release verification" : "Fallback visual generated by the interface"}</small>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [movies, setMovies] = useState<Movie[]>(fallback);
  const [hero, setHero] = useState<Movie>(fallback[0]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [stats, setStats] = useState<CatalogueStats>(fallbackStats);
  const [facets, setFacets] = useState<CatalogueFacets>(fallbackFacets);
  const [pagination, setPagination] = useState<Pagination>(fallbackPagination);
  const [periodCounts, setPeriodCounts] = useState<PeriodCounts>(fallbackPeriods);
  const [source, setSource] = useState<ApiResponse["source"]>("preview");
  const [activeLanguage, setActiveLanguage] = useState("All");
  const [activeCountry, setActiveCountry] = useState("All");
  const [activePeriod, setActivePeriod] = useState("upcoming");
  const [officialOnly, setOfficialOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const today = todayKey();
  const sevenDayEnd = addDaysKey(today, 6);
  const thirtyDayEnd = addDaysKey(today, 29);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(searchQuery.trim()), 240);
    return () => window.clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    if (!selectedMovie) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedMovie(null);
    };
    window.addEventListener("keydown", onKeyDown);
    window.requestAnimationFrame(() => document.querySelector<HTMLButtonElement>(".detail-close")?.focus());
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [selectedMovie]);

  function buildCatalogueUrl(offset: number) {
    const params = new URLSearchParams({ limit: "60", offset: String(offset) });
    if (activePeriod === "all") params.set("scope", "all");
    else if (/^\d{4}$/.test(activePeriod)) { params.set("scope", "all"); params.set("year", activePeriod); }
    else {
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
    return `/api/movies?${params}`;
  }

  function applyResponse(data: ApiResponse, append: boolean) {
    setMovies((current) => append ? [...current, ...data.movies.filter((movie) => !current.some((item) => item.id === movie.id))] : data.movies);
    if (data.stats) setStats(data.stats);
    if (data.facets) setFacets(data.facets);
    if (data.pagination) setPagination(data.pagination);
    if (data.periodCounts) setPeriodCounts(data.periodCounts);
    setSource(data.source);
    if (!append && !debouncedSearch && activeLanguage === "All" && activeCountry === "All" && data.movies.length) {
      setHero(
        data.movies.find((movie) => movie.verificationStatus === "verified" && hasArtwork(movie))
        ?? data.movies.find((movie) => movie.verificationStatus === "verified")
        ?? data.movies.find(hasArtwork)
        ?? data.movies[0],
      );
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetch(buildCatalogueUrl(0), { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Movie API unavailable"); return response.json() as Promise<ApiResponse>; })
      .then((data) => applyResponse(data, false))
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [activeCountry, activeLanguage, activePeriod, debouncedSearch, officialOnly]);

  function openMovie(movie: Movie) { setSelectedMovie(movie); }
  function featureMovie(movie: Movie) {
    setHero(movie);
    setSelectedMovie(null);
    window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  function loadMore() {
    if (loadingMore || !pagination.hasMore) return;
    setLoadingMore(true);
    fetch(buildCatalogueUrl(movies.length))
      .then((response) => { if (!response.ok) throw new Error("Movie API unavailable"); return response.json() as Promise<ApiResponse>; })
      .then((data) => applyResponse(data, true))
      .catch(() => undefined)
      .finally(() => setLoadingMore(false));
  }

  const verified = useMemo(() => movies.filter((movie) => movie.verificationStatus === "verified"), [movies]);
  const arriving = useMemo(() => [...movies].sort((a, b) => a.releaseDate.localeCompare(b.releaseDate)), [movies]);
  const featured = verified.length ? verified : arriving;
  const languages = useMemo(() => ["All", ...facets.languages.slice(0, 16).map((item) => item.value)], [facets.languages]);
  const countries = useMemo(() => ["All", ...facets.countries.slice(0, 12).map((item) => item.value)], [facets.countries]);
  const years = useMemo(() => facets.years.slice(0, 10), [facets.years]);
  const activeHeroArtwork = heroArtwork(hero);

  return (
    <main className="stream-app">
      <header className="stream-nav">
        <a className="stream-brand" href="#top"><span>CINEMA</span><b>& SERIES</b></a>
        <nav className="desktop-nav" aria-label="Primary navigation">
          <a className="active" href="#top">Home</a><a href="#upcoming">Upcoming</a><a href="#browse">Browse</a>
        </nav>
        <div className="nav-actions">
          <button className="icon-button" onClick={() => setSearchOpen((value) => !value)} aria-label="Toggle search">⌕</button>
          <button className={`verified-nav ${officialOnly ? "active" : ""}`} onClick={() => setOfficialOnly((value) => !value)}>✓ Verified</button>
          <span className={`service-dot ${source === "d1" ? "live" : ""}`} title={source === "d1" ? "Live catalogue" : "Preview catalogue"} />
        </div>
      </header>

      <section id="top" className={`stream-hero ${toneClass(hero)} ${activeHeroArtwork ? "has-artwork" : ""}`}>
        <div className="hero-art">
          {activeHeroArtwork ? <img className="hero-backdrop" src={activeHeroArtwork} alt="" referrerPolicy="no-referrer" onError={(event) => { event.currentTarget.style.display = "none"; }} /> : null}
          <div className="hero-orb" /><div className="hero-lines" /><span className="hero-monogram">{hero.title.slice(0, 1)}</span>
        </div>
        <div className="hero-vignette" />
        <div className="stream-hero-copy">
          <div className="series-label"><span>N</span> FEATURED RELEASE</div>
          <h1>{hero.title}</h1>
          <div className="hero-meta">
            <strong className={hero.verificationStatus}>{statusLabel(hero.verificationStatus)}</strong>
            <span>{formatDate(hero.releaseDate)}</span><span>{hero.language || "Cinema"}</span><span>{countryLabel(hero.countryCode)}</span>
          </div>
          <p>{hero.verificationStatus === "verified" ? `Release date confirmed through ${movieSourceLabel(hero)}.` : `Currently tracked through ${movieSourceLabel(hero)} while stronger release evidence is monitored.`} Explore a growing India-first, global movie catalogue.</p>
          <div className="hero-buttons">
            <a className="play-button" href="#browse"><span>▶</span> Browse catalogue</a>
            <button className="info-button" onClick={() => setSelectedMovie(hero)}><span>ⓘ</span> More info</button>
          </div>
        </div>
        <div className="hero-stats"><span>{stats.total.toLocaleString("en-IN")} TITLES</span><i /><span>{stats.activeSources} OFFICIAL SOURCES</span></div>
      </section>

      <div className={`search-panel ${searchOpen || searchQuery ? "open" : ""}`}>
        <span>⌕</span><input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Titles, languages, countries…" aria-label="Search catalogue" />
        {searchQuery && <button onClick={() => setSearchQuery("")}>Clear</button>}
      </div>

      <section className="content-stage">
        <div className="stream-row first-row">
          <div className="row-heading"><h2>Verified releases</h2><span>{stats.verified} official dates</span></div>
          <div className="poster-rail rank-rail">
            {featured.slice(0, 10).map((movie, index) => <PosterCard key={movie.id} movie={movie} onOpen={openMovie} rank={index + 1} />)}
          </div>
        </div>

        <div id="upcoming" className="stream-row">
          <div className="row-heading"><h2>Coming soon</h2><span>{periodCounts.upcoming} tracked</span></div>
          <div className="poster-rail">
            {arriving.slice(0, 14).map((movie) => <PosterCard key={movie.id} movie={movie} onOpen={openMovie} />)}
          </div>
        </div>

        <div className="stream-row">
          <div className="row-heading"><h2>Browse by language</h2><span>India-first discovery</span></div>
          <div className="genre-rail">
            {facets.languages.slice(0, 12).map((item, index) => (
              <button key={item.value} className={`language-tile tile-${index % 6}`} onClick={() => { setActiveLanguage(item.value); document.querySelector("#browse")?.scrollIntoView({ behavior: "smooth" }); }}>
                <span>{item.value}</span><small>{item.count} titles</small><b>→</b>
              </button>
            ))}
          </div>
        </div>

        <section id="browse" className="browse-section">
          <div className="browse-heading"><div><p>EXPLORE THE CATALOGUE</p><h2>{debouncedSearch ? `Results for “${debouncedSearch}”` : activeLanguage !== "All" ? `${activeLanguage} cinema` : activeCountry !== "All" ? `${countryLabel(activeCountry)} cinema` : "More to discover"}</h2></div><span>{pagination.total} matching titles</span></div>
          <div className="filter-deck">
            <div className="filter-strip">
              <button className={activePeriod === "upcoming" ? "active" : ""} onClick={() => setActivePeriod("upcoming")}>Upcoming</button>
              <button className={activePeriod === "30d" ? "active" : ""} onClick={() => setActivePeriod("30d")}>Next 30 days</button>
              {years.map(({ value }) => <button key={value} className={activePeriod === value ? "active" : ""} onClick={() => setActivePeriod(value)}>{value}</button>)}
              <button className={activePeriod === "all" ? "active" : ""} onClick={() => setActivePeriod("all")}>All years</button>
            </div>
            <div className="filter-strip muted-filter">
              {languages.map((language) => <button key={language} className={activeLanguage === language ? "active" : ""} onClick={() => setActiveLanguage(language)}>{language}</button>)}
            </div>
            <div className="filter-strip muted-filter country-filter">
              {countries.map((country) => <button key={country} className={activeCountry === country ? "active" : ""} onClick={() => setActiveCountry(country)}>{country === "All" ? "All countries" : countryLabel(country)}</button>)}
            </div>
          </div>

          {loading && <div className="skeleton-grid">{Array.from({ length: 12 }).map((_, index) => <div className="skeleton-card" key={index} />)}</div>}
          {!loading && movies.length > 0 && <div className="catalogue-grid">{movies.map((movie) => <PosterCard key={movie.id} movie={movie} onOpen={openMovie} />)}</div>}
          {!loading && !movies.length && <div className="empty"><span>⌕</span><h3>No titles in this slice</h3><p>Try another year, language, country or confidence filter.</p></div>}
          {pagination.hasMore && <button className="load-more" onClick={loadMore} disabled={loadingMore}>{loadingMore ? "Loading…" : `Load more · ${Math.max(0, pagination.total - movies.length)} left`}</button>}
        </section>
      </section>

      <footer className="stream-footer"><div className="stream-brand"><span>CINEMA</span><b>& SERIES</b></div><p>India-first release intelligence · global cinema catalogue</p><small>{stats.total.toLocaleString("en-IN")} titles · {facets.languages.length} languages · {stats.activeSources} official sources</small></footer>

      <nav className="mobile-nav" aria-label="Mobile navigation">
        <a href="#top"><span>⌂</span><small>Home</small></a><a href="#upcoming"><span>◷</span><small>Upcoming</small></a><button onClick={() => setSearchOpen(true)}><span>⌕</span><small>Search</small></button><a href="#browse"><span>▦</span><small>Browse</small></a>
      </nav>

      {selectedMovie ? <MovieDetail movie={selectedMovie} onClose={() => setSelectedMovie(null)} onFeature={featureMovie} /> : null}
    </main>
  );
}
