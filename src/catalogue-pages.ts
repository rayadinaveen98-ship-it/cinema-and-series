/**
 * Shared V1 catalogue request and page primitives.
 * All page fetches remain bounded; callers own the query-key and AbortController.
 */
export function cataloguePageSearch(query: Record<string, string>, limit: number, page: number, includeMetadata = true): string {
  if (!Number.isInteger(limit) || limit < 1 || limit > 200) throw new RangeError("Invalid catalogue page size");
  if (!Number.isInteger(page) || page < 0) throw new RangeError("Invalid catalogue page");
  // Constrain caller input so pagination cannot silently be overridden.
  const params = new URLSearchParams({ ...query, artwork: "1", limit: String(limit), offset: String(page * limit) });
  // Only the first full browse page needs catalogue-wide facets and totals.
  // Home rails and subsequent pages request rows + filtered count only.
  if (page > 0 || !includeMetadata) params.set("meta", "0");
  else params.delete("meta");
  return params.toString();
}

export function appendUniquePage<T extends { id: string }>(previous: T[], next: T[], page: number): T[] {
  const existing = page === 0 ? [] : previous;
  const ids = new Set<string>();
  return [...existing, ...next].filter((item) => {
    if (ids.has(item.id)) return false;
    ids.add(item.id);
    return true;
  });
}

export async function readCataloguePage<T>(result: Response): Promise<T> {
  if (!result.ok) {
    if (result.status === 503) {
      const details = await result.json().catch(() => null) as { error?: string } | null;
      if (details?.error === "catalogue_daily_read_limit") {
        throw new Error("The catalogue has reached its daily database limit. Please try again after 5:30 AM IST.");
      }
    }
    throw new Error("Catalogue could not load. Check your connection and try again.");
  }
  const data = await result.json() as T;
  if (result.headers.get("X-Catalogue-Cache") === "stale-on-quota" && data && typeof data === "object") {
    return { ...data, staleDuringQuota: true } as T;
  }
  return data;
}
