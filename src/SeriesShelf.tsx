import { useEffect, useState } from "react";
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
type SeriesResponse = {
  series: SeriesTitle[];
  pagination?: { limit: number; offset: number; total: number; hasMore: boolean };
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
  unknown: "Status not available",
  upcoming: "Upcoming",
  ongoing: "Ongoing",
  ended: "Ended",
  limited: "Limited series",
};

function kindLabel(kind: SeriesKind) { return kindLabels[kind] ?? "Series"; }
function initial(title: string) { return title.trim().slice(0, 1).toUpperCase() || "S"; }
function countryLabel(code?: string) {
  const names: Record<string, string> = { IN: "India", US: "United States", GB: "United Kingdom", KR: "South Korea", JP: "Japan", CN: "China", CA: "Canada", AU: "Australia", FR: "France", DE: "Germany", ES: "Spain", BR: "Brazil", MX: "Mexico", PK: "Pakistan", BD: "Bangladesh", TR: "Turkey" };
  return !code ? "" : names[code] ?? code;
}
function seriesMeta(item: SeriesTitle) {
  return [item.firstAirYear ? String(item.firstAirYear) : "", item.language && item.language !== "Unknown" ? item.language : "", countryLabel(item.countryCode)].filter(Boolean).join(" · ");
}

export default function SeriesShelf() {
  const [mountNode, setMountNode] = useState<HTMLDivElement | null>(null);
  const [series, setSeries] = useState<SeriesTitle[]>([]);
  const [counts, setCounts] = useState<CatalogueCounts>({ movies: 0, series: 0, total: 0 });
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
    setLoading(true);
    fetch("/api/series?limit=24&offset=0", { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error("Series API unavailable"); return response.json() as Promise<SeriesResponse>; })
      .then((payload) => setSeries(payload.series ?? []))
      .catch(() => undefined)
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

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

  if (!mountNode) return null;

  return createPortal(
    <>
      <section id="series" className="series-zone" aria-label="Series catalogue">
        <div className="series-zone-heading">
          <h2>Series</h2>
          <span>{counts.series.toLocaleString("en-IN")} titles</span>
        </div>

        {loading ? (
          <div className="series-rail series-loading">{Array.from({ length: 7 }).map((_, index) => <div className="series-skeleton" key={index} />)}</div>
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
                <div className="series-card-art" aria-hidden="true"><span>{initial(item.title)}</span></div>
                <div className="series-card-copy">
                  <strong>{item.title}</strong>
                  <small>{seriesMeta(item) || kindLabel(item.seriesKind)}</small>
                </div>
              </button>
            ))}
          </div>
        ) : null}
      </section>

      {selectedSeries ? (
        <div className="series-detail-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedSeries(null); }}>
          <article className="series-detail-sheet" role="dialog" aria-modal="true" aria-labelledby="series-detail-title">
            <header className="series-detail-hero">
              <span className="series-detail-monogram" aria-hidden="true">{initial(selectedSeries.title)}</span>
              <button className="series-detail-close" type="button" onClick={() => setSelectedSeries(null)} aria-label="Close series details">×</button>
              <div className="series-detail-heading">
                <p>{kindLabel(selectedSeries.seriesKind)}</p>
                <h2 id="series-detail-title">{selectedSeries.title}</h2>
                <div className="series-detail-meta">
                  {selectedSeries.firstAirYear ? <span>{selectedSeries.firstAirYear}</span> : null}
                  {selectedSeries.language && selectedSeries.language !== "Unknown" ? <span>{selectedSeries.language}</span> : null}
                  {selectedSeries.countryCode ? <span>{countryLabel(selectedSeries.countryCode)}</span> : null}
                </div>
              </div>
            </header>

            <div className="series-detail-body">
              <div className="series-detail-grid" aria-label="Series metadata">
                <div className="series-detail-stat"><small>Type</small><strong>{kindLabel(selectedSeries.seriesKind)}</strong></div>
                <div className="series-detail-stat"><small>Status</small><strong>{lifecycleLabels[selectedSeries.lifecycleStatus]}</strong></div>
                <div className="series-detail-stat"><small>Seasons</small><strong>{selectedSeries.seasonCount ?? "—"}</strong></div>
                <div className="series-detail-stat"><small>Episodes</small><strong>{selectedSeries.episodeCount ?? "—"}</strong></div>
              </div>

              {(selectedSeries.sourceUrl || selectedSeries.wikidataQid) ? (
                <section className="series-detail-section" aria-label="Source references">
                  <h3>Sources</h3>
                  <div className="series-detail-sources">
                    {selectedSeries.sourceUrl ? <a className="series-detail-source" href={selectedSeries.sourceUrl} target="_blank" rel="noreferrer noopener">Wikipedia ↗</a> : null}
                    {selectedSeries.wikidataQid ? <a className="series-detail-source" href={`https://www.wikidata.org/wiki/${selectedSeries.wikidataQid}`} target="_blank" rel="noreferrer noopener">Wikidata ↗</a> : null}
                  </div>
                </section>
              ) : null}
            </div>
          </article>
        </div>
      ) : null}
    </>,
    mountNode,
  );
}
