-- Recommendation Metadata Foundation V1.
-- Shared metadata projection for Movies + Series used by personalized discovery.
-- This migration is committed for review only; do not apply to production until
-- the read-only coverage audit demonstrates useful yield and quality.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS recommendation_titles (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT NOT NULL UNIQUE,
  media_type TEXT NOT NULL CHECK (media_type IN ('movie','series')),
  display_title TEXT NOT NULL,
  source_table TEXT NOT NULL CHECK (source_table IN ('movies','catalogue_titles','series_titles')),
  source_id TEXT NOT NULL,
  source_url TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendation_titles_media_type
  ON recommendation_titles(media_type, display_title COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS genres (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_genres_name
  ON genres(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS people (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_people_name
  ON people(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS title_genres (
  title_id TEXT NOT NULL REFERENCES recommendation_titles(id) ON DELETE CASCADE,
  genre_id TEXT NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
  source_property TEXT NOT NULL CHECK (source_property = 'P136'),
  source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (title_id, genre_id, source_property)
);

CREATE INDEX IF NOT EXISTS idx_title_genres_genre
  ON title_genres(genre_id, title_id);

CREATE TABLE IF NOT EXISTS title_credits (
  title_id TEXT NOT NULL REFERENCES recommendation_titles(id) ON DELETE CASCADE,
  person_id TEXT NOT NULL REFERENCES people(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('director','creator','cast')),
  source_property TEXT NOT NULL CHECK (source_property IN ('P57','P170','P161')),
  source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (title_id, person_id, role, source_property)
);

CREATE INDEX IF NOT EXISTS idx_title_credits_person_role
  ON title_credits(person_id, role, title_id);
CREATE INDEX IF NOT EXISTS idx_title_credits_title_role
  ON title_credits(title_id, role);
