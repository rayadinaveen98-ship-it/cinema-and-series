-- Series Engine V1: series-run catalogue projection plus season/episode identity scaffolding.
-- This stays separate from the movie tables so episodic structure never overloads movie semantics.

CREATE TABLE IF NOT EXISTS series_titles (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT,
  wikipedia_page_id INTEGER,
  title TEXT NOT NULL,
  native_title TEXT,
  series_kind TEXT NOT NULL DEFAULT 'series' CHECK (series_kind IN ('series','web_series','miniseries','anthology','unknown')),
  language_name TEXT NOT NULL DEFAULT 'Unknown',
  country_code TEXT NOT NULL DEFAULT 'XX',
  first_air_year INTEGER CHECK (first_air_year IS NULL OR first_air_year BETWEEN 1900 AND 2200),
  last_air_year INTEGER CHECK (last_air_year IS NULL OR last_air_year BETWEEN 1900 AND 2200),
  lifecycle_status TEXT NOT NULL DEFAULT 'unknown' CHECK (lifecycle_status IN ('unknown','upcoming','ongoing','ended','limited')),
  season_count INTEGER CHECK (season_count IS NULL OR season_count >= 0),
  episode_count INTEGER CHECK (episode_count IS NULL OR episode_count >= 0),
  source_category TEXT NOT NULL,
  source_url TEXT NOT NULL,
  verification_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('verified','supported','unconfirmed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_series_titles_wikidata_qid
  ON series_titles(wikidata_qid)
  WHERE wikidata_qid IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_series_titles_wikipedia_page
  ON series_titles(wikipedia_page_id)
  WHERE wikipedia_page_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_series_titles_first_air_title
  ON series_titles(first_air_year DESC, title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_series_titles_country_year
  ON series_titles(country_code, first_air_year DESC);
CREATE INDEX IF NOT EXISTS idx_series_titles_language_year
  ON series_titles(language_name, first_air_year DESC);
CREATE INDEX IF NOT EXISTS idx_series_titles_kind_year
  ON series_titles(series_kind, first_air_year DESC);

CREATE TABLE IF NOT EXISTS series_seasons (
  id TEXT PRIMARY KEY,
  series_id TEXT NOT NULL REFERENCES series_titles(id) ON DELETE CASCADE,
  season_number INTEGER,
  display_name TEXT,
  release_year INTEGER CHECK (release_year IS NULL OR release_year BETWEEN 1900 AND 2200),
  source_url TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('verified','supported','unconfirmed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(series_id, season_number)
);
CREATE INDEX IF NOT EXISTS idx_series_seasons_series ON series_seasons(series_id, season_number);

CREATE TABLE IF NOT EXISTS series_episodes (
  id TEXT PRIMARY KEY,
  series_id TEXT NOT NULL REFERENCES series_titles(id) ON DELETE CASCADE,
  season_id TEXT REFERENCES series_seasons(id) ON DELETE SET NULL,
  episode_number INTEGER,
  title TEXT,
  air_date TEXT,
  source_url TEXT,
  verification_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('verified','supported','unconfirmed')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_series_episodes_series ON series_episodes(series_id, season_id, episode_number);
CREATE INDEX IF NOT EXISTS idx_series_episodes_air_date ON series_episodes(air_date);
