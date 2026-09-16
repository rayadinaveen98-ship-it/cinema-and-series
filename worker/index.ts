interface Env {
  DB?: D1Database;
}

type MovieRow = {
  id: string;
  wikidata_qid: string | null;
  title: string;
  native_title: string | null;
  language_name: string;
  release_date: string;
  verification_status: "verified" | "supported" | "unconfirmed";
  release_date_source: string;
  release_source_name: string | null;
};

type StatsRow = {
  total: number;
  verified: number;
  supported: number;
  unconfirmed: number;
  latest_updated_at: string | null;
};

type SourcesRow = {
  count: number;
  latest_updated_at: string | null;
};

const previewMovies = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", releaseDate: "2026-09-18", verificationStatus: "unconfirmed", releaseSource: "preview" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", releaseDate: "2026-09-19", verificationStatus: "supported", releaseSource: "preview" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", releaseDate: "2026-09-25", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", releaseDate: "2026-10-02", verificationStatus: "unconfirmed", releaseSource: "preview" },
];

const visibleMovieClause = "(m.wikidata_qid IS NULL OR m.title <> m.wikidata_qid)";
const movieColumns = `m.id, m.wikidata_qid, m.title, m.native_title, m.language_name, m.release_date,
  m.verification_status, m.release_date_source, s.source_name AS release_source_name`;
const movieSourceJoin = "LEFT JOIN source_channels s ON s.source_key = m.release_date_source";

function json(data: unknown, status = 200) {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": "public, max-age=60, s-maxage=300" },
  });
}

function d1TimestampToIso(value: string | null | undefined) {
  if (!value) return undefined;
  return `${value.replace(" ", "T")}Z`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/health") {
      return json({ ok: true, database: Boolean(env.DB), now: new Date().toISOString() });
    }

    if (url.pathname === "/api/movies") {
      if (!env.DB) {
        const now = new Date().toISOString();
        return json({
          movies: previewMovies,
          source: "preview",
          generatedAt: now,
          catalogueUpdatedAt: now,
          stats: { total: previewMovies.length, verified: 1, supported: 1, unconfirmed: 2, activeSources: 0 },
        });
      }

      const scope = url.searchParams.get("scope") ?? "upcoming";
      const requestedYear = url.searchParams.get("year");
      let result;

      if (scope === "all") {
        result = await env.DB.prepare(
          `SELECT ${movieColumns}
           FROM movies m
           ${movieSourceJoin}
           WHERE ${visibleMovieClause}
           ORDER BY m.release_date ASC, m.title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).all<MovieRow>();
      } else if (requestedYear && /^\d{4}$/.test(requestedYear)) {
        result = await env.DB.prepare(
          `SELECT ${movieColumns}
           FROM movies m
           ${movieSourceJoin}
           WHERE ${visibleMovieClause}
             AND m.release_date BETWEEN ?1 AND ?2
           ORDER BY m.release_date ASC, m.title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).bind(`${requestedYear}-01-01`, `${requestedYear}-12-31`).all<MovieRow>();
      } else {
        const from = url.searchParams.get("from") ?? new Date().toISOString().slice(0, 10);
        const to = url.searchParams.get("to") ?? new Date(Date.now() + 730 * 86400000).toISOString().slice(0, 10);
        result = await env.DB.prepare(
          `SELECT ${movieColumns}
           FROM movies m
           ${movieSourceJoin}
           WHERE ${visibleMovieClause}
             AND m.release_date BETWEEN ?1 AND ?2
           ORDER BY m.release_date ASC, m.title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).bind(from, to).all<MovieRow>();
      }

      const [statsResult, sourcesResult] = await Promise.all([
        env.DB.prepare(
          `SELECT
             COUNT(*) AS total,
             COALESCE(SUM(CASE WHEN verification_status='verified' THEN 1 ELSE 0 END), 0) AS verified,
             COALESCE(SUM(CASE WHEN verification_status='supported' THEN 1 ELSE 0 END), 0) AS supported,
             COALESCE(SUM(CASE WHEN verification_status='unconfirmed' THEN 1 ELSE 0 END), 0) AS unconfirmed,
             MAX(updated_at) AS latest_updated_at
           FROM movies
           WHERE (wikidata_qid IS NULL OR title <> wikidata_qid)`,
        ).first<StatsRow>(),
        env.DB.prepare(
          "SELECT COUNT(*) AS count, MAX(updated_at) AS latest_updated_at FROM source_channels WHERE active=1",
        ).first<SourcesRow>(),
      ]);

      const movies = result.results.map((movie) => ({
        id: movie.id,
        wikidataQid: movie.wikidata_qid ?? undefined,
        title: movie.title,
        nativeTitle: movie.native_title ?? undefined,
        language: movie.language_name,
        releaseDate: movie.release_date,
        verificationStatus: movie.verification_status,
        releaseSource: movie.release_date_source,
        releaseSourceName: movie.release_source_name ?? undefined,
      }));

      const latestUpdate = [statsResult?.latest_updated_at, sourcesResult?.latest_updated_at]
        .filter((value): value is string => Boolean(value))
        .sort()
        .at(-1);

      return json({
        movies,
        source: "d1",
        generatedAt: new Date().toISOString(),
        catalogueUpdatedAt: d1TimestampToIso(latestUpdate),
        stats: {
          total: Number(statsResult?.total ?? movies.length),
          verified: Number(statsResult?.verified ?? 0),
          supported: Number(statsResult?.supported ?? 0),
          unconfirmed: Number(statsResult?.unconfirmed ?? 0),
          activeSources: Number(sourcesResult?.count ?? 0),
        },
      });
    }

    return new Response(null, { status: 404 });
  },
} satisfies ExportedHandler<Env>;
