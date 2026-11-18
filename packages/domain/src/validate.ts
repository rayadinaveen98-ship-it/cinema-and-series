import type { DomainIssue, ReleaseEvent, StagedTitle } from './types.ts';
import { isValidISODate } from './dates.ts';
import { isCountryCode, isLanguageTag } from './normalize.ts';

const RELEASE_KINDS = new Set(['original_premiere', 'territory_theatrical', 'ott_premiere', 'rerelease', 'series_debut']);
const VERIFICATIONS = new Set(['verified', 'unverified', 'rejected']);

export type ValidationResult = { ok: boolean; issues: DomainIssue[]; record?: StagedTitle };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Syntactic/staging validation. Production publication additionally requires evidence review. */
export function validateStagedTitle(input: unknown): ValidationResult {
  const issues: DomainIssue[] = [];
  if (!isRecord(input)) {
    return { ok: false, issues: [{ field: 'record', code: 'NOT_OBJECT' }] };
  }
  if (input.type !== 'movie' && input.type !== 'series') {
    issues.push({ field: 'type', code: 'INVALID_TYPE' });
  }
  if (typeof input.originalTitle !== 'string' ||
      input.originalTitle.trim().length === 0 || input.originalTitle.length > 300) {
    issues.push({ field: 'originalTitle', code: 'INVALID_TITLE' });
  }
  if (typeof input.sourceId !== 'string' ||
      !/^[a-z][a-z0-9_-]{1,31}:[A-Za-z0-9._-]{1,120}$/.test(input.sourceId)) {
    issues.push({ field: 'sourceId', code: 'INVALID_SOURCE_ID' });
  }
  if (typeof input.sourceUrl !== 'string') {
    issues.push({ field: 'sourceUrl', code: 'INVALID_SOURCE_URL' });
  } else {
    try {
      const url = new URL(input.sourceUrl);
      if (url.protocol !== 'https:' || !url.hostname.includes('.')) throw new Error('invalid');
    } catch {
      issues.push({ field: 'sourceUrl', code: 'INVALID_SOURCE_URL' });
    }
  }
  if (!Array.isArray(input.originalLanguages) ||
      input.originalLanguages.length === 0 ||
      input.originalLanguages.some((language: unknown) => !isLanguageTag(language))) {
    issues.push({ field: 'originalLanguages', code: 'INVALID_ORIGINAL_LANGUAGES' });
  }
  if (!Array.isArray(input.genres) ||
      input.genres.some((genre: unknown) => typeof genre !== 'string' ||
        !/^[a-z][a-z0-9-]{1,39}$/.test(genre))) {
    issues.push({ field: 'genres', code: 'INVALID_GENRES' });
  }
  if (!Array.isArray(input.releaseEvents)) {
    issues.push({ field: 'releaseEvents', code: 'INVALID_RELEASE_EVENTS' });
  } else {
    input.releaseEvents.forEach((item: unknown, index: number) => {
      const field = 'releaseEvents[' + index + ']';
      if (!isRecord(item) ||
          !isValidISODate(item.date) ||
          !RELEASE_KINDS.has(String(item.kind)) ||
          !VERIFICATIONS.has(String(item.verification)) ||
          typeof item.sourceRecordId !== 'string' ||
          item.sourceRecordId.trim().length === 0 ||
          (item.territory != null && !isCountryCode(item.territory))) {
        issues.push({ field, code: 'INVALID_RELEASE_EVENT' });
      }
    });
  }
  if (issues.length > 0) return { ok: false, issues };
  return { ok: true, issues: [], record: input as unknown as StagedTitle };
}

/** Guards a claim before it enters the public historical release surface. */
export function isVerifiedOriginalPremiere(event: ReleaseEvent): boolean {
  return event.kind === 'original_premiere' &&
    event.verification === 'verified' &&
    isValidISODate(event.date) &&
    event.sourceRecordId.trim().length > 0;
}
