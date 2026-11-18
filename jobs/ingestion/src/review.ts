import type { Sql,TransactionSql } from 'postgres';
import { inspectWikidataFields, compareStagedFields } from './field-evidence.ts';
import type { StagedTitle } from '@cinema/domain';

export type ReviewDecision='qualify'|'reject';
export interface ReviewCommand {
  stageId:string;
  reviewerCode:string;
  decision:ReviewDecision;
  note:string;
}
export interface ReviewResult {
  stageId:string;
  status:'validated'|'rejected';
  /** "validated" means checked for downstream editorial processing, NOT published. */
  published:false;
}

function validateReviewCommand(command:ReviewCommand):void {
  if (!command || typeof command.stageId!=='string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(command.stageId) ||
      typeof command.reviewerCode!=='string' ||
      !/^[a-z][a-z0-9_-]{2,63}$/.test(command.reviewerCode) ||
      !['qualify','reject'].includes(command.decision) ||
      typeof command.note!=='string' ||
      command.note.trim().length<12 ||
      command.note.length>1000) {
    throw new RangeError('INVALID_REVIEW_COMMAND');
  }
}

/**
 * Internal stage-only quality gate. Caller identity has NOT been authenticated;
 * DO NOT expose this to a public API before real operator authentication/RBAC.
 *
 * For a new candidate, qualification requires retrieved source evidence, matching
 * source ID, and an explicit review note. Existing identity collision and
 * rejected/ambiguous records cannot be qualified through this simple gate.
 * NO INSERT/UPDATE to titles, releases, current offers, or canonical IDs.
 */
export async function reviewInsideTransaction(
  tx:TransactionSql,
  command:ReviewCommand
):Promise<ReviewResult> {
  validateReviewCommand(command);
  const [item]=await tx`
    SELECT q.id::text AS review_id,q.status AS review_status,
           s.id::text AS stage_id,s.review_status AS stage_status,
           s.issue_codes AS issues,s.raw_candidate AS candidate,
           sr.external_record_id AS external_record_id,
           sr.retrieved_at AS retrieved_at,
           sr.raw_payload AS source_payload
    FROM staging_records s
    INNER JOIN review_queue q ON q.staging_record_id=s.id
    LEFT JOIN source_records sr ON s.source_record_id=sr.id
    WHERE s.id=${command.stageId}::uuid
    ORDER BY q.created_at,q.id
    LIMIT 1 FOR UPDATE OF s,q
  `;
  if(!item || item.review_status!=='open' || item.stage_status!=='pending') {
    throw new Error('REVIEW_NOT_OPEN');
  }
  const issueCodes=Array.isArray(item.issues)?item.issues:[];
  let fieldAssessment:ReturnType<typeof compareStagedFields>|null=null;
  if(command.decision==='qualify') {
    if(issueCodes.length!==1 || issueCodes[0]!=='NEW_SOURCE_NEEDS_VERIFICATION') {
      throw new Error('IDENTITY_REVIEW_REQUIRED');
    }
    const candidate=item.candidate;
    const evidence=item.source_payload;
    const expectedId=typeof candidate?.sourceId==='string'
      ? candidate.sourceId.split(':')[1]:null;
    if(!item.retrieved_at ||
       !evidence || typeof evidence!=='object' || Array.isArray(evidence) ||
       evidence.id!==expectedId ||
       item.external_record_id!==expectedId) {
      throw new Error('SOURCE_SNAPSHOT_REQUIRED');
    }
    const payload=evidence as Record<string,unknown>;
    const snapshot={
      sourceId:'wikidata:'+expectedId,
      canonicalSourceUrl:'https://www.wikidata.org/wiki/'+expectedId,
      retrievedAt:new Date(item.retrieved_at as string | Date).toISOString(),
      revisionId:typeof payload.lastrevid==='number' &&
        Number.isSafeInteger(payload.lastrevid) && payload.lastrevid>0
        ? payload.lastrevid:null,
      rawEntity:payload
    };
    const proof=inspectWikidataFields(snapshot);
    fieldAssessment=compareStagedFields(candidate as StagedTitle,proof);
  }

  const status=command.decision==='qualify'?'validated' as const:'rejected' as const;
  const ticket=command.decision==='qualify'?'resolved':'rejected';
  await tx`
    UPDATE staging_records
    SET review_status=${status}
    WHERE id=${command.stageId}::uuid
  `;
  await tx`
    UPDATE review_queue
    SET status=${ticket},reviewer_note=${command.note.trim()},resolved_at=now()
    WHERE id=${String(item.review_id)}::uuid
  `;
  // Do not place a free-text note into global audit (risk of sensitive data).
  const audit={
    stageId:command.stageId,
    action:command.decision,
    reviewerCode:command.reviewerCode,
    publication:false,
    ...(fieldAssessment ? {fieldAssessment:{
      labelObserved:fieldAssessment.labelObserved,
      publicationDateMatches:fieldAssessment.publicationDateMatches,
      sourceLanguageIdsUnmapped:fieldAssessment.sourceLanguageIdsUnmapped,
      sourceGenreIdsUnmapped:fieldAssessment.sourceGenreIdsUnmapped,
      issues:fieldAssessment.problems,
      originalPremiereVerified:false,
      streamingVerified:false
    }} : {})
  };
  await tx`
    INSERT INTO catalogue_audit_log(actor_type,action,changes)
    VALUES ('quality_reviewer','stage_quality_decision',${tx.json(audit)}::jsonb)
  `;
  return {stageId:command.stageId,status,published:false};
}

export async function applyStageReview(sql:Sql,command:ReviewCommand):Promise<ReviewResult> {
  validateReviewCommand(command);
  return sql.begin(tx=>reviewInsideTransaction(tx,command));
}
