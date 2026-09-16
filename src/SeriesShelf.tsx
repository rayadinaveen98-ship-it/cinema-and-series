import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import "./series-details.css";

type SeriesKind = "series" | "web_series" | "miniseries" | "anthology" | "unknown";
type SeriesTitle = {
  id: string;
  wikidataQid?: string;
  wikipediaPageId?: number;
  title: string;
  nativeTitle?: string;
  seriesKind: SeriesKind;
  language: string;
  countryCode?: string;
  firstAirYear?: number;
  lastAirYear?: number;
  lifecycleStatus: "unknown" | "upcoming" | "ongoing" | "ended" | "limited";
  seasonCount?: number;
  episodeCount?: number;
  verificationStatus: "verified" | "supported" | "unconfirmed";
  sourceCategory?: string;
  sourceUrl?: string;
};
type FacetValue = { value: string; count: number };
type SeriesResponse = {
  series: SeriesTitle[];
  pagination?: { limit: number; offset: number; total: number; hasMore: boolean };
  facets?: { years: FacetValue[]; languages: FacetValue[]; countries: FacetValue[]; kinds: FacetValue[] };
  stats?: { total: number; withFirstAirYear: number; webSeries: number; miniseries: number };
};
type CatalogueCounts = { movies: number; series: number; total: number };

const kindLabels: Record<SeriesKind, string> = {
  series: "Series",
  web_series: "Web Series",
  miniseries: "Miniseries",
  anthology: "Anthology",
  unknown: "Series",
};

const lifecycleLabels: Record<SeriesTitle["lifecycleStatus"], string> = {
  unknown: "Not classified yet",
  upcoming: "Upcoming",
  ongoing: "Ongoing",
  ended: "Ended",
  limited: "Limited series",
};

function kindLabel(kind: SeriesKind) { return kindLabels[kind] ?? "Series"; }
function initial(title: string) { return title.trim().slice(0, 1).toUpperCase() || "S"; }

export default function SeriesShelf() {
  const [mountNode, setMountNode] = useState<HTMLDivElement | null>(null);
  const [series, setSeries] = useState<SeriesTitle[]>([]);
  const [counts, setCounts] = useState<CatalogueCounts>({ movies: 0, series: 0, total: 0 });
  const [facets, setFacets] = useState<SeriesResponse["facets"]>();
  const [activeKind, setActiveKind] = useState("all");
  const [activeLanguage, setActiveLanguage] = useState("all");
  const [selectedSeries, setSelectedSeries] = useState<SeriesTitle | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stage = document.querySelector(".content-stage");
    const browse = document.querySelector("#browse");
    if (!stage) return;
    const node = document.createElement("div");
    node.dataset.seriesPortal = "true";
    if (browse?.parentElement === stage) stage.insertBefore(node, browse);
    else stage.appendChild(node);
    setMountNode(node);
    return () => node.remove();
  }, []);

  useEffect(() => {
    fetch("/api/catalogue-stats")
      .then((response) => response.ok ? response.json() as Promise<CatalogueCounts> : Promise.reject())
      .then(setCounts)
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ limit: "24", offset: "0" });
    if (activeKind !== "all") params.set("kind", activeKind);
    if (activeLanguage !== "all") params.set("language", activeLanguage);
    setLoading(true);
    fetch(`/api/series?${params}`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Series API unavailable"); return response.json() as Promise<SeriesResponse>; })
      .then((payload) => {
        setSeries(payload.series ?? []);
        setFacets(payload.facets);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [activeKind, activeLanguage]);

  useEffect(() => {
    if (!selectedSeries) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSelectedSeries(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [selectedSeries]);

  const kindOptions = useMemo(() => facets?.kinds?.filter((item) => item.value !== "unknown").slice(0, 5) ?? [], [facets]);
  const languageOptions = useMemo(() => facets?.languages?.filter((item) => item.value !== "Unknown").slice(0, 8) ?? [], [facets]);

  if (!mountNode) return null;

  return createPortal(
    <>
      <section id="series" className="series-zone" aria-label="Series catalogue">
        <div className="series-zone-heading">
          <div>
            <p>SERIES ENGINE V1</p>
            <h2>Series to discover</h2>
            <span>Separate SeriesRun identities — not movie rows with a different label.</span>
          </div>
          <div className="media-counts" aria-label="Catalogue media counts">
            <b>{counts.movies.toLocaleString("en-IN")}<small>Movies</small></b>
            <i />
            <b>{counts.series.toLocaleString("en-IN")}<small>Series</small></b>
            <i />
            <b>{counts.total.toLocaleString("en-IN")}<small>All titles</small></b>
          </div>
        </div>

        <div className="series-filter-row" aria-label="Series kind filters">
          <button className={activeKind === "all" ? "active" : ""} onClick={() => setActiveKind("all")}>All series</button>
          {kindOptions.map((item) => (
            <button key={item.value} className={activeKind === item.value ? "active" : ""} onClick={() => setActiveKind(item.value)}>
              {kindLabel(item.value as SeriesKind)} <span>{item.count}</span>
            </button>
          ))}
        </div>

        <div className="series-filter-row language-row" aria-label="Series language filters">
          <button className={activeLanguage === "all" ? "active" : ""} onClick={() => setActiveLanguage("all")}>All languages</button>
          {languageOptions.map((item) => (
            <button key={item.value} className={activeLanguage === item.value ? "active" : ""} onClick={() => setActiveLanguage(item.value)}>
              {item.value}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="series-rail series-loading">{Array.from({ length: 8 }).map((_, index) => <div className="series-skeleton" key={index} />)}</div>
        ) : series.length ? (
          <div className="series-rail">
            {series.map((item) => (
              <button
                type="button"
                className="series-card"
                key={item.id}
                onClick={() => setSelectedSeries(item)}
                aria-label={`Open ${item.title} details`}
              >
                <div className="series-card-art" aria-hidden="true"><span>{initial(item.title)}</span><em>{kindLabel(item.seriesKind)}</em></div>
                <div className="series-card-copy">
                  <strong>{item.title}</strong>
                  <p>{item.firstAirYear ? `Since ${item.firstAirYear}` : "First-air year not asserted"}</p>
                  <small>{item.language || "Unknown language"} · {item.countryCode || "Global"}</small>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="series-empty"><strong>No series in this slice yet.</strong><span>Try another kind or language.</span></div>
        )}
      </section>

      {selectedSeries ? (
        <div
          className="series-detail-backdrop"
          role="presentation"
          onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedSeries(null); }}
        >
          <article className="series-detail-sheet" role="dialog" aria-modal="true" aria-labelledby="series-detail-title">
            <header className="series-detail-hero">
              <span className="series-detail-monogram" aria-hidden="true">{initial(selectedSeries.title)}</span>
              <button className="series-detail-close" type="button" onClick={() => setSelectedSeries(null)} aria-label="Close series details">×</button>
              <div className="series-detail-heading">
                <p>CINEMA &amp; SERIES · {kindLabel(selectedSeries.seriesKind)}</p>
                <h2 id="series-detail-title">{selectedSeries.title}</h2>
                <div className="series-detail-meta">
                  <span>{selectedSeries.firstAirYear ?? "Year not asserted"}</span>
                  <span>{selectedSeries.language || "Language unknown"}</span>
                  <span>{selectedSeries.countryCode || "Country unknown"}</span>
                  <span>{selectedSeries.verificationStatus}</span>
                </div>
              </div>
            </header>

            <div className="series-detail-body">
              <p className="series-detail-summary">
                This is the Cinema &amp; Series canonical detail view for this SeriesRun. The information shown here comes from our catalogue metadata; richer verified story, cast, platform, season and episode information will appear here as those engines are ingested.
              </p>

              <div className="series-detail-grid" aria-label="Series metadata">
                <div className="series-detail-stat"><small>Type</small><strong>{kindLabel(selectedSeries.seriesKind)}</strong></div>
                <div className="series-detail-stat"><small>Status</small><strong>{lifecycleLabels[selectedSeries.lifecycleStatus]}</strong></div>
                <div className="series-detail-stat"><small>Seasons</small><strong>{selectedSeries.seasonCount ?? "—"}</strong></div>
                <div className="series-detail-stat"><small>Episodes</small><strong>{selectedSeries.episodeCount ?? "—"}</strong></div>
              </div>

              <section className="series-detail-section" aria-label="Source evidence">
                <h3>Sources</h3>
                <p>External references are evidence for our catalogue. They no longer replace the Cinema &amp; Series detail experience.</p>
                <div className="series-detail-sources">
                  {selectedSeries.sourceUrl ? (
                    <a className="series-detail-source" href={selectedSeries.sourceUrl} target="_blank" rel="noreferrer noopener">Wikipedia source ↗</a>
                  ) : null}
                  {selectedSeries.wikidataQid ? (
                    <a className="series-detail-source" href={`https://www.wikidata.org/wiki/${selectedSeries.wikidataQid}`} target="_blank" rel="noreferrer noopener">Wikidata {selectedSeries.wikidataQid} ↗</a>
                  ) : null}
                  {!selectedSeries.sourceUrl && !selectedSeries.wikidataQid ? <span className="series-detail-empty-source">No external source link is exposed for this record yet.</span> : null}
                </div>
              </section>
            </div>
          </article>
        </div>
      ) : null}
    </>,
    mountNode,
  );
}
