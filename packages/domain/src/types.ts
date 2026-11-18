export type TitleType = 'movie' | 'series';
export type RecordStatus = 'staged' | 'published';
export type ReleaseKind = 'original_premiere' | 'territory_theatrical' | 'ott_premiere' | 'rerelease';
export type SourceVerification = 'verified' | 'unverified' | 'rejected';

export interface ReleaseEvent {
  date: string;
  kind: ReleaseKind;
  territory?: string | null;
  verification: SourceVerification;
  sourceRecordId: string;
}

export interface CatalogueTitle {
  id: string;
  type: TitleType;
  originalTitle: string;
  originalLanguages: string[];
  genres: string[];
  status: RecordStatus;
  externalIds: string[];
  alternativeTitles?: string[];
  releaseEvents: ReleaseEvent[];
}

export interface StagedTitle {
  type: TitleType;
  sourceId: string;
  sourceUrl: string;
  originalTitle: string;
  originalLanguages: string[];
  genres: string[];
  releaseEvents: ReleaseEvent[];
}

export interface ViewerPreferences {
  languages: string[];
  genres: string[];
}

export interface StreamingOffer {
  providerCode: string;
  territory: string;
  verification: SourceVerification;
  lastVerifiedAt: string | null;
  expiresAt?: string | null;
}

export interface DomainIssue {
  field: string;
  code: string;
}
