import type { CatalogueTitle, ViewerPreferences } from './types.ts';
import { languageRoot } from './normalize.ts';

export interface Recommendation {
  titleId: string;
  score: number;
  reasons: Array<'language' | 'genre'>;
}

/** Deterministic, explainable guest-first ranking. No AI model or behavioral tracking. */
export function recommendTitles(
  catalogue: readonly CatalogueTitle[],
  preferences: ViewerPreferences,
  limit = 20
): Recommendation[] {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new RangeError('Invalid limit');
  const languages = new Set(preferences.languages.map(languageRoot).filter(Boolean));
  const genres = new Set(preferences.genres.map((genre) => genre.trim().toLowerCase()).filter(Boolean));
  const result: Recommendation[] = [];
  for (const title of catalogue) {
    if (title.status !== 'published') continue;
    const reasons: Recommendation['reasons'] = [];
    const languageHit = title.originalLanguages.some((lang) => languages.has(languageRoot(lang)));
    const genreMatches = title.genres.filter((g) => genres.has(g.toLowerCase())).length;
    if (languageHit) reasons.push('language');
    if (genreMatches > 0) reasons.push('genre');
    const score = (languageHit ? 5 : 0) + genreMatches * 3;
    if (score > 0) result.push({ titleId: title.id, score, reasons });
  }
  return result.sort((a, b) => b.score - a.score || a.titleId.localeCompare(b.titleId))
    .slice(0, limit);
}


/** Pure deterministic reference for related-title ranking. */
export function similarTitles(
  catalogue: readonly CatalogueTitle[],
  sourceId: string,
  limit = 20
): Recommendation[] {
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new RangeError('Invalid limit');
  const source = catalogue.find(x=>x.id===sourceId && x.status==='published');
  if (!source) return [];
  const languages = new Set(source.originalLanguages.map(languageRoot).filter(Boolean));
  const genres = new Set(source.genres.map(x=>x.toLowerCase()));
  const ranked: Recommendation[] = [];
  for (const title of catalogue) {
    if (title.status!=='published' || title.id===sourceId) continue;
    const sameLanguage=title.originalLanguages.some(x=>languages.has(languageRoot(x)));
    const genreHits=new Set(title.genres.map(x=>x.toLowerCase()).filter(x=>genres.has(x))).size;
    if (!sameLanguage && genreHits===0) continue;
    const reasons: Recommendation['reasons']=[
      ...(sameLanguage?['language' as const]:[]),...(genreHits?['genre' as const]:[])
    ];
    ranked.push({
      titleId:title.id,
      score:(sameLanguage?5:0)+3*genreHits+(source.type===title.type?2:0),
      reasons
    });
  }
  return ranked.sort((a,b)=>b.score-a.score || a.titleId.localeCompare(b.titleId)).slice(0,limit);
}
