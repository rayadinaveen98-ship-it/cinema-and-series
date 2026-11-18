import type { CatalogueTitle, StagedTitle } from './types.ts';
import { normalizeSearchKey } from './normalize.ts';

export type IdentityDecision =
  | { decision: 'matched'; titleId: string }
  | { decision: 'review'; candidateIds: string[] }
  | { decision: 'new'; candidateIds: [] };

/** Never silently merge candidates merely because their names or years match. */
export function resolveTitleIdentity(
  candidate: StagedTitle,
  catalogue: readonly CatalogueTitle[]
): IdentityDecision {
  const byId = catalogue.filter((title) => title.externalIds.includes(candidate.sourceId));
  if (byId.length === 1 && byId[0]) return { decision: 'matched', titleId: byId[0].id };
  if (byId.length > 1) return { decision: 'review', candidateIds: byId.map((t) => t.id) };

  const key = normalizeSearchKey(candidate.originalTitle);
  const possible = catalogue.filter((title) =>
    title.type === candidate.type &&
    (normalizeSearchKey(title.originalTitle) === key ||
     (title.alternativeTitles ?? []).some((alias) => normalizeSearchKey(alias) === key))
  );
  if (possible.length) return { decision: 'review', candidateIds: possible.map((t) => t.id) };
  return { decision: 'new', candidateIds: [] };
}
