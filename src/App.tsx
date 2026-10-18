import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, Navigate, NavLink, Route, Routes } from "react-router";

type Movie = {
  id: string;
  title: string;
  nativeTitle?: string;
  language: string;
  countryCode?: string;
  releaseDate?: string;
  releaseYear?: number;
  datePrecision?: "day" | "year";
  verificationStatus: "verified" | "supported" | "unconfirmed";
  releaseSource?: string;
  releaseSourceName?: string;
  releaseSourceUrl?: string;
  posterUrl?: string;
  backdropUrl?: string;
};

type SeriesKind = "series" | "web_series" | "miniseries" | "anthology" | "unknown";
type SeriesTitle = {
  id: string;
  wikidataQid?: string;
  title: string;
  nativeTitle?: string;
  posterUrl?: string;
  backdropUrl?: string;
  artworkSource?: string;
  seriesKind: SeriesKind;
  language: string;
  countryCode?: string;
  firstAirYear?: number;
  lastAirYear?: number;
  lifecycleStatus: "unknown" | "upcoming" | "ongoing" | "ended" | "limited";
  seasonCount?: number;
  episodeCount?: number;
  verificationStatus: "verified" | "supported" | "unconfirmed";
  sourceUrl?: string;
};

type FacetValue = { value: string; count: number };
type MovieResponse = {
  movies: Movie[];
  pagination?: { limit: number; offset: number; total: number; hasMore: boolean };
  facets?: { years: FacetValue[]; languages: FacetValue[]; countries: FacetValue[] };
  periodCounts?: { upcoming: number; next7Days: number; next30Days: number };
  stats?: { total: number; verified: number; supported: number; unconfirmed: number; activeSources: number };
};
type SeriesResponse = {
  series: SeriesTitle[];
  pagination?: { limit: number; offset: number; total: number; hasMore: boolean };
  facets?: { years: FacetValue[]; languages: FacetValue[]; countries: FacetValue[]; kinds: FacetValue[] };
  stats?: { total: number; withFirstAirYear: number; webSeries: number; miniseries: number };
};
type CatalogueCounts = { movies: number; series: number; total: number };
type MovieFilters = { q: string; year: string; language: string; country: string };
type SeriesFilters = MovieFilters & { kind: string };

const countryNames: Record<string, string> = {
  IN: "India", US: "United States", GB: "United Kingdom", KR: "South Korea", JP: "Japan", FR: "France", DE: "Germany",
  IT: "Italy", ES: "Spain", CN: "China", HK: "Hong Kong", TW: "Taiwan", CA: "Canada", AU: "Australia", NZ: "New Zealand",
  BR: "Brazil", MX: "Mexico", AR: "Argentina", TR: "Turkey", PK: "Pakistan", BD: "Bangladesh", ID: "Indonesia", TH: "Thailand",
};
const kindLabels: Record<SeriesKind, string> = {
  series: "Series", web_series: "Web series", miniseries: "Miniseries", anthology: "Anthology", unknown: "Series",
};

function countryLabel(code?: string) { return !code ? "Global" : countryNames[code] ?? code; }
function movieYear(movie: Movie) { return movie.releaseYear ?? Number(movie.releaseDate?.slice(0, 4) || 0); }
function formatDate(value?: string) {
  if (!value) return "Release date not confirmed";
  return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00+05:30`));
}
function kindLabel(kind: SeriesKind) { return kindLabels[kind] ?? "Series"; }
function toneIndex(title: string) { return [...title].reduce((total, char) => total + char.charCodeAt(0), 0) % 8; }
function firstLetter(title: string) { return title.trim().slice(0, 1).toUpperCase() || "C"; }
function activeFilterCount(filters: Record<string, string>) { return Object.values(filters).filter((value) => value && value !== "all").length; }
function indiaDateKey(date = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date).map(({ type, value }) => [type, value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}
function addDaysKey(value: string, days: number) {
  const instant = new Date(`${value}T00:00:00+05:30`);
  instant.setDate(instant.getDate() + days);
  return indiaDateKey(instant);
}

function useCounts() {
  const [counts, setCounts] = useState<CatalogueCounts>({ movies: 0, series: 0, total: 0 });
  useEffect(() => {
    fetch("/api/catalogue-stats").then((response) => response.ok ? response.json() as Promise<CatalogueCounts> : Promise.reject()).then(setCounts).catch(() => undefined);
  }, []);
  return counts;
}

// Avoid a new expensive D1 catalogue query for every keystroke in search.
function useDebouncedValue(value: string, delayMs = 400) {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setSettled(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return settled;
}

function useMovies(query: Record<string, string>, limit = 60) {
  const [payload, setPayload] = useState<MovieResponse>({ movies: [] });
  const [loading, setLoading] = useState(true);
  const queryKey = JSON.stringify(query);
  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: String(limit), offset: "0", artwork: "1", ...query });
    setLoading(true);
    fetch(`/api/movies?${params}`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("movies unavailable"); return response.json() as Promise<MovieResponse>; })
      .then(setPayload).catch(() => undefined).finally(() => setLoading(false));
    return () => controller.abort();
  }, [queryKey, limit]);
  return { payload, loading };
}

function useSeries(query: Record<string, string>, limit = 60) {
  const [payload, setPayload] = useState<SeriesResponse>({ series: [] });
  const [loading, setLoading] = useState(true);
  const queryKey = JSON.stringify(query);
  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: String(limit), offset: "0", artwork: "1", ...query });
    setLoading(true);
    fetch(`/api/series?${params}`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("series unavailable"); return response.json() as Promise<SeriesResponse>; })
      .then(setPayload).catch(() => undefined).finally(() => setLoading(false));
    return () => controller.abort();
  }, [queryKey, limit]);
  return { payload, loading };
}


type PageRequestState = { key: string; page: number; loading: boolean; error: boolean };

// A browse page retains previously loaded cards, but never mixes items from
// two different search/filter queries. All requests remain bounded to 60 rows.
function usePagedMovies(query: Record<string, string>, limit = 60) {
  const queryKey = JSON.stringify(query);
  const [cursor, setCursor] = useState({ key: "", page: 0 });
  const [response, setResponse] = useState<{ key: string; payload: MovieResponse }>({ key: "", payload: { movies: [] } });
  const [request, setRequest] = useState<PageRequestState>({ key: "", page: 0, loading: true, error: false });
  const [retryIndex, setRetryIndex] = useState(0);
  const page = cursor.key === queryKey ? cursor.page : 0;

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit), artwork: "1", ...query });
    setRequest({ key: queryKey, page, loading: true, error: false });
    fetch(`/api/movies?${params}`, { signal: controller.signal })
      .then((result) => { if (!result.ok) throw new Error("movies unavailable"); return result.json() as Promise<MovieResponse>; })
      .then((next) => {
        if (controller.signal.aborted) return;
        setResponse((previous) => ({
          key: queryKey,
          payload: page === 0 ? next : {
            ...next,
            movies: [...(previous.key === queryKey ? previous.payload.movies : []), ...next.movies],
          },
        }));
        setRequest({ key: queryKey, page, loading: false, error: false });
      })
      .catch(() => {
        if (!controller.signal.aborted) setRequest({ key: queryKey, page, loading: false, error: true });
      });
    return () => controller.abort();
  }, [queryKey, page, limit, retryIndex]);

  const payload: MovieResponse = response.key === queryKey ? response.payload : { movies: [] };
  const loading = request.key !== queryKey || request.page !== page || request.loading;
  const error = request.key === queryKey && request.page === page && request.error;
  const loadMore = () => {
    if (!loading && !error && payload.pagination?.hasMore) setCursor({ key: queryKey, page: page + 1 });
  };
  return { payload, loading, error, loadMore, retry: () => setRetryIndex((index) => index + 1) };
}

function usePagedSeries(query: Record<string, string>, limit = 60) {
  const queryKey = JSON.stringify(query);
  const [cursor, setCursor] = useState({ key: "", page: 0 });
  const [response, setResponse] = useState<{ key: string; payload: SeriesResponse }>({ key: "", payload: { series: [] } });
  const [request, setRequest] = useState<PageRequestState>({ key: "", page: 0, loading: true, error: false });
  const [retryIndex, setRetryIndex] = useState(0);
  const page = cursor.key === queryKey ? cursor.page : 0;

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit), artwork: "1", ...query });
    setRequest({ key: queryKey, page, loading: true, error: false });
    fetch(`/api/series?${params}`, { signal: controller.signal })
      .then((result) => { if (!result.ok) throw new Error("series unavailable"); return result.json() as Promise<SeriesResponse>; })
      .then((next) => {
        if (controller.signal.aborted) return;
        setResponse((previous) => ({
          key: queryKey,
          payload: page === 0 ? next : {
            ...next,
            series: [...(previous.key === queryKey ? previous.payload.series : []), ...next.series],
          },
        }));
        setRequest({ key: queryKey, page, loading: false, error: false });
      })
      .catch(() => {
        if (!controller.signal.aborted) setRequest({ key: queryKey, page, loading: false, error: true });
      });
    return () => controller.abort();
  }, [queryKey, page, limit, retryIndex]);

  const payload: SeriesResponse = response.key === queryKey ? response.payload : { series: [] };
  const loading = request.key !== queryKey || request.page !== page || request.loading;
  const error = request.key === queryKey && request.page === page && request.error;
  const loadMore = () => {
    if (!loading && !error && payload.pagination?.hasMore) setCursor({ key: queryKey, page: page + 1 });
  };
  return { payload, loading, error, loadMore, retry: () => setRetryIndex((index) => index + 1) };
}

function useModalLock(active: boolean, onClose: () => void) {
  useEffect(() => {
    if (!active) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => { document.body.style.overflow = previous; window.removeEventListener("keydown", onKey); };
  }, [active, onClose]);
}

function TopNav() {
  return (
    <header className="top-nav">
      <Link className="brand" to="/"><span>CINEMA</span><b>& SERIES</b></Link>
      <nav className="primary-links" aria-label="Primary navigation">
        <NavLink end to="/">Home</NavLink>
        <NavLink to="/movies">Movies</NavLink>
        <NavLink to="/series">Series</NavLink>
        <NavLink to="/upcoming">Upcoming</NavLink>
      </nav>
      <div className="nav-end"><span className="live-dot" /><span>Live catalogue</span></div>
    </header>
  );
}

function MobileNav() {
  return (
    <nav className="mobile-nav-v2" aria-label="Mobile navigation">
      <NavLink end to="/"><span>⌂</span><small>Home</small></NavLink>
      <NavLink to="/movies"><span>▣</span><small>Movies</small></NavLink>
      <NavLink to="/series"><span>▤</span><small>Series</small></NavLink>
      <NavLink to="/upcoming"><span>◷</span><small>Upcoming</small></NavLink>
    </nav>
  );
}

// A broken remote image must reveal the designed title initial instead of
// leaving an empty gradient card. The keyed instance resets when URLs change.
function PosterArtwork({ url, title, hero = false }: { url?: string; title: string; hero?: boolean }) {
  const [failed, setFailed] = useState(false);
  if (!url || failed) {
    return <span className={hero ? "detail-fallback-letter" : "fallback-letter"}>{firstLetter(title)}</span>;
  }
  return <img src={url} alt="" loading={hero ? "eager" : "lazy"} referrerPolicy="no-referrer" onError={() => setFailed(true)} />;
}

function MovieCard({ movie, onOpen }: { movie: Movie; onOpen: (movie: Movie) => void }) {
  const artwork = movie.posterUrl || movie.backdropUrl;
  return (
    <button className={`media-card movie-card tone-${toneIndex(movie.title)}`} onClick={() => onOpen(movie)}>
      <div className="media-art">
        <PosterArtwork key={artwork ?? movie.id} url={artwork} title={movie.title} />
        {movie.verificationStatus === "verified" ? <em className="quality-pill">Verified</em> : null}
      </div>
      <div className="media-copy"><strong>{movie.title}</strong><span>{movieYear(movie) || "—"} · {movie.language || "Cinema"}</span></div>
    </button>
  );
}

function SeriesCard({ item, onOpen }: { item: SeriesTitle; onOpen: (item: SeriesTitle) => void }) {
  return (
    <button className={`media-card series-poster tone-${toneIndex(item.title)}`} onClick={() => onOpen(item)}>
      <div className="media-art series-fallback">
        <PosterArtwork key={item.posterUrl ?? item.id} url={item.posterUrl} title={item.title} />
        <em className="kind-pill">{kindLabel(item.seriesKind)}</em>
      </div>
      <div className="media-copy"><strong>{item.title}</strong><span>{item.firstAirYear ?? "Year unknown"} · {item.language || "Language unknown"}</span></div>
    </button>
  );
}

function Row({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return <section className="content-row"><div className="row-title"><h2>{title}</h2>{action}</div><div className="horizontal-rail">{children}</div></section>;
}

function MovieDetail({ movie, onClose }: { movie: Movie; onClose: () => void }) {
  useModalLock(true, onClose);
  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <article className={`detail-sheet tone-${toneIndex(movie.title)}`} role="dialog" aria-modal="true">
        <button className="modal-close" onClick={onClose}>×</button>
        <div className="detail-hero">
          <PosterArtwork key={movie.backdropUrl || movie.posterUrl || movie.id} url={movie.backdropUrl || movie.posterUrl} title={movie.title} hero />
          <div><p>MOVIE</p><h2>{movie.title}</h2><small>{formatDate(movie.releaseDate)} · {movie.language} · {countryLabel(movie.countryCode)}</small></div>
        </div>
        <div className="detail-content">
          <p>{movie.datePrecision === "year" || !movie.releaseDate ? `Release year sourced from ${movie.releaseSourceName || "the catalogue"}. The exact release date is not independently verified.` : movie.verificationStatus === "verified" ? `Release information is verified against ${movie.releaseSourceName || "a first-party source"}.` : "This title is in the catalogue while stronger first-party release evidence is still being collected."}</p>
          <div className="detail-facts"><span><b>Year</b>{movieYear(movie) || "—"}</span><span><b>Language</b>{movie.language || "Unknown"}</span><span><b>Country</b>{countryLabel(movie.countryCode)}</span><span><b>Status</b>{movie.verificationStatus === "verified" ? "Verified" : "Unconfirmed"}</span></div>
          {movie.releaseSourceUrl && (movie.datePrecision === "year" || !movie.releaseDate) ? <div className="source-links"><a href={movie.releaseSourceUrl} target="_blank" rel="noopener noreferrer">View {movie.releaseSource === "wikidata" ? "Wikidata film record" : "Wikipedia film source"} ↗</a></div> : null}
        </div>
      </article>
    </div>
  );
}

function SeriesDetail({ item, onClose }: { item: SeriesTitle; onClose: () => void }) {
  useModalLock(true, onClose);
  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <article className={`detail-sheet tone-${toneIndex(item.title)}`} role="dialog" aria-modal="true">
        <button className="modal-close" onClick={onClose}>×</button>
        <div className="detail-hero">
          <PosterArtwork key={item.backdropUrl || item.posterUrl || item.id} url={item.backdropUrl || item.posterUrl} title={item.title} hero />
          <div><p>{kindLabel(item.seriesKind).toUpperCase()}</p><h2>{item.title}</h2><small>{item.firstAirYear ?? "Year unknown"} · {item.language || "Language unknown"} · {countryLabel(item.countryCode)}</small></div>
        </div>
        <div className="detail-content">
          <p>Series information stays inside Cinema & Series. External references are sources, not the browsing experience.</p>
          <div className="detail-facts"><span><b>Format</b>{kindLabel(item.seriesKind)}</span><span><b>Status</b>{item.lifecycleStatus === "unknown" ? "Not classified" : item.lifecycleStatus}</span><span><b>Seasons</b>{item.seasonCount ?? "—"}</span><span><b>Episodes</b>{item.episodeCount ?? "—"}</span></div>
          {(item.sourceUrl || item.wikidataQid) ? <div className="source-links">{item.sourceUrl ? <a href={item.sourceUrl} target="_blank" rel="noreferrer noopener">Wikipedia source ↗</a> : null}{item.wikidataQid ? <a href={`https://www.wikidata.org/wiki/${item.wikidataQid}`} target="_blank" rel="noreferrer noopener">Wikidata ↗</a> : null}</div> : null}
        </div>
      </article>
    </div>
  );
}

function HomePage() {
  const counts = useCounts();
  const upcoming = useMovies({ scope: "upcoming" }, 40);
  const series = useSeries({}, 18);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [selectedSeries, setSelectedSeries] = useState<SeriesTitle | null>(null);
  const hero = upcoming.payload.movies.find((item) => item.verificationStatus === "verified" && (item.backdropUrl || item.posterUrl)) ?? upcoming.payload.movies.find((item) => item.verificationStatus === "verified") ?? upcoming.payload.movies[0];
  const verified = upcoming.payload.movies.filter((item) => item.verificationStatus === "verified").slice(0, 12);
  const coming = upcoming.payload.movies.filter((item) => item.releaseDate).slice(0, 14);
  return (
    <main className="page home-page">
      <section className={`home-hero tone-${toneIndex(hero?.title || "Cinema")}`}>
        {hero?.backdropUrl || hero?.posterUrl ? <img src={hero.backdropUrl || hero.posterUrl} alt="" referrerPolicy="no-referrer" /> : null}
        <div className="home-hero-shade" />
        <div className="home-hero-copy"><p>FEATURED RELEASE</p><h1>{hero?.title || "Cinema & Series"}</h1><span>{hero ? `${formatDate(hero.releaseDate)} · ${hero.language}` : "Movies and series, one cinematic home."}</span><div className="hero-actions">{hero ? <button onClick={() => setSelectedMovie(hero)}>ⓘ More info</button> : null}<Link to="/movies">Browse movies</Link></div></div>
      </section>
      <div className="home-content">
        <Row title="Verified releases" action={<Link to="/upcoming">See all</Link>}>{verified.map((item) => <MovieCard key={item.id} movie={item} onOpen={setSelectedMovie} />)}</Row>
        <Row title="Coming soon" action={<Link to="/upcoming">See all</Link>}>{coming.map((item) => <MovieCard key={item.id} movie={item} onOpen={setSelectedMovie} />)}</Row>
        <Row title="Series to discover" action={<Link to="/series">Explore series</Link>}>{series.payload.series.slice(0, 14).map((item) => <SeriesCard key={item.id} item={item} onOpen={setSelectedSeries} />)}</Row>
        <section className="home-library-callout"><div><p>EXPLORE THE LIBRARY</p><h2>{counts.total.toLocaleString("en-IN")} titles and growing</h2><span>{counts.movies.toLocaleString("en-IN")} movies · {counts.series.toLocaleString("en-IN")} series</span></div><div><Link to="/movies">Movies</Link><Link to="/series">Series</Link></div></section>
      </div>
      {selectedMovie ? <MovieDetail movie={selectedMovie} onClose={() => setSelectedMovie(null)} /> : null}
      {selectedSeries ? <SeriesDetail item={selectedSeries} onClose={() => setSelectedSeries(null)} /> : null}
    </main>
  );
}

function FilterButton({ open, count, onClick }: { open: boolean; count: number; onClick: () => void }) {
  return <button className={`filter-button ${open ? "active" : ""}`} onClick={onClick}>☰ Filters{count ? <b>{count}</b> : null}</button>;
}

function MoviesPage() {
  const counts = useCounts();
  const [filters, setFilters] = useState<MovieFilters>({ q: "", year: "all", language: "all", country: "all" });
  const [filterOpen, setFilterOpen] = useState(false);
  const [selected, setSelected] = useState<Movie | null>(null);
  const settledSearch = useDebouncedValue(filters.q.trim());
  const query = useMemo(() => ({ scope: "all", ...(settledSearch ? { q: settledSearch } : {}), ...(filters.year !== "all" ? { year: filters.year } : {}), ...(filters.language !== "all" ? { language: filters.language } : {}), ...(filters.country !== "all" ? { country: filters.country } : {}) }), [filters.year, filters.language, filters.country, settledSearch]);
  const all = usePagedMovies(query, 60);
  const coming = useMovies({ scope: "upcoming" }, 14);
  const facets = all.payload.facets;
  return (
    <main className="page library-page">
      <section className="library-hero movie-library-hero"><div><p>MOVIES</p><h1>Movies</h1><span>Discover cinema by language, country and year.</span></div><b>{counts.movies.toLocaleString("en-IN")} titles</b></section>
      <Row title="New & upcoming" action={<Link to="/upcoming">View upcoming</Link>}>{coming.payload.movies.map((item) => <MovieCard key={item.id} movie={item} onOpen={setSelected} />)}</Row>
      <section className="catalogue-section">
        <div className="catalogue-heading"><div><h2>Explore movies</h2><span>{all.payload.pagination?.total?.toLocaleString("en-IN") || counts.movies.toLocaleString("en-IN")} titles</span></div><div className="catalogue-tools"><input value={filters.q} onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))} placeholder="Search movies" /><FilterButton open={filterOpen} count={activeFilterCount({ year: filters.year, language: filters.language, country: filters.country })} onClick={() => setFilterOpen((value) => !value)} /></div></div>
        {filterOpen ? <div className="filter-panel"><label>Year<select value={filters.year} onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))}><option value="all">All years</option>{facets?.years.map((item) => <option key={item.value} value={item.value}>{item.value}</option>)}</select></label><label>Language<select value={filters.language} onChange={(event) => setFilters((current) => ({ ...current, language: event.target.value }))}><option value="all">All languages</option>{facets?.languages.filter((item) => item.value !== "Unknown").map((item) => <option key={item.value} value={item.value}>{item.value}</option>)}</select></label><label>Country<select value={filters.country} onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}><option value="all">All countries</option>{facets?.countries.map((item) => <option key={item.value} value={item.value}>{countryLabel(item.value)}</option>)}</select></label><button onClick={() => setFilters({ q: "", year: "all", language: "all", country: "all" })}>Reset</button></div> : null}
        {all.loading && !all.payload.movies.length ? <CardSkeletons /> : <div className="media-grid">{all.payload.movies.map((item) => <MovieCard key={item.id} movie={item} onOpen={setSelected} />)}</div>}
        {!all.loading && !all.error && !all.payload.movies.length ? <p className="catalogue-empty">No movies match these filters. Try another title, year, or language.</p> : null}
        <div className="catalogue-pagination" aria-live="polite">
          {all.payload.movies.length ? <span>Showing {all.payload.movies.length.toLocaleString("en-IN")} of {(all.payload.pagination?.total ?? all.payload.movies.length).toLocaleString("en-IN")} movies</span> : null}
          {all.error ? <button type="button" onClick={all.retry}>Couldn’t load movies. Retry</button> : null}
          {all.payload.pagination?.hasMore ? <button type="button" onClick={all.loadMore} disabled={all.loading || all.error}>{all.loading ? "Loading more…" : "Load more movies"}</button> : null}
        </div>
      </section>
      {selected ? <MovieDetail movie={selected} onClose={() => setSelected(null)} /> : null}
    </main>
  );
}

function SeriesPage() {
  const counts = useCounts();
  const [filters, setFilters] = useState<SeriesFilters>({ q: "", year: "all", language: "all", country: "all", kind: "all" });
  const [filterOpen, setFilterOpen] = useState(false);
  const [selected, setSelected] = useState<SeriesTitle | null>(null);
  const settledSearch = useDebouncedValue(filters.q.trim());
  const query = useMemo(() => ({ ...(settledSearch ? { q: settledSearch } : {}), ...(filters.year !== "all" ? { year: filters.year } : {}), ...(filters.language !== "all" ? { language: filters.language } : {}), ...(filters.country !== "all" ? { country: filters.country } : {}), ...(filters.kind !== "all" ? { kind: filters.kind } : {}) }), [filters.year, filters.language, filters.country, filters.kind, settledSearch]);
  const all = usePagedSeries(query, 60);
  const facets = all.payload.facets;
  return (
    <main className="page library-page series-library-page">
      <section className="library-hero series-library-hero"><div><p>SERIES</p><h1>Series</h1><span>Shows from India and around the world, in their own dedicated library.</span></div><b>{counts.series.toLocaleString("en-IN")} titles</b></section>
      <section className="spotlight-strip"><div><small>DISCOVER SERIES</small><h2>Find your next show</h2><p>Browse by language, country, debut year or format. Genre browsing will appear when genre metadata is available in the catalogue.</p></div></section>
      <section className="catalogue-section series-catalogue-section">
        <div className="catalogue-heading"><div><h2>Explore series</h2><span>{all.payload.pagination?.total?.toLocaleString("en-IN") || counts.series.toLocaleString("en-IN")} titles</span></div><div className="catalogue-tools"><input value={filters.q} onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))} placeholder="Search series" /><FilterButton open={filterOpen} count={activeFilterCount({ year: filters.year, language: filters.language, country: filters.country, kind: filters.kind })} onClick={() => setFilterOpen((value) => !value)} /></div></div>
        {filterOpen ? <div className="filter-panel four"><label>Language<select value={filters.language} onChange={(event) => setFilters((current) => ({ ...current, language: event.target.value }))}><option value="all">All languages</option>{facets?.languages.filter((item) => item.value !== "Unknown").map((item) => <option key={item.value} value={item.value}>{item.value}</option>)}</select></label><label>Country<select value={filters.country} onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}><option value="all">All countries</option>{facets?.countries.map((item) => <option key={item.value} value={item.value}>{countryLabel(item.value)}</option>)}</select></label><label>Year<select value={filters.year} onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))}><option value="all">All years</option>{facets?.years.map((item) => <option key={item.value} value={item.value}>{item.value}</option>)}</select></label><label>Format<select value={filters.kind} onChange={(event) => setFilters((current) => ({ ...current, kind: event.target.value }))}><option value="all">All formats</option>{facets?.kinds.filter((item) => item.value !== "unknown").map((item) => <option key={item.value} value={item.value}>{kindLabel(item.value as SeriesKind)}</option>)}</select></label><button onClick={() => setFilters({ q: "", year: "all", language: "all", country: "all", kind: "all" })}>Reset</button></div> : null}
        {all.loading && !all.payload.series.length ? <CardSkeletons /> : <div className="media-grid">{all.payload.series.map((item) => <SeriesCard key={item.id} item={item} onOpen={setSelected} />)}</div>}
        {!all.loading && !all.error && !all.payload.series.length ? <p className="catalogue-empty">No series match these filters. Try another title, year, or language.</p> : null}
        <div className="catalogue-pagination" aria-live="polite">
          {all.payload.series.length ? <span>Showing {all.payload.series.length.toLocaleString("en-IN")} of {(all.payload.pagination?.total ?? all.payload.series.length).toLocaleString("en-IN")} series</span> : null}
          {all.error ? <button type="button" onClick={all.retry}>Couldn’t load series. Retry</button> : null}
          {all.payload.pagination?.hasMore ? <button type="button" onClick={all.loadMore} disabled={all.loading || all.error}>{all.loading ? "Loading more…" : "Load more series"}</button> : null}
        </div>
      </section>
      {selected ? <SeriesDetail item={selected} onClose={() => setSelected(null)} /> : null}
    </main>
  );
}

function UpcomingPage() {
  const [window, setWindow] = useState<"all" | "30d" | "7d">("all");
  const [language, setLanguage] = useState("all");
  const [selected, setSelected] = useState<Movie | null>(null);
  const today = indiaDateKey();
  const query = useMemo(() => ({ scope: "upcoming", from: today, ...(window === "7d" ? { to: addDaysKey(today, 6) } : window === "30d" ? { to: addDaysKey(today, 29) } : {}), ...(language !== "all" ? { language } : {}) }), [window, language, today]);
  const data = useMovies(query, 80);
  const facets = data.payload.facets;
  return (
    <main className="page upcoming-page">
      <section className="library-hero upcoming-hero"><div><p>UPCOMING</p><h1>Coming soon</h1><span>Upcoming theatrical releases and tracked release dates.</span></div><b>{data.payload.pagination?.total?.toLocaleString("en-IN") || "—"} titles</b></section>
      <section className="upcoming-controls"><div className="segmented"><button className={window === "all" ? "active" : ""} onClick={() => setWindow("all")}>All upcoming</button><button className={window === "30d" ? "active" : ""} onClick={() => setWindow("30d")}>Next 30 days</button><button className={window === "7d" ? "active" : ""} onClick={() => setWindow("7d")}>Next 7 days</button></div><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="all">All languages</option>{facets?.languages.filter((item) => item.value !== "Unknown").map((item) => <option key={item.value} value={item.value}>{item.value}</option>)}</select></section>
      <section className="catalogue-section compact-top">{data.loading ? <CardSkeletons /> : <div className="media-grid">{data.payload.movies.map((item) => <MovieCard key={item.id} movie={item} onOpen={setSelected} />)}</div>}</section>
      {selected ? <MovieDetail movie={selected} onClose={() => setSelected(null)} /> : null}
    </main>
  );
}

function CardSkeletons() { return <div className="media-grid">{Array.from({ length: 12 }).map((_, index) => <div className="card-skeleton" key={index} />)}</div>; }

export default function App() {
  return (
    <div className="cs-app">
      <TopNav />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/movies" element={<MoviesPage />} />
        <Route path="/series" element={<SeriesPage />} />
        <Route path="/upcoming" element={<UpcomingPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <MobileNav />
    </div>
  );
}
