import baseWorker from "./index";

interface Env {
  DB?: D1Database;
}

type OnThisDayRow = {
  id: string;
  wikidata_qid: string | null;
  title: string;
  native_title: string | null;
  language_name: string;
  country_code: string;
  release_date: string;
  verification_status: "verified" | "supported" | "unconfirmed";
  release_date_source: string;
  poster_url: string | null;
  backdrop_url: string | null;
};

function json(data: unknown, status = 200, cacheControl = "public, max-age=300, s-maxage=900") {
  return Response.json(data, { status, headers: { "Cache-Control": cacheControl } });
}

function indiaDateKey(date = new Date()) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(date).map(({ type, value }) => [type, value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function boundedInteger(value: string | null, fallback: number, minimum: number, maximum: number) {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(maximum, Math.max(minimum, parsed));
}

function validDate(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

async function onThisDay(request: Request, env: Env) {
  if (!env.DB) {
    return json({ error: "database_unavailable" }, 503, "no-store");
  }

  const url = new URL(request.url);
  const selectedDate = (url.searchParams.get("date") ?? indiaDateKey()).trim();
  if (!validDate(selectedDate)) {
    return json({ error: "date must use YYYY-MM-DD" }, 400, "no-store");
  }

  const language = (url.searchParams.get("language") ?? "").trim().slice(0, 80);
  const limit = boundedInteger(url.searchParams.get("limit"), 60, 1, 200);
  const monthDay = selectedDate.slice(5);
  const selectedYear = Number.parseInt(selectedDate.slice(0, 4), 10);

  const conditions = [
    "substr(m.release_date, 6, 5) = ?1",
    "m.release_date <= ?2",
    "(m.wikidata_qid IS NULL OR m.title <> m.wikidata_qid)",
  ];
  const bindings: (string | number)[] = [monthDay, selectedDate];
  if (language) {
    conditions.push(`m.language_name = ?${bindings.length + 1}`);
    bindings.push(language);
  }
  bindings.push(limit);

  const result = await env.DB.prepare(
    `SELECT m.id, m.wikidata_qid, m.title, m.native_title, m.language_name, m.country_code,
            m.release_date, m.verification_status, m.release_date_source,
            m.poster_url, m.backdrop_url
       FROM movies m
      WHERE ${conditions.join(" AND ")}
      ORDER BY m.release_date DESC, m.title COLLATE NOCASE ASC
      LIMIT ?${bindings.length}`,
  ).bind(...bindings).all<OnThisDayRow>();

  const movies = result.results.map((movie) => {
    const releaseYear = Number.parseInt(movie.release_date.slice(0, 4), 10);
    return {
      id: movie.id,
      wikidataQid: movie.wikidata_qid ?? undefined,
      title: movie.title,
      nativeTitle: movie.native_title ?? undefined,
      language: movie.language_name,
      countryCode: movie.country_code,
      releaseDate: movie.release_date,
      releaseYear,
      yearsAgo: Math.max(0, selectedYear - releaseYear),
      verificationStatus: movie.verification_status,
      releaseSource: movie.release_date_source,
      posterUrl: movie.poster_url ?? undefined,
      backdropUrl: movie.backdrop_url ?? undefined,
    };
  });

  return json({
    selectedDate,
    monthDay,
    movies,
    count: movies.length,
    source: "d1",
    generatedAt: new Date().toISOString(),
  });
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext) {
    const url = new URL(request.url);
    if (url.pathname === "/api/on-this-day") {
      if (request.method !== "GET") {
        return new Response(null, { status: 405, headers: { Allow: "GET" } });
      }
      return onThisDay(request, env);
    }

    return baseWorker.fetch(request as Parameters<typeof baseWorker.fetch>[0], env);
  },
} satisfies ExportedHandler<Env>;
