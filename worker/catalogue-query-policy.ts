/**
 * Metadata (catalogue-wide facets, global totals, source tallies and period
 * counts) is expensive in Cloudflare D1. Only explicitly opt out when the
 * caller already has the first-page metadata or is showing a compact rail.
 *
 * A missing parameter means the backwards-compatible FULL response.
 * Page rows and filtered counts must remain available on every request.
 */
export function catalogueMetadataNeeded(params: URLSearchParams): boolean {
  return params.get("meta") !== "0";
}

export function cataloguePageNeedsMetadata(page: number, includeMetadata: boolean): boolean {
  return includeMetadata && page === 0;
}
