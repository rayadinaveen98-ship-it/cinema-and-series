import type { ViewerPreferences } from '@cinema/domain';

export interface TitleSummary {
  id: string;
  originalTitle: string;
  type: 'movie' | 'series';
  year: number | null;
}

export interface ReleaseSummary {
  date: string;
  kind: string;
  territory: string | null;
  provider: string | null;
  verified: boolean;
  sourceUrl: string;
}

export interface ProviderOffer {
  provider: string;
  territory: string;
  audioLanguage: string | null;
  availability: 'recently_verified' | 'stale' | 'expired' | 'unverified';
  lastChecked: string | null;
}

export interface TitleDetail extends TitleSummary {
  originalLanguages: string[];
  genres: string[];
  alternateTitles: { title: string; language: string | null; kind: string }[];
  releases: ReleaseSummary[];
  providers: ProviderOffer[];
}

export interface Page<T> {
  items: T[];
  nextCursor: string | null;
}

export interface ListOptions {
  limit: number;
  cursor?: string;
  type?: 'movie' | 'series';
  language?: string;
  genre?: string;
}
export interface HistoricalOptions {
  month: number;
  day: number;
  limit: number;
}

export interface CatalogueRepository {
  list(options: ListOptions): Promise<Page<TitleSummary>>;
  detail(id: string): Promise<TitleDetail | null>;
  search(q: string, limit: number): Promise<TitleSummary[]>;
  onThisDay(options: HistoricalOptions): Promise<ReleaseSummary[] & never[]> | Promise<HistoricalTitle[]>;
  languages(): Promise<{ code: string; name: string }[]>;
  genres(): Promise<{ code: string; name: string }[]>;
  recommend(preferences: ViewerPreferences, limit: number): Promise<RecommendedTitle[]>;
}

export interface HistoricalTitle extends TitleSummary {
  originalPremiereDate: string;
}

export interface RecommendedTitle extends TitleSummary {
  score: number;
  reasons: Array<'language' | 'genre'>;
}
