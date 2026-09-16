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

function statusLabel(status: Movie["verificationStatus"]) {
  if (status === "verified") return "Officially verified";
  if (status === "supported") return "Supported";
  return "Date tracking";
}

export default function App() {
  const [movies, setMovies] = useState<Movie[]>(fallback);
  const [source, setSource] = useState<ApiResponse["source"]>("preview");
  const [activeLanguage, setActiveLanguage] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/movies", { signal: controller.signal })
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

  const languages = useMemo(() => ["All", ...Array.from(new Set(movies.map((movie) => movie.language)))], [movies]);
  const filtered = useMemo(
    () => activeLanguage === "All" ? movies : movies.filter((movie) => movie.language === activeLanguage),
    [activeLanguage, movies],
  );
  const hero = filtered[0] ?? movies[0];

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
          {source === "d1" ? "Live catalogue" : loading ? "Connecting…" : "Preview catalogue"}
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
            <h2>Upcoming</h2>
          </div>
          <p>{filtered.length} tracked release{filtered.length === 1 ? "" : "s"}</p>
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
                  <span>{movie.language}</span>
                  <span className={`status ${movie.verificationStatus}`}>{statusLabel(movie.verificationStatus)}</span>
                </div>
                <h3>{movie.title}</h3>
                {movie.nativeTitle && movie.nativeTitle !== movie.title && <p className="native-title">{movie.nativeTitle}</p>}
              </div>
              <div className="card-index">{String(index + 1).padStart(2, "0")}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="calendar-banner">
        <p className="eyebrow">Built for clarity</p>
        <h2>Names. Dates. Nothing noisy.</h2>
        <p>The catalogue layer stays intentionally small so the data can be checked, refreshed and corrected quickly.</p>
      </section>

      <footer>
        <span>Cinema & Series</span>
        <span>Fast V1 · 2026</span>
      </footer>
    </main>
  );
}
