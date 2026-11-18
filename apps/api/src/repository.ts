import { drizzle } from 'drizzle-orm/neon-http';
import { and, asc, desc, eq, exists, gt, inArray, lt, ne, or, sql } from 'drizzle-orm';
import type { SQL } from 'drizzle-orm';
import {
  titles, titleLanguages, titleGenres, genres, languages, titleLocalizations,
  releaseEvents, seriesDebuts, streamingOffers, providers, sourceRecords
} from '@cinema/db/schema';
import { classifyOffer, languageRoot } from '@cinema/domain';
import type { ViewerPreferences } from '@cinema/domain';
import type {
  CatalogueRepository, HistoricalOptions, HistoricalTitle, ListOptions,
  Page, RankedTitle, TitleDetail, TitleSummary
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

    const [langRows,genreRows,aliases,releases,seriesLaunches,offers]=await Promise.all([
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
        date:seriesDebuts.debutDate,
        territory:seriesDebuts.territoryCode,provider:seriesDebuts.providerCode,
        verified:seriesDebuts.verified,sourceUrl:sourceRecords.sourceUrl
      }).from(seriesDebuts)
        .innerJoin(sourceRecords,eq(seriesDebuts.sourceRecordId,sourceRecords.id))
        .where(eq(seriesDebuts.titleId,id)).orderBy(asc(seriesDebuts.debutDate)),
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
      releases:[
        ...releases.map(x=>({
          date:x.date,kind:x.kind,territory:x.territory,
          provider:x.provider,verified:x.verified,sourceUrl:x.sourceUrl
        })),
        ...seriesLaunches.map(x=>({
          date:x.date,kind:'series_debut' as const,territory:x.territory,
          provider:x.provider,verified:x.verified,sourceUrl:x.sourceUrl
        }))
      ].sort((a,b)=>a.date.localeCompare(b.date)),
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
    // Indexed candidate lookup instead of scanning all published titles with OR.
    // The pattern's literal %, _ and backslash are escaped before binding.
    const pattern='%'+term.replace(/[\\%_]/g,(char)=>'\\'+char)+'%';
    const matches=sql`(
      SELECT ${titles.id} FROM ${titles}
      WHERE lower(${titles.originalTitle}) LIKE lower(${pattern})
      UNION
      SELECT ${titleLocalizations.titleId} FROM ${titleLocalizations}
      WHERE lower(${titleLocalizations.displayTitle}) LIKE lower(${pattern})
    )`;
    return this.db.select({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear
    }).from(titles)
      .where(and(
        eq(titles.publicationStatus,'published'),
        sql`${titles.id} IN ${matches}`
      ))
      .orderBy(
        sql`CASE WHEN lower(${titles.originalTitle}) = lower(${term}) THEN 0 ELSE 1 END`,
        asc(titles.originalTitle),asc(titles.id)
      ).limit(limit);
  }

  async onThisDay({month,day,limit,beforeYear}: HistoricalOptions): Promise<HistoricalTitle[]> {
    return this.db.selectDistinct({
      id:titles.id,originalTitle:titles.originalTitle,
      type:titles.titleType,year:titles.firstReleaseYear,
      originalPremiereDate:releaseEvents.releaseDate
    }).from(releaseEvents)
      .innerJoin(titles,eq(releaseEvents.titleId,titles.id))
      .where(and(
        eq(titles.publicationStatus,'published'),
        eq(titles.titleType,'movie'),
        eq(releaseEvents.eventType,'original_premiere'),
        eq(releaseEvents.verified,true),
        lt(releaseEvents.releaseDate,String(beforeYear)+'-01-01'),
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

  /**
   * Database-side rank (not a 300-title recent candidate cutoff).
   * Matches are constrained by indexed original-language and genre relations.
   * Query cost must be benchmarked before large catalogue import.
   */
  private async rankedMatches(
    languagesInput: readonly string[],
    genresInput: readonly string[],
    limit: number,
    excludeId?: string,
    preferType?: 'movie' | 'series'
  ): Promise<RankedTitle[]> {
    const languageCodes = [...new Set(languagesInput.map(languageRoot).filter(Boolean))];
    const genreCodes = [...new Set(genresInput.map(x => x.toLowerCase()).filter(Boolean))];
    if (languageCodes.length === 0 && genreCodes.length === 0) return [];

    // Pre-aggregate matches once; do not perform a correlated genre count
    // per candidate. This preserves the original language/genre scoring.
    const languageMatches=this.db.select({
      titleId:titleLanguages.titleId
    }).from(titleLanguages)
      .where(and(
        eq(titleLanguages.relation,'original'),
        inArray(titleLanguages.languageCode,languageCodes)
      ))
      .groupBy(titleLanguages.titleId)
      .as('matching_languages');

    const genreMatches=this.db.select({
      titleId:titleGenres.titleId,
      hits:sql<number>`count(*)::integer`.as('hits')
    }).from(titleGenres)
      .where(inArray(titleGenres.genreCode,genreCodes))
      .groupBy(titleGenres.titleId)
      .as('matching_genres');

    const hasLanguage=sql<boolean>`${languageMatches.titleId} IS NOT NULL`;
    const genreHits=sql<number>`COALESCE(${genreMatches.hits},0)`;
    const hasGenre=sql<boolean>`${genreMatches.titleId} IS NOT NULL`;
    const score=sql<number>`(
      (CASE WHEN ${hasLanguage} THEN 5 ELSE 0 END)
      + (${genreHits} * 3)
      + ${preferType
        ? sql`(CASE WHEN ${titles.titleType} = ${preferType} THEN 2 ELSE 0 END)`
        : sql`0`}
    )`;

    const filters=[eq(titles.publicationStatus,'published'),or(hasLanguage,hasGenre)];
    if(excludeId)filters.push(ne(titles.id,excludeId));

    const rows=await this.db.select({
      id:titles.id,originalTitle:titles.originalTitle,type:titles.titleType,
      year:titles.firstReleaseYear,languageHit:hasLanguage,genreHits,score
    }).from(titles)
      .leftJoin(languageMatches,eq(languageMatches.titleId,titles.id))
      .leftJoin(genreMatches,eq(genreMatches.titleId,titles.id))
      .where(and(...filters))
      .orderBy(desc(score),asc(titles.id))
      .limit(limit);

    return rows.map(x=>({
      id:x.id,originalTitle:x.originalTitle,type:x.type,year:x.year,
      score:Number(x.score),
      reasons:[
        ...(x.languageHit ? ['language' as const] : []),
        ...(Number(x.genreHits)>0 ? ['genre' as const] : []),
        ...(preferType && x.type===preferType ? ['sameType' as const] : [])
      ]
    }));
  }

  async recommend(preferences: ViewerPreferences, limit: number): Promise<RankedTitle[]> {
    return this.rankedMatches(preferences.languages,preferences.genres,limit);
  }

  async similar(titleId: string, limit: number): Promise<RankedTitle[] | null> {
    const [source] = await this.db.select({id:titles.id,type:titles.titleType})
      .from(titles).where(and(eq(titles.id,titleId),eq(titles.publicationStatus,'published')))
      .limit(1);
    if (!source) return null;

    const [original,genreRows] = await Promise.all([
      this.db.select({code:titleLanguages.languageCode}).from(titleLanguages)
        .where(and(eq(titleLanguages.titleId,titleId),eq(titleLanguages.relation,'original'))),
      this.db.select({code:titleGenres.genreCode}).from(titleGenres)
        .where(eq(titleGenres.titleId,titleId))
    ]);
    return this.rankedMatches(original.map(x=>x.code),genreRows.map(x=>x.code),limit,titleId,source.type);
  }
}
