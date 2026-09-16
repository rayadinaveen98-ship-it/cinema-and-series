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
};

type StatsRow = {
  total: number;
  verified: number;
  supported: number;
  unconfirmed: number;
};

const previewMovies = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", releaseDate: "2026-09-18", verificationStatus: "unconfirmed", releaseSource: "preview" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", releaseDate: "2026-09-19", verificationStatus: "supported", releaseSource: "preview" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", releaseDate: "2026-09-25", verificationStatus: "verified", releaseSource: "official" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", releaseDate: "2026-10-02", verificationStatus: "unconfirmed", releaseSource: "preview" },
];

function json(data: unknown, status = 200) {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": "public, max-age=60, s-maxage=300" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/health") {
      return json({ ok: true, database: Boolean(env.DB), now: new Date().toISOString() });
    }

    if (url.pathname === "/api/movies") {
      if (!env.DB) {
        return json({
          movies: previewMovies,
          source: "preview",
          generatedAt: new Date().toISOString(),
          stats: { total: previewMovies.length, verified: 1, supported: 1, unconfirmed: 2, activeSources: 0 },
        });
      }

      const scope = url.searchParams.get("scope") ?? "upcoming";
      const requestedYear = url.searchParams.get("year");
      let result;

      const columns = "id, wikidata_qid, title, native_title, language_name, release_date, verification_status, release_date_source";

      if (scope === "all") {
        result = await env.DB.prepare(
          `SELECT ${columns}
           FROM movies
           ORDER BY release_date ASC, title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).all<MovieRow>();
      } else if (requestedYear && /^\d{4}$/.test(requestedYear)) {
        result = await env.DB.prepare(
          `SELECT ${columns}
           FROM movies
           WHERE release_date BETWEEN ?1 AND ?2
           ORDER BY release_date ASC, title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).bind(`${requestedYear}-01-01`, `${requestedYear}-12-31`).all<MovieRow>();
      } else {
        const from = url.searchParams.get("from") ?? new Date().toISOString().slice(0, 10);
        const to = url.searchParams.get("to") ?? new Date(Date.now() + 730 * 86400000).toISOString().slice(0, 10);
        result = await env.DB.prepare(
          `SELECT ${columns}
           FROM movies
           WHERE release_date BETWEEN ?1 AND ?2
           ORDER BY release_date ASC, title COLLATE NOCASE ASC
           LIMIT 1000`,
        ).bind(from, to).all<MovieRow>();
      }

      const [statsResult, sourcesResult] = await Promise.all([
        env.DB.prepare(
          `SELECT
             COUNT(*) AS total,
             COALESCE(SUM(CASE WHEN verification_status='verified' THEN 1 ELSE 0 END), 0) AS verified,
             COALESCE(SUM(CASE WHEN verification_status='supported' THEN 1 ELSE 0 END), 0) AS supported,
             COALESCE(SUM(CASE WHEN verification_status='unconfirmed' THEN 1 ELSE 0 END), 0) AS unconfirmed
           FROM movies`,
        ).first<StatsRow>(),
        env.DB.prepare("SELECT COUNT(*) AS count FROM source_channels WHERE active=1").first<{ count: number }>(),
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
      }));

      return json({
        movies,
        source: "d1",
        generatedAt: new Date().toISOString(),
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
