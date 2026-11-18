import type { StreamingOffer } from './types.ts';

export type OfferFreshness = 'recently_verified' | 'stale' | 'expired' | 'unverified';

/** A verified claim must also be fresh and within its validity interval. */
export function classifyOffer(
  offer: StreamingOffer,
  now: Date,
  maximumAgeDays = 30
): OfferFreshness {
  if (offer.verification !== 'verified' || !offer.lastVerifiedAt ||
      !Number.isFinite(now.getTime()) || maximumAgeDays < 1) return 'unverified';
  const checked = new Date(offer.lastVerifiedAt);
  if (!Number.isFinite(checked.getTime()) || checked.getTime() > now.getTime()) return 'unverified';
  if (offer.expiresAt) {
    const expires = new Date(offer.expiresAt);
    if (!Number.isFinite(expires.getTime())) return 'unverified';
    if (expires.getTime() < now.getTime()) return 'expired';
  }
  return now.getTime() - checked.getTime() > maximumAgeDays * 86400000
    ? 'stale' : 'recently_verified';
}
