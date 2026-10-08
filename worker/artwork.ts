export type ArtworkPresentationRole = "poster" | "backdrop";

export type ArtworkPublicationState =
  | "DISCOVERED" | "PENDING_REVIEW" | "OPEN_LICENSE_VERIFIED" | "PUBLIC_DOMAIN_VERIFIED"
  | "PROVIDER_LICENSED" | "RIGHTS_APPROVED" | "PROMOTIONAL_PERMISSION_VERIFIED"
  | "REJECTED" | "EXPIRED" | "TAKEDOWN_PENDING" | "TAKEN_DOWN";

export type ArtworkRightsBasis =
  | "OPEN_LICENSE" | "PUBLIC_DOMAIN" | "PROVIDER_CONTRACT" | "RIGHTSHOLDER_PERMISSION"
  | "PROMOTIONAL_PERMISSION" | "PLATFORM_EMBED_AUTHORIZATION" | "NO_RIGHTS_BASIS";

export type ArtworkHostingMode = "SELF_HOSTED" | "PROVIDER_CDN" | "EXTERNAL_ALLOWED" | "REFERENCE_ONLY" | "EMBED_ONLY";

export type ArtworkCandidate = {
  assetId: string;
  assetType: string;
  role: ArtworkPresentationRole;
  sourceKey: string;
  sourceAssetId: string | null;
  sourcePageUrl: string | null;
  deliveryUrl: string | null;
  languageCode: string;
  territoryCode: string;
  publicationState: ArtworkPublicationState;
  rightsBasis: ArtworkRightsBasis;
  hostingMode: ArtworkHostingMode;
  attributionRequired: boolean;
  attributionText: string | null;
  rightsVerifiedAt: string | null;
  validFrom: string | null;
  validUntil: string | null;
  takedownStatus: "clear" | "pending" | "taken_down";
  width: number | null;
  height: number | null;
  aspectRatio: number | null;
  qualityScore: number | null;
};

export type ArtworkSelection = { url: string | null; assetId: string | null; attribution: string | null; isFallback: boolean };
export type ArtworkProjection = {
  poster: ArtworkSelection;
  backdrop: ArtworkSelection;
  hasPublishablePoster: boolean;
  hasPublishableBackdrop: boolean;
  isFallback: boolean;
};

const PUBLIC_PAIRINGS: Record<ArtworkPublicationState, ArtworkRightsBasis | null> = {
  DISCOVERED: null, PENDING_REVIEW: null, OPEN_LICENSE_VERIFIED: "OPEN_LICENSE",
  PUBLIC_DOMAIN_VERIFIED: "PUBLIC_DOMAIN", PROVIDER_LICENSED: "PROVIDER_CONTRACT",
  RIGHTS_APPROVED: "RIGHTSHOLDER_PERMISSION", PROMOTIONAL_PERMISSION_VERIFIED: "PROMOTIONAL_PERMISSION",
  REJECTED: null, EXPIRED: null, TAKEDOWN_PENDING: null, TAKEN_DOWN: null,
};
const PUBLIC_HOSTING = new Set<ArtworkHostingMode>(["SELF_HOSTED", "PROVIDER_CDN", "EXTERNAL_ALLOWED"]);

function httpsUrl(value: string | null) {
  if (!value) return false;
  try { const parsed = new URL(value); return parsed.protocol === "https:" && Boolean(parsed.host); }
  catch { return false; }
}
function atOrBefore(value: string, instant: string) {
  const left = Date.parse(value), right = Date.parse(instant);
  return Number.isFinite(left) && Number.isFinite(right) && left <= right;
}
function after(value: string, instant: string) {
  const left = Date.parse(value), right = Date.parse(instant);
  return Number.isFinite(left) && Number.isFinite(right) && left > right;
}

export function isArtworkEligible(candidate: ArtworkCandidate, nowIso: string, territory: string) {
  if (PUBLIC_PAIRINGS[candidate.publicationState] !== candidate.rightsBasis) return false;
  if (!PUBLIC_HOSTING.has(candidate.hostingMode)) return false;
  if (candidate.takedownStatus !== "clear") return false;
  if (!candidate.rightsVerifiedAt || !atOrBefore(candidate.rightsVerifiedAt, nowIso)) return false;
  if (candidate.validFrom && !Number.isFinite(Date.parse(candidate.validFrom))) return false;
  if (candidate.validUntil && !Number.isFinite(Date.parse(candidate.validUntil))) return false;
  if (candidate.validFrom && after(candidate.validFrom, nowIso)) return false;
  if (candidate.validUntil && !after(candidate.validUntil, nowIso)) return false;
  if (candidate.territoryCode && candidate.territoryCode !== territory) return false;
  if (!httpsUrl(candidate.deliveryUrl)) return false;
  if (candidate.attributionRequired && !candidate.attributionText?.trim()) return false;
  if (candidate.assetType !== candidate.role) return false;
  return true;
}

function localeRank(candidate: ArtworkCandidate, language: string, territory: string) {
  if (candidate.languageCode === language && candidate.territoryCode === territory) return 0;
  if (candidate.languageCode === language && !candidate.territoryCode) return 1;
  if (!candidate.languageCode && candidate.territoryCode === territory) return 2;
  if (!candidate.languageCode && !candidate.territoryCode) return 3;
  return 99;
}
function rightsRank(candidate: ArtworkCandidate) {
  switch (candidate.publicationState) {
    case "RIGHTS_APPROVED":
    case "PROVIDER_LICENSED": return 0;
    case "PROMOTIONAL_PERMISSION_VERIFIED": return 1;
    case "OPEN_LICENSE_VERIFIED": return 2;
    case "PUBLIC_DOMAIN_VERIFIED": return 3;
    default: return 99;
  }
}
function visualRank(candidate: ArtworkCandidate, requestedAspectRatio?: number) {
  const ratioPenalty = requestedAspectRatio && candidate.aspectRatio ? Math.abs(candidate.aspectRatio - requestedAspectRatio) : 0;
  const pixels = (candidate.width ?? 0) * (candidate.height ?? 0);
  return [ratioPenalty, -(candidate.qualityScore ?? 0), -pixels] as const;
}
function compareCandidates(a: ArtworkCandidate, b: ArtworkCandidate, language: string, territory: string, requestedAspectRatio?: number) {
  const aRank = [localeRank(a, language, territory), rightsRank(a), ...visualRank(a, requestedAspectRatio), a.assetId];
  const bRank = [localeRank(b, language, territory), rightsRank(b), ...visualRank(b, requestedAspectRatio), b.assetId];
  for (let i = 0; i < aRank.length; i += 1) {
    if (aRank[i] < bRank[i]) return -1;
    if (aRank[i] > bRank[i]) return 1;
  }
  return 0;
}
export function selectArtwork(candidates: ArtworkCandidate[], role: ArtworkPresentationRole, language: string, territory: string, nowIso: string, requestedAspectRatio?: number): ArtworkSelection {
  const eligible = candidates.filter((c) => c.role === role)
    .filter((c) => isArtworkEligible(c, nowIso, territory))
    .filter((c) => localeRank(c, language, territory) < 4)
    .sort((a, b) => compareCandidates(a, b, language, territory, requestedAspectRatio));
  const winner = eligible[0];
  if (!winner) return { url: null, assetId: null, attribution: null, isFallback: true };
  return { url: winner.deliveryUrl, assetId: winner.assetId, attribution: winner.attributionRequired ? winner.attributionText : null, isFallback: false };
}
export function projectArtwork(candidates: ArtworkCandidate[], language: string, territory: string, nowIso: string): ArtworkProjection {
  const poster = selectArtwork(candidates, "poster", language, territory, nowIso, 2 / 3);
  const backdrop = selectArtwork(candidates, "backdrop", language, territory, nowIso, 16 / 9);
  return { poster, backdrop, hasPublishablePoster: !poster.isFallback, hasPublishableBackdrop: !backdrop.isFallback, isFallback: poster.isFallback && backdrop.isFallback };
}
