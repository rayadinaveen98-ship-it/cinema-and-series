/**
 * Read-model mapping of SQL migrations 0001–0005.
 * The SQL migrations remain authoritative until a schema-diff gate is added.
 * Do not use drizzle-kit push against the hosted pilot.
 */
import { pgTable, uuid, text, integer, boolean, date, char, timestamp } from 'drizzle-orm/pg-core';

export const titles = pgTable('titles', {
  id: uuid('id').primaryKey(),
  titleType: text('title_type').notNull().$type<'movie' | 'series'>(),
  originalTitle: text('original_title').notNull(),
  publicationStatus: text('publication_status').notNull(),
  firstReleaseYear: integer('first_release_year'),
});

export const languages = pgTable('languages', {
  code: text('code').primaryKey(),
  name: text('name').notNull(),
});

export const genres = pgTable('genres', {
  code: text('code').primaryKey(),
  displayName: text('display_name').notNull(),
});

export const titleLanguages = pgTable('title_languages', {
  titleId: uuid('title_id').notNull(),
  languageCode: text('language_code').notNull(),
  relation: text('relation').notNull(),
});

export const titleGenres = pgTable('title_genres', {
  titleId: uuid('title_id').notNull(),
  genreCode: text('genre_code').notNull(),
});

export const titleLocalizations = pgTable('title_localizations', {
  titleId: uuid('title_id').notNull(),
  languageCode: text('language_code'),
  displayTitle: text('display_title').notNull(),
  titleKind: text('title_kind').notNull(),
});

export const releaseEvents = pgTable('release_events', {
  id: uuid('id').primaryKey(),
  titleId: uuid('title_id').notNull(),
  releaseDate: date('release_date').notNull(),
  eventType: text('event_type').notNull().$type<'original_premiere'|'territory_theatrical'|'ott_premiere'|'rerelease'|'series_debut'>(),
  territoryCode: char('territory_code', { length: 2 }),
  verified: boolean('verified').notNull(),
  sourceRecordId: uuid('source_record_id').notNull(),
  providerCode: text('provider_code'),
});

export const sourceRecords = pgTable('source_records', {
  id: uuid('id').primaryKey(),
  sourceKey: text('source_key').notNull(),
  sourceUrl: text('source_url').notNull(),
});

export const streamingOffers = pgTable('streaming_offers', {
  id: uuid('id').primaryKey(),
  titleId: uuid('title_id').notNull(),
  providerCode: text('provider_code').notNull(),
  territoryCode: char('territory_code', { length: 2 }).notNull(),
  audioLanguageCode: text('audio_language_code'),
  verificationStatus: text('verification_status').notNull(),
  verifiedAt: timestamp('verified_at', { withTimezone: true }),
  validUntil: timestamp('valid_until', { withTimezone: true }),
  sourceRecordId: uuid('source_record_id').notNull(),
});

export const providers = pgTable('providers', {
  code: text('code').primaryKey(),
  displayName: text('display_name').notNull(),
});
