import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

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

function kindLabel(kind: SeriesKind) { return kindLabels[kind] ?? "Series"; }
function initial(title: string) { return title.trim().slice(0, 1).toUpperCase() || "S"; }

export default function SeriesShelf() {
  const [mountNode, setMountNode] = useState<HTMLDivElement | null>(null);
  const [series, setSeries] = useState<SeriesTitle[]>([]);
  const [counts, setCounts] = useState<CatalogueCounts>({ movies: 0, series: 0, total: 0 });
  const [facets, setFacets] = useState<SeriesResponse["facets"]>();
  const [activeKind, setActiveKind] = useState("all");
  const [activeLanguage, setActiveLanguage] = useState("all");
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

  const kindOptions = useMemo(() => facets?.kinds?.filter((item) => item.value !== "unknown").slice(0, 5) ?? [], [facets]);
  const languageOptions = useMemo(() => facets?.languages?.filter((item) => item.value !== "Unknown").slice(0, 8) ?? [], [facets]);

  if (!mountNode) return null;

  return createPortal(
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
            <a className="series-card" key={item.id} href={item.sourceUrl || "#series"} target={item.sourceUrl ? "_blank" : undefined} rel={item.sourceUrl ? "noreferrer noopener" : undefined}>
              <div className="series-card-art" aria-hidden="true"><span>{initial(item.title)}</span><em>{kindLabel(item.seriesKind)}</em></div>
              <div className="series-card-copy">
                <strong>{item.title}</strong>
                <p>{item.firstAirYear ? `Since ${item.firstAirYear}` : "First-air year not asserted"}</p>
                <small>{item.language || "Unknown language"} · {item.countryCode || "Global"}</small>
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div className="series-empty"><strong>No series in this slice yet.</strong><span>Try another kind or language.</span></div>
      )}
    </section>,
    mountNode,
  );
}
