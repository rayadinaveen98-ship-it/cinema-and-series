import test from "node:test";
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";

const bundled = await build({
  entryPoints: [fileURLToPath(new URL("../worker/index.ts", import.meta.url))],
  bundle: true,
  platform: "neutral",
  format: "esm",
  write: false,
});
const worker = (await import("data:text/javascript;base64," + Buffer.from(bundled.outputFiles[0].text).toString("base64"))).default;

function fakeDb(artworkRow = null) {
  const queries = [];
  const film = {
    id: "movie-1", wikidata_qid: null, title: "Film", native_title: null,
    language_name: "Telugu", country_code: "IN", release_date: null,
    release_year: 2026, date_precision: "year", verification_status: "supported",
    release_date_source: "wikipedia", release_source_name: "English Wikipedia",
    release_source_url: "https://en.wikipedia.org/wiki/Film", poster_url: null,
    backdrop_url: null, artwork_source: null, artwork_source_url: null,
    official_observation_url: null, updated_at: "2026-10-18 00:00:00",
  };
  const show = {
    id: "series-1", wikidata_qid: null, wikipedia_page_id: null, title: "Show",
    native_title: null, series_kind: "series", language_name: "Telugu",
    country_code: "IN", first_air_year: 2026, last_air_year: null,
    lifecycle_status: "ongoing", season_count: 1, episode_count: 8,
    source_category: "wikipedia", source_url: "https://en.wikipedia.org/wiki/Show",
    poster_url: null, backdrop_url: null, verification_status: "supported", updated_at: null,
  };
  const db = {
    prepare(sql) {
      queries.push(sql);
      return {
        bind() { return this; },
        async all() {
          if (sql.includes("FROM title_artwork_links")) return { results: artworkRow ? [artworkRow] : [] };
          if (sql.includes("SELECT c.* FROM combined_catalogue")) return { results: [film] };
          if (sql.includes("SELECT s.* FROM series_titles")) return { results: [show] };
          return { results: [] };
        },
        async first() {
          if (sql.includes("COUNT(*) AS count")) return { count: 1, latest_updated_at: null };
          if (sql.includes("COUNT(*) AS total") && sql.includes("FROM series_titles"))
            return { total: 1, with_first_air_year: 1, web_series: 0, miniseries: 0, latest_updated_at: null };
          if (sql.includes("COUNT(*) AS total"))
            return { total: 1, verified: 0, supported: 1, unconfirmed: 0, latest_updated_at: null };
          return { upcoming: 0, next_7_days: 0, next_30_days: 0 };
        },
      };
    },
  };
  return { db, queries };
}

async function request(path, artworkRow = null) {
  const { db, queries } = fakeDb(artworkRow);
  // POST bypasses Worker edge caching for an isolated query-plan test;
  // handleRequest uses identical routing for GET and POST.
  const response = await worker.fetch(new Request("https://cinema.test" + path, { method: "POST" }), { DB: db }, { waitUntil() {} });
  assert.equal(response.status, 200);
  return { data: await response.json(), queries };
}

test("Movie page-only uses 2 catalogue statements + 1 page-local artwork lookup", async () => {
  const { data, queries } = await request("/api/movies?scope=all&limit=60&offset=60&meta=0");
  assert.equal(queries.length, 3);
  assert.equal(queries.filter((sql) => sql.includes("FROM title_artwork_links")).length, 1);
  assert.equal(data.movies.length, 1);
  assert.deepEqual(data.pagination, { limit: 60, offset: 60, total: 1, hasMore: false });
  assert.equal(data.metadataLevel, "page-only");
  assert.equal(Object.hasOwn(data, "facets"), false);
  assert.equal(Object.hasOwn(data, "stats"), false);
  assert.equal(Object.hasOwn(data, "periodCounts"), false);
});
test("Movie legacy full metadata remains backward compatible", async () => {
  const { data, queries } = await request("/api/movies?scope=all&limit=60");
  assert.equal(queries.length, 9);
  assert.equal(data.metadataLevel, "full");
  assert.ok(data.facets);
  assert.ok(data.stats);
  assert.ok(data.periodCounts);
});
test("Series page-only uses 2 catalogue statements + 1 bounded artwork lookup", async () => {
  const { data, queries } = await request("/api/series?limit=18&meta=0");
  assert.equal(queries.length, 3);
  assert.equal(queries.filter((sql) => sql.includes("FROM title_artwork_links")).length, 1);
  assert.equal(data.series.length, 1);
  assert.equal(data.metadataLevel, "page-only");
  assert.equal(Object.hasOwn(data, "facets"), false);
  assert.equal(Object.hasOwn(data, "stats"), false);
});
test("Series full metadata still returns all expected keys", async () => {
  const { data, queries } = await request("/api/series?limit=60");
  assert.equal(queries.length, 8);
  assert.equal(data.metadataLevel, "full");
  assert.ok(data.facets?.kinds);
  assert.equal(data.stats.total, 1);
});

test("Approved open-license movie image returns both poster and clickable license credit", async () => {
  const row = {
    source_id: "movie-1", presentation_role: "poster",
    asset_id: "commons-vrt-sample", asset_type: "poster",
    source_key: "wikimedia_commons_vrt", source_asset_id: "Poster.jpg",
    source_page_url: "https://commons.wikimedia.org/wiki/File:Poster.jpg",
    delivery_url: "https://thumb.wikimedia.org/wikipedia/commons/film.jpg",
    rights_reference: "https://creativecommons.org/licenses/by-sa/4.0/",
    language_code: "", territory_code: "",
    publication_state: "OPEN_LICENSE_VERIFIED",
    rights_basis: "OPEN_LICENSE", hosting_mode: "PROVIDER_CDN",
    attribution_required: 1,
    attribution_text: "Film poster by rightsholder, CC BY-SA 4.0",
    rights_verified_at: "2026-10-20T00:00:00Z",
    valid_from: null, valid_until: null, takedown_status: "clear",
    width: 680, height: 890, aspect_ratio: 0.764, quality_score: 1,
  };
  const { data, queries } = await request("/api/movies?scope=all&limit=10&meta=0", row);
  assert.equal(queries.filter((sql) => sql.includes("FROM title_artwork_links")).length, 1);
  assert.equal(data.movies[0].posterUrl, row.delivery_url);
  assert.equal(data.movies[0].artworkSource, row.source_key);
  assert.equal(data.movies[0].artworkAttribution, row.attribution_text);
  assert.equal(data.movies[0].artworkLicenseUrl, row.rights_reference);
});
