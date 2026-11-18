import type { CatalogueTitle } from './types.ts';
import { isValidMonthDay } from './dates.ts';
import { isVerifiedOriginalPremiere } from './validate.ts';

export interface OnThisDayItem {
  titleId: string;
  originalTitle: string;
  originalLanguageCodes: string[];
  originalPremiereDate: string;
}

export function findOnThisDay(
  catalogue: readonly CatalogueTitle[],
  month: number,
  day: number,
  limit = 50,
  beforeYear = new Date().getUTCFullYear()
): OnThisDayItem[] {
  if (!isValidMonthDay(month, day)) throw new RangeError('Invalid month/day');
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new RangeError('Invalid limit');
  if (!Number.isInteger(beforeYear) || beforeYear < 1801 || beforeYear > 2101) throw new RangeError('Invalid historical cutoff year');
  const dayCode = '-' + String(month).padStart(2, '0') + '-' + String(day).padStart(2, '0');
  const results: OnThisDayItem[] = [];
  for (const title of catalogue) {
    if (title.status !== 'published') continue;
    const premieres = title.releaseEvents
      .filter((event) => isVerifiedOriginalPremiere(event) && event.date.endsWith(dayCode) && Number(event.date.slice(0,4)) < beforeYear)
      .sort((a, b) => a.date.localeCompare(b.date));
    if (premieres[0]) {
      results.push({
        titleId: title.id,
        originalTitle: title.originalTitle,
        originalLanguageCodes: title.originalLanguages,
        originalPremiereDate: premieres[0].date
      });
    }
  }
  return results.sort((a, b) =>
    b.originalPremiereDate.localeCompare(a.originalPremiereDate) ||
    a.titleId.localeCompare(b.titleId)
  ).slice(0, limit);
}
