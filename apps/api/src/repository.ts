import { drizzle } from 'drizzle-orm/neon-http';
import { and, asc, desc, eq, exists, gt, ilike, or, sql } from 'drizzle-orm';
import type { SQL } from 'drizzle-orm';
import {
  titles, titleLanguages, titleGenres, genres, languages, titleLocalizations,
  releaseEvents, streamingOffers, providers, sourceRecords
} from '@cinema/db/schema';
import { classifyOffer, languageRoot } from '@cinema/domain';
import type {
  CatalogueRepository, HistoricalOptions, HistoricalTitle, ListOptions,
  Page, TitleDetail, TitleSummary
} from './contracts.ts';

const connect = (url: string) => drizzle(url);
type Database = ReturnType<typeof connect>;

export class NeonCatalogueRepository implements CatalogueRepository {
  private readonly db: Database;

  constructor(url: string) {
    if (!/^postgres(ql)?:\/\//.test(url)) throw new Error('Database is not configured');
    this.db = connect(url);
  }

  async list(options: ListOptions): Promise<Page<TitleSummary>> {
    const predicates: SQL[] = [eq(titles.publicationStatus,'published')];
    if (options.type) predicates.push(eq(titles.titleType,options.type));
    if (options.cursor) predicates.push(gt(titles.id,options.cursor));
    if (options.language) {
      predicates.push(exists(
        this.db.select({id:titleLanguages.titleId}).from(titleLanguages)
          .where(and(
            eq(titleLanguages.titleId,titles.id),
            eq(titleLanguages.relation,'original'),
            eq(titleLanguages.languageCode,languageRoot(options.language))
          ))
      ));
    }
    if (options.genre) {
      predicates.push(exists(
        this.db.select({id:titleGenres.titleId}).from(titleGenres)
          .where(and(eq(titleGenres.titleId,titles.id),eq(titleGenres.genreCode,options.genre)))
      ));
    }
    const rows=await this.db.select({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear
    }).from(titles).where(and(...predicates))
      .orderBy(asc(titles.id)).limit(options.limit+1);
    const items=rows.slice(0,options.limit);
    return {
      items,
      nextCursor: rows.length>options.limit && items.length>0 ? items[items.length-1]!.id : null
    };
  }

  async detail(id: string): Promise<TitleDetail | null> {
    const [title]=await this.db.select({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear
    }).from(titles).where(and(eq(titles.id,id),eq(titles.publicationStatus,'published'))).limit(1);
    if (!title) return null;

    const [langRows,genreRows,aliases,releases,offers]=await Promise.all([
      this.db.select({code:titleLanguages.languageCode}).from(titleLanguages)
        .where(and(eq(titleLanguages.titleId,id),eq(titleLanguages.relation,'original'))),
      this.db.select({code:titleGenres.genreCode}).from(titleGenres)
        .where(eq(titleGenres.titleId,id)),
      this.db.select({
        title:titleLocalizations.displayTitle,language:titleLocalizations.languageCode,
        kind:titleLocalizations.titleKind
      }).from(titleLocalizations).where(eq(titleLocalizations.titleId,id)),
      this.db.select({
        date:releaseEvents.releaseDate,kind:releaseEvents.eventType,
        territory:releaseEvents.territoryCode,provider:releaseEvents.providerCode,
        verified:releaseEvents.verified,sourceUrl:sourceRecords.sourceUrl
      }).from(releaseEvents)
        .innerJoin(sourceRecords,eq(releaseEvents.sourceRecordId,sourceRecords.id))
        .where(eq(releaseEvents.titleId,id)).orderBy(asc(releaseEvents.releaseDate)),
      this.db.select({
        provider:providers.displayName,providerCode:streamingOffers.providerCode,
        territory:streamingOffers.territoryCode,
        audioLanguage:streamingOffers.audioLanguageCode,
        verified:streamingOffers.verificationStatus,
        checked:streamingOffers.verifiedAt,expires:streamingOffers.validUntil
      }).from(streamingOffers)
        .innerJoin(providers,eq(streamingOffers.providerCode,providers.code))
        .where(eq(streamingOffers.titleId,id))
    ]);
    return {
      ...title,
      originalLanguages:langRows.map(x=>x.code),
      genres:genreRows.map(x=>x.code),
      alternateTitles:aliases.map(x=>({
        title:x.title,language:x.language,kind:x.kind
      })),
      releases:releases.map(x=>({
        date:x.date,kind:x.kind,territory:x.territory,
        provider:x.provider,verified:x.verified,sourceUrl:x.sourceUrl
      })),
      providers:offers.map(x=>({
        provider:x.provider,territory:x.territory,
        audioLanguage:x.audioLanguage,
        availability:classifyOffer({
          providerCode:x.providerCode,territory:x.territory,
          verification:x.verified==='verified'?'verified':'unverified',
          lastVerifiedAt:x.checked?.toISOString() ?? null,
          expiresAt:x.expires?.toISOString() ?? null
        },new Date()),
        lastChecked:x.checked?.toISOString() ?? null
      }))
    };
  }

  async search(term: string, limit: number): Promise<TitleSummary[]> {
    // LIKE wildcards are escaped; SQL values are parameterized by Drizzle.
    const pattern='%'+term.replace(/[\\%_]/g,(c)=>'\\'+c)+'%';
    return this.db.select({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear
    }).from(titles)
      .where(and(
        eq(titles.publicationStatus,'published'),
        or(
          ilike(titles.originalTitle,pattern),
          exists(this.db.select({id:titleLocalizations.titleId})
            .from(titleLocalizations)
            .where(and(
              eq(titleLocalizations.titleId,titles.id),
              ilike(titleLocalizations.displayTitle,pattern)
            )))
        )
      ))
      .orderBy(
        sql`CASE WHEN lower(${titles.originalTitle}) = lower(${term}) THEN 0 ELSE 1 END`,
        asc(titles.originalTitle),asc(titles.id)
      ).limit(limit);
  }

  async onThisDay({month,day,limit}: HistoricalOptions): Promise<HistoricalTitle[]> {
    return this.db.selectDistinct({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear,
      originalPremiereDate:releaseEvents.releaseDate
    }).from(releaseEvents)
      .innerJoin(titles,eq(releaseEvents.titleId,titles.id))
      .where(and(
        eq(titles.publicationStatus,'published'),
        eq(releaseEvents.eventType,'original_premiere'),
        eq(releaseEvents.verified,true),
        sql`EXTRACT(MONTH FROM ${releaseEvents.releaseDate})=${month}`,
        sql`EXTRACT(DAY FROM ${releaseEvents.releaseDate})=${day}`
      ))
      .orderBy(desc(releaseEvents.releaseDate),asc(titles.id))
      .limit(limit);
  }

  async languages(): Promise<{code:string;name:string}[]> {
    return this.db.select({code:languages.code,name:languages.name})
      .from(languages).orderBy(asc(languages.name)).limit(250);
  }
  async genres(): Promise<{code:string;name:string}[]> {
    return this.db.select({code:genres.code,name:genres.displayName})
      .from(genres).orderBy(asc(genres.displayName)).limit(100);
  }
  async recommend(): Promise<[]> {
    // Recommend endpoint is deliberately not exposed until scoped candidate queries are tested.
    return [];
  }
}
