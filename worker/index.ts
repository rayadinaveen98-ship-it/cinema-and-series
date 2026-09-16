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
};

const previewMovies = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", releaseDate: "2026-09-18", verificationStatus: "unconfirmed" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", releaseDate: "2026-09-19", verificationStatus: "supported" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", releaseDate: "2026-09-25", verificationStatus: "verified" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", releaseDate: "2026-10-02", verificationStatus: "unconfirmed" },
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
        return json({ movies: previewMovies, source: "preview", generatedAt: new Date().toISOString() });
      }

      const from = url.searchParams.get("from") ?? new Date(Date.now() - 14 * 86400000).toISOString().slice(0, 10);
      const to = url.searchParams.get("to") ?? new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10);

      const result = await env.DB.prepare(
        `SELECT id, wikidata_qid, title, native_title, language_name, release_date, verification_status
         FROM movies
         WHERE release_date BETWEEN ?1 AND ?2
         ORDER BY release_date ASC, title COLLATE NOCASE ASC
         LIMIT 250`,
      ).bind(from, to).all<MovieRow>();

      const movies = result.results.map((movie) => ({
        id: movie.id,
        wikidataQid: movie.wikidata_qid ?? undefined,
        title: movie.title,
        nativeTitle: movie.native_title ?? undefined,
        language: movie.language_name,
        releaseDate: movie.release_date,
        verificationStatus: movie.verification_status,
      }));

      return json({ movies, source: "d1", generatedAt: new Date().toISOString() });
    }

    return new Response(null, { status: 404 });
  },
} satisfies ExportedHandler<Env>;
