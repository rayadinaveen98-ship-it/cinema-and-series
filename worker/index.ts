interface Env {
  DB?: D1Database;
}

type MovieRow = {
  id: string;
  wikidata_qid: string | null;
  title: string;
  native_title: string | null;
  language_name: string;
  country_code: string;
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

type FacetRow = {
  value: string;
  count: number;
};

type PeriodCountsRow = {
  upcoming: number;
  next_7_days: number;
  next_30_days: number;
};

type ObservationRow = {
  id: number;
  source_key: string;
  source_name: string | null;
  external_id: string;
  external_url: string;
  title: string;
  published_at: string | null;
  candidate_release_date: string | null;
  candidate_dates_json: string;
  evidence_contexts_json: string;
  observed_at: string;
};

const previewMovies = [
  { id: "preview-1", title: "A Film in Production", language: "Telugu", countryCode: "IN", releaseDate: "2026-09-18", verificationStatus: "unconfirmed", releaseSource: "preview" },
  { id: "preview-2", title: "Festival Premiere", language: "Malayalam", countryCode: "IN", releaseDate: "2026-09-19", verificationStatus: "supported", releaseSource: "preview" },
  { id: "preview-3", title: "Theatrical Release", language: "Tamil", countryCode: "IN", releaseDate: "2026-09-25", verificationStatus: "verified", releaseSource: "official", releaseSourceName: "Official source" },
  { id: "preview-4", title: "Coming Soon", language: "Kannada", countryCode: "IN", releaseDate: "2026-10-02", verificationStatus: "unconfirmed", releaseSource: "preview" },
];

const visibleMovieClause = "(m.wikidata_qid IS NULL OR m.title <> m.wikidata_qid)";
const movieColumns = `m.id, m.wikidata_qid, m.title, m.native_title, m.language_name, m.country_code, m.release_date,
  m.verification_status, m.release_date_source, s.source_name AS release_source_name`;
const movieSourceJoin = "LEFT JOIN source_channels s ON s.source_key = m.release_date_source";

function json(data: unknown, status = 200, cacheControl = "public, max-age=60, s-maxage=300") {
  return Response.json(data, {
    status,
    headers: { "Cache-Control": cacheControl },
  });
}

function d1TimestampToIso(value: string | null | undefined) {
  if (!value) return undefined;
  return `${value.replace(" ", "T")}Z`;
}

function parseJsonArray(value: string | null | undefined): unknown[] {
  if (!value) return [];
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function boundedInteger(value: string | null, fallback: number, minimum: number, maximum: number) {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(maximum, Math.max(minimum, parsed));
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

function addDays(value: string, days: number) {
  const instant = new Date(`${value}T00:00:00Z`);
  instant.setUTCDate(instant.getUTCDate() + days);
  return instant.toISOString().slice(0, 10);
}

function facet(rows: FacetRow[]) {
  return rows.map((row) => ({ value: row.value, count: Number(row.count ?? 0) }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/health") {
      return json({ ok: true, database: Boolean(env.DB), now: new Date().toISOString() });
    }

    if (url.pathname === "/api/review-observations") {
      if (!env.DB) {
        return json(
          { observations: [], source: "preview", generatedAt: new Date().toISOString() },
          200,
          "no-store",
        );
      }

      const result = await env.DB.prepare(
        `SELECT o.id, o.source_key, s.source_name, o.external_id, o.external_url, o.title,
                o.published_at, o.candidate_release_date, o.candidate_dates_json,
                o.evidence_contexts_json, o.observed_at
         FROM source_observations o
         LEFT JOIN source_channels s ON s.source_key = o.source_key
         WHERE o.review_status = 'pending_review'
         ORDER BY COALESCE(o.candidate_release_date, '9999-12-31') ASC, o.observed_at DESC
         LIMIT 100`,
      ).all<ObservationRow>();

      return json(
        {
          observations: result.results.map((observation) => ({
            id: observation.id,
            sourceKey: observation.source_key,
            sourceName: observation.source_name ?? observation.source_key,
            externalId: observation.external_id,
            externalUrl: observation.external_url,
            title: observation.title,
            publishedAt: observation.published_at ?? undefined,
            candidateReleaseDate: observation.candidate_release_date ?? undefined,
            candidateDates: parseJsonArray(observation.candidate_dates_json),
            evidenceContexts: parseJsonArray(observation.evidence_contexts_json),
            observedAt: d1TimestampToIso(observation.observed_at),
          })),
          source: "d1",
          generatedAt: new Date().toISOString(),
        },
        200,
        "no-store",
      );
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
          pagination: { limit: previewMovies.length, offset: 0, total: previewMovies.length, hasMore: false },
          facets: {
            years: [{ value: "2026", count: previewMovies.length }],
            languages: [
              { value: "Kannada", count: 1 },
              { value: "Malayalam", count: 1 },
              { value: "Tamil", count: 1 },
              { value: "Telugu", count: 1 },
            ],
            countries: [{ value: "IN", count: previewMovies.length }],
          },
          periodCounts: { upcoming: previewMovies.length, next7Days: 1, next30Days: previewMovies.length },
        });
      }

      const scope = url.searchParams.get("scope") ?? "upcoming";
      const requestedYear = url.searchParams.get("year");
      const search = (url.searchParams.get("q") ?? "").trim().slice(0, 120);
      const language = (url.searchParams.get("language") ?? "").trim().slice(0, 80);
      const country = (url.searchParams.get("country") ?? "").trim().toUpperCase().slice(0, 3);
      const officialOnly = url.searchParams.get("official") === "1";
      const limit = boundedInteger(url.searchParams.get("limit"), 60, 1, 200);
      const offset = boundedInteger(url.searchParams.get("offset"), 0, 0, 100_000);
      const today = indiaDateKey();

      const conditions: string[] = [visibleMovieClause];
      const bindings: (string | number)[] = [];
      const bind = (value: string | number) => {
        bindings.push(value);
        return `?${bindings.length}`;
      };

      if (requestedYear && /^\d{4}$/.test(requestedYear)) {
        const start = `${requestedYear}-01-01`;
        const end = `${requestedYear}-12-31`;
        conditions.push(`m.release_date BETWEEN ${bind(start)} AND ${bind(end)}`);
      } else if (scope !== "all") {
        const from = url.searchParams.get("from") ?? today;
        const to = url.searchParams.get("to") ?? addDays(today, 730);
        if (!/^\d{4}-\d{2}-\d{2}$/.test(from) || !/^\d{4}-\d{2}-\d{2}$/.test(to)) {
          return json({ error: "from/to must use YYYY-MM-DD" }, 400, "no-store");
        }
        conditions.push(`m.release_date BETWEEN ${bind(from)} AND ${bind(to)}`);
      }

      if (search) {
        const pattern = `%${search}%`;
        const titleParam = bind(pattern);
        const nativeParam = bind(pattern);
        conditions.push(`(m.title LIKE ${titleParam} COLLATE NOCASE OR m.native_title LIKE ${nativeParam} COLLATE NOCASE)`);
      }
      if (language) conditions.push(`m.language_name = ${bind(language)}`);
      if (country) conditions.push(`m.country_code = ${bind(country)}`);
      if (officialOnly) conditions.push("m.verification_status = 'verified'");

      const where = conditions.join(" AND ");
      const direction = scope === "all" && !requestedYear ? "DESC" : "ASC";
      const listStatement = env.DB.prepare(
        `SELECT ${movieColumns}
         FROM movies m
         ${movieSourceJoin}
         WHERE ${where}
         ORDER BY m.release_date ${direction}, m.title COLLATE NOCASE ASC
         LIMIT ?${bindings.length + 1} OFFSET ?${bindings.length + 2}`,
      ).bind(...bindings, limit, offset);
      const countStatement = env.DB.prepare(
        `SELECT COUNT(*) AS count FROM movies m WHERE ${where}`,
      ).bind(...bindings);

      const next7 = addDays(today, 6);
      const next30 = addDays(today, 29);
      const [result, filteredCount, statsResult, sourcesResult, yearsResult, languagesResult, countriesResult, periodCountsResult] = await Promise.all([
        listStatement.all<MovieRow>(),
        countStatement.first<{ count: number }>(),
        env.DB.prepare(
          `SELECT
             COUNT(*) AS total,
             COALESCE(SUM(CASE WHEN verification_status='verified' THEN 1 ELSE 0 END), 0) AS verified,
             COALESCE(SUM(CASE WHEN verification_status='supported' THEN 1 ELSE 0 END), 0) AS supported,
             COALESCE(SUM(CASE WHEN verification_status='unconfirmed' THEN 1 ELSE 0 END), 0) AS unconfirmed,
             MAX(updated_at) AS latest_updated_at
           FROM movies m
           WHERE ${visibleMovieClause}`,
        ).first<StatsRow>(),
        env.DB.prepare(
          "SELECT COUNT(*) AS count, MAX(updated_at) AS latest_updated_at FROM source_channels WHERE active=1",
        ).first<SourcesRow>(),
        env.DB.prepare(
          `SELECT substr(m.release_date, 1, 4) AS value, COUNT(*) AS count
           FROM movies m WHERE ${visibleMovieClause}
           GROUP BY value ORDER BY value DESC LIMIT 120`,
        ).all<FacetRow>(),
        env.DB.prepare(
          `SELECT m.language_name AS value, COUNT(*) AS count
           FROM movies m WHERE ${visibleMovieClause}
           GROUP BY m.language_name ORDER BY count DESC, value COLLATE NOCASE ASC LIMIT 100`,
        ).all<FacetRow>(),
        env.DB.prepare(
          `SELECT m.country_code AS value, COUNT(*) AS count
           FROM movies m WHERE ${visibleMovieClause}
           GROUP BY m.country_code ORDER BY count DESC, value ASC LIMIT 100`,
        ).all<FacetRow>(),
        env.DB.prepare(
          `SELECT
             COALESCE(SUM(CASE WHEN m.release_date >= ?1 THEN 1 ELSE 0 END), 0) AS upcoming,
             COALESCE(SUM(CASE WHEN m.release_date BETWEEN ?1 AND ?2 THEN 1 ELSE 0 END), 0) AS next_7_days,
             COALESCE(SUM(CASE WHEN m.release_date BETWEEN ?1 AND ?3 THEN 1 ELSE 0 END), 0) AS next_30_days
           FROM movies m WHERE ${visibleMovieClause}`,
        ).bind(today, next7, next30).first<PeriodCountsRow>(),
      ]);

      const movies = result.results.map((movie) => ({
        id: movie.id,
        wikidataQid: movie.wikidata_qid ?? undefined,
        title: movie.title,
        nativeTitle: movie.native_title ?? undefined,
        language: movie.language_name,
        countryCode: movie.country_code,
        releaseDate: movie.release_date,
        verificationStatus: movie.verification_status,
        releaseSource: movie.release_date_source,
        releaseSourceName: movie.release_source_name ?? undefined,
      }));

      const latestUpdate = [statsResult?.latest_updated_at, sourcesResult?.latest_updated_at]
        .filter((value): value is string => Boolean(value))
        .sort()
        .at(-1);
      const filteredTotal = Number(filteredCount?.count ?? movies.length);

      return json({
        movies,
        source: "d1",
        generatedAt: new Date().toISOString(),
        catalogueUpdatedAt: d1TimestampToIso(latestUpdate),
        pagination: {
          limit,
          offset,
          total: filteredTotal,
          hasMore: offset + movies.length < filteredTotal,
        },
        facets: {
          years: facet(yearsResult.results),
          languages: facet(languagesResult.results),
          countries: facet(countriesResult.results),
        },
        periodCounts: {
          upcoming: Number(periodCountsResult?.upcoming ?? 0),
          next7Days: Number(periodCountsResult?.next_7_days ?? 0),
          next30Days: Number(periodCountsResult?.next_30_days ?? 0),
        },
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
