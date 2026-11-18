import { resolveTitleIdentity, validateStagedTitle } from '@cinema/domain';
import type { CatalogueTitle, StagedTitle } from '@cinema/domain';

export type StageDisposition = 'needs_new_review' | 'needs_existing_review' | 'quarantined';
export interface StageDecision {
  sourceId: string | null;
  disposition: StageDisposition;
  issues: string[];
  possibleTitleIds: string[];
}
export interface BatchEvaluation {
  total: number;
  reviewNew: number;
  reviewExisting: number;
  quarantined: number;
  decisions: StageDecision[];
}

/**
 * First-pass gate only. No network, writes, or publication.
 * Initial source allowlist: canonical Wikidata Q-identities (CC0).
 * Every structurally valid record still requires manual metadata review.
 */
export function evaluateBatch(
  raw: readonly unknown[],
  catalogue: readonly CatalogueTitle[]
): BatchEvaluation {
  if (raw.length > 40) throw new RangeError('Pilot batches are limited to 40 records');
  const seen = new Set<string>();
  const decisions: StageDecision[] = [];
  for (const record of raw) {
    const result = validateStagedTitle(record);
    if (!result.ok || !result.record) {
      const sourceId=typeof record==='object' && record!==null &&
        'sourceId' in record && typeof record.sourceId==='string'
        ? record.sourceId : null;
      decisions.push({
        sourceId,disposition:'quarantined',
        issues:result.issues.map(x=>x.code),possibleTitleIds:[]
      });
      continue;
    }

    const candidate: StagedTitle=result.record;
    const sourceId=candidate.sourceId;
    const sourceUrl=new URL(candidate.sourceUrl);
    if (!/^wikidata:Q[1-9][0-9]*$/.test(sourceId) ||
        sourceUrl.hostname!=='www.wikidata.org' ||
        sourceUrl.pathname!=='/wiki/'+sourceId.split(':')[1] ||
        sourceUrl.search!=='' || sourceUrl.hash!=='' || sourceUrl.port!=='') {
      decisions.push({
        sourceId,disposition:'quarantined',
        issues:['SOURCE_NOT_APPROVED_OR_MISMATCHED'],possibleTitleIds:[]
      });
      continue;
    }
    if (seen.has(sourceId)) {
      decisions.push({
        sourceId,disposition:'quarantined',
        issues:['DUPLICATE_IN_BATCH'],possibleTitleIds:[]
      });
      continue;
    }
    seen.add(sourceId);
    const match=resolveTitleIdentity(candidate,catalogue);
    if (match.decision==='matched') {
      const existing=catalogue.find(x=>x.id===match.titleId);
      if (!existing || existing.type!==candidate.type) {
        decisions.push({
          sourceId,disposition:'quarantined',
          issues:['CANONICAL_TITLE_TYPE_CONFLICT'],possibleTitleIds:[match.titleId]
        });
      } else {
        decisions.push({
          sourceId,disposition:'needs_existing_review',
          issues:['SOURCE_MATCH_REQUIRES_FIELD_REVIEW'],possibleTitleIds:[match.titleId]
        });
      }
    } else {
      decisions.push({
        sourceId,
        disposition:match.decision==='review'?'needs_existing_review':'needs_new_review',
        issues:match.decision==='review'?['AMBIGUOUS_TITLE_ALIAS']:['NEW_SOURCE_NEEDS_VERIFICATION'],
        possibleTitleIds:match.candidateIds
      });
    }
  }
  return {
    total:decisions.length,
    reviewNew:decisions.filter(x=>x.disposition==='needs_new_review').length,
    reviewExisting:decisions.filter(x=>x.disposition==='needs_existing_review').length,
    quarantined:decisions.filter(x=>x.disposition==='quarantined').length,
    decisions
  };
}
