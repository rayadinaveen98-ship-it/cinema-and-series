// Consumer-facing release metadata must never turn year-only source data into
// a fabricated exact premiere day.
export type ReleaseDateInfo = {
  releaseDate?: string;
  releaseYear?: number;
  datePrecision?: "day" | "year";
};

export function releaseDateLabel(movie: ReleaseDateInfo): string {
  const value = movie.releaseDate;
  const year = movie.releaseYear ?? (value && /^\d{4}/.test(value) ? Number(value.slice(0, 4)) : undefined);
  if (movie.datePrecision === "year" || !value) {
    return year ? `${year} · Exact date unconfirmed` : "Release date unconfirmed";
  }
  // No exact-day claim without a complete, valid date.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return year ? `${year} · Exact date unconfirmed` : "Release date unconfirmed";
  }
  const date = new Date(`${value}T00:00:00+05:30`);
  if (!Number.isFinite(date.valueOf()) || date.toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).replace(/\//g, "-") !== value) {
    // Use UTC components for strict ISO date validation across runtimes.
    const [y, m, d] = value.split("-").map(Number);
    const validated = new Date(Date.UTC(y, m - 1, d));
    if (validated.getUTCFullYear() !== y || validated.getUTCMonth() !== m - 1 || validated.getUTCDate() !== d) {
      return year ? `${year} · Exact date unconfirmed` : "Release date unconfirmed";
    }
  }
  return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Kolkata" }).format(date);
}

export function countryDisplayLabel(code?: string, names: Record<string, string> = {}): string {
  const normalized = code?.trim();
  return normalized ? names[normalized] ?? normalized : "Country unknown";
}
