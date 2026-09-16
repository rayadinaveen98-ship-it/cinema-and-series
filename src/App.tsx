import { useEffect, useMemo, useState } from "react";

type Movie = {
  id: string;
  wikidataQid?: string;
  title: string;
  nativeTitle?: string;
  language: string;
  releaseDate: string;
  verificationStatus: "verified" | "supported" | "unconfirmed";
};

type ApiResponse = {
  movies: Movie[];
  source: "d1" | "preview";
  generatedAt: string;
};

const fallback: Movie[] = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", releaseDate: "2026-09-18", verificationStatus: "unconfirmed" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", releaseDate: "2026-09-19", verificationStatus: "supported" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", releaseDate: "2026-09-25", verificationStatus: "verified" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", releaseDate: "2026-10-02", verificationStatus: "unconfirmed" },
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(`${value}T00:00:00+05:30`));
}

function shortDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short" }).format(new Date(`${value}T00:00:00+05:30`));
}

function todayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function statusLabel(status: Movie["verificationStatus"]) {
  if (status === "verified") return "Officially verified";
  if (status === "supported") return "Supported";
  return "Date tracking";
}

function periodLabel(period: string) {
  if (period === "upcoming") return "Upcoming";
  if (period === "all") return "All tracked releases";
  return `${period} releases`;
}

export default function App() {
  const [movies, setMovies] = useState<Movie[]>(fallback);
  const [source, setSource] = useState<ApiResponse["source"]>("preview");
  const [activeLanguage, setActiveLanguage] = useState("All");
  const [activePeriod, setActivePeriod] = useState("upcoming");
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
        setSource(data.source);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const today = todayKey();
  const years = useMemo(
    () => Array.from(new Set(movies.map((movie) => movie.releaseDate.slice(0, 4)))).sort(),
    [movies],
  );
  const upcomingCount = useMemo(() => movies.filter((movie) => movie.releaseDate >= today).length, [movies, today]);
  const yearCounts = useMemo(() => {
    const counts = new Map<string, number>();
    movies.forEach((movie) => counts.set(movie.releaseDate.slice(0, 4), (counts.get(movie.releaseDate.slice(0, 4)) ?? 0) + 1));
    return counts;
  }, [movies]);

  const periodMovies = useMemo(() => {
    if (activePeriod === "all") return movies;
    if (activePeriod === "upcoming") return movies.filter((movie) => movie.releaseDate >= today);
    return movies.filter((movie) => movie.releaseDate.startsWith(`${activePeriod}-`));
  }, [activePeriod, movies, today]);

  const languages = useMemo(
    () => ["All", ...Array.from(new Set(periodMovies.map((movie) => movie.language || "Unknown"))).sort()],
    [periodMovies],
  );
  const filtered = useMemo(
    () => activeLanguage === "All" ? periodMovies : periodMovies.filter((movie) => (movie.language || "Unknown") === activeLanguage),
    [activeLanguage, periodMovies],
  );
  const hero = useMemo(
    () => movies.find((movie) => movie.releaseDate >= today) ?? movies[0],
    [movies, today],
  );

  useEffect(() => {
    if (!languages.includes(activeLanguage)) setActiveLanguage("All");
  }, [activeLanguage, languages]);

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
          {source === "d1" ? `${upcomingCount} upcoming · ${movies.length} tracked` : loading ? "Connecting…" : "Preview catalogue"}
        </div>
      </header>

      <section className="hero">
        <div className="hero-kicker">INDIA · RELEASE CALENDAR</div>
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Next on the calendar</p>
            <h1>{hero?.title ?? "Cinema, beautifully timed."}</h1>
            {hero && <p className="hero-date">{formatDate(hero.releaseDate)}</p>}
            <p className="hero-summary">One calm place for movie names and release dates — sourced from open data and verified against official announcements where possible.</p>
            <div className="hero-actions">
              <a href="#releases" className="primary-action">Explore releases</a>
              <span className="verification-pill">{hero ? statusLabel(hero.verificationStatus) : "Tracking"}</span>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <div className="frame frame-a" />
            <div className="frame frame-b" />
            <div className="frame frame-c" />
            <div className="hero-monogram">C&S</div>
          </div>
        </div>
      </section>

      <section className="language-strip" aria-label="Choose release period">
        <button className={activePeriod === "upcoming" ? "chip active" : "chip"} onClick={() => setActivePeriod("upcoming")}>
          Upcoming · {upcomingCount}
        </button>
        {years.map((year) => (
          <button key={year} className={activePeriod === year ? "chip active" : "chip"} onClick={() => setActivePeriod(year)}>
            {year} · {yearCounts.get(year) ?? 0}
          </button>
        ))}
        <button className={activePeriod === "all" ? "chip active" : "chip"} onClick={() => setActivePeriod("all")}>
          All · {movies.length}
        </button>
      </section>

      <section className="language-strip" aria-label="Filter by language">
        {languages.map((language) => (
          <button
            key={language}
            className={language === activeLanguage ? "chip active" : "chip"}
            onClick={() => setActiveLanguage(language)}
          >
            {language}
          </button>
        ))}
      </section>

      <section id="releases" className="release-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Release desk</p>
            <h2>{periodLabel(activePeriod)}</h2>
          </div>
          <p>{filtered.length} shown · {movies.length} total tracked</p>
        </div>

        <div className="release-list">
          {filtered.map((movie, index) => (
            <article className="release-card" key={movie.id}>
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
              </div>
              <div className="card-index">{String(index + 1).padStart(2, "0")}</div>
            </article>
          ))}
          {!filtered.length && (
            <div className="calendar-banner">
              <p className="eyebrow">No matching releases yet</p>
              <h2>We’re still tracking this slice.</h2>
              <p>Try another year or language while the scheduled catalogue refresh continues to add release-date candidates.</p>
            </div>
          )}
        </div>
      </section>

      <section className="calendar-banner">
        <p className="eyebrow">Built for clarity</p>
        <h2>{movies.length} names and dates, without the noise.</h2>
        <p>Upcoming is only one view. Use the year and All filters above to browse the complete tracked catalogue while official-source verification grows.</p>
      </section>

      <footer>
        <span>Cinema & Series</span>
        <span>Fast V1 · 2026</span>
      </footer>
    </main>
  );
}
