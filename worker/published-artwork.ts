import { projectArtwork, type ArtworkCandidate } from "./artwork";

export type TitleArtworkIdentity = {
  id: string; language_name: string; country_code: string;
};
type LinkAssetRow = {
  source_id: string; presentation_role: string; asset_id: string; asset_type: string;
  source_key: string; source_asset_id: string | null; source_page_url: string | null;
  delivery_url: string | null; language_code: string; territory_code: string;
  publication_state: string; rights_basis: string; hosting_mode: string;
  attribution_required: number; attribution_text: string | null;
  rights_verified_at: string | null; valid_from: string | null;
  valid_until: string | null; takedown_status: string;
  width: number | null; height: number | null; aspect_ratio: number | null;
  quality_score: number | null;
};
export type PublishedArtwork = {
  posterUrl?: string; backdropUrl?: string; artworkSource?: string;
  artworkSourceUrl?: string; artworkAttribution?: string;
};

/** One bounded, page-local lookup; no full-catalogue artwork joins. */
export async function publishedArtworkForPage(
  db: D1Database,
  sourceTable: "movies" | "catalogue_titles" | "series_titles",
  titles: TitleArtworkIdentity[],
  territory = "IN",
  nowIso = new Date().toISOString(),
): Promise<Map<string, PublishedArtwork>> {
  const output = new Map<string, PublishedArtwork>();
  const ids = [...new Set(titles.map((item) => item.id).filter(Boolean))].slice(0, 200);
  if (!ids.length) return output;
  const placeholders = ids.map((_, i) => "?" + (i + 2)).join(",");
  const query = "SELECT l.source_id, l.presentation_role, a.id AS asset_id, a.asset_type, " +
    "a.source_key, a.source_asset_id, a.source_page_url, a.delivery_url, " +
    "a.language_code, a.territory_code, a.publication_state, a.rights_basis, " +
    "a.hosting_mode, a.attribution_required, a.attribution_text, a.rights_verified_at, " +
    "a.valid_from, a.valid_until, a.takedown_status, a.width, a.height, a.aspect_ratio, a.quality_score " +
    "FROM title_artwork_links l JOIN artwork_assets a ON a.id=l.asset_id " +
    "WHERE l.source_table=?1 AND l.source_id IN (" + placeholders + ") " +
    "AND l.media_type=?" + (ids.length + 2) + " AND a.takedown_status='clear' " +
    "AND a.publication_state IN ('OPEN_LICENSE_VERIFIED','PUBLIC_DOMAIN_VERIFIED'," +
    "'PROVIDER_LICENSED','RIGHTS_APPROVED','PROMOTIONAL_PERMISSION_VERIFIED') LIMIT 800";
  const rows = await db.prepare(query)
    .bind(sourceTable, ...ids, sourceTable === "series_titles" ? "series" : "movie")
    .all<LinkAssetRow>();

  const byId = new Map<string, ArtworkCandidate[]>();
  const sourceByAssetId = new Map<string, LinkAssetRow>();
  for (const row of rows.results ?? []) {
    if (row.presentation_role !== "poster" && row.presentation_role !== "backdrop") continue;
    const candidate: ArtworkCandidate = {
      assetId: row.asset_id, assetType: row.asset_type,
      role: row.presentation_role, sourceKey: row.source_key,
      sourceAssetId: row.source_asset_id, sourcePageUrl: row.source_page_url,
      deliveryUrl: row.delivery_url, languageCode: row.language_code,
      territoryCode: row.territory_code, publicationState: row.publication_state as ArtworkCandidate["publicationState"],
      rightsBasis: row.rights_basis as ArtworkCandidate["rightsBasis"],
      hostingMode: row.hosting_mode as ArtworkCandidate["hostingMode"],
      attributionRequired: row.attribution_required === 1,
      attributionText: row.attribution_text, rightsVerifiedAt: row.rights_verified_at,
      validFrom: row.valid_from, validUntil: row.valid_until,
      takedownStatus: row.takedown_status as ArtworkCandidate["takedownStatus"],
      width: row.width, height: row.height, aspectRatio: row.aspect_ratio,
      qualityScore: row.quality_score,
    };
    const list = byId.get(row.source_id) ?? [];
    list.push(candidate);
    byId.set(row.source_id, list);
    sourceByAssetId.set(row.asset_id, row);
  }
  for (const title of titles) {
    const projection = projectArtwork(byId.get(title.id) ?? [],
      languageCode(title.language_name), territory, nowIso);
    if (!projection.hasPublishablePoster && !projection.hasPublishableBackdrop) continue;
    const winnerId = projection.poster.assetId ?? projection.backdrop.assetId;
    const winner = winnerId ? sourceByAssetId.get(winnerId) : undefined;
    output.set(title.id, {
      posterUrl: projection.poster.url ?? undefined,
      backdropUrl: projection.backdrop.url ?? undefined,
      artworkSource: winner?.source_key, artworkSourceUrl: winner?.source_page_url ?? undefined,
      artworkAttribution: projection.poster.attribution ?? projection.backdrop.attribution ?? undefined,
    });
  }
  return output;
}
export function languageCode(name: string) {
  const value = name.trim().toLowerCase();
  const codes: Record<string, string> = {
    telugu:"te", tamil:"ta", malayalam:"ml", hindi:"hi", kannada:"kn",
    bengali:"bn", marathi:"mr", english:"en", punjabi:"pa", odia:"or",
  };
  return codes[value] ?? "";
}
