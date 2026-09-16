-- Broad catalogue discovery projection for titles whose exact release day is
-- not yet known. This table deliberately does NOT overload movies.release_date
-- with fake January 1 dates. Exact-day release intelligence remains in movies.

CREATE TABLE IF NOT EXISTS catalogue_titles (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT,
  wikipedia_page_id INTEGER,
  title TEXT NOT NULL,
  release_year INTEGER NOT NULL CHECK (release_year BETWEEN 1888 AND 2200),
  date_precision TEXT NOT NULL DEFAULT 'year' CHECK (date_precision = 'year'),
  language_name TEXT NOT NULL DEFAULT 'Unknown',
  country_code TEXT NOT NULL DEFAULT 'XX',
  source_category TEXT NOT NULL,
  source_url TEXT NOT NULL,
  verification_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status = 'unconfirmed'),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_catalogue_titles_wikidata_qid
  ON catalogue_titles(wikidata_qid)
  WHERE wikidata_qid IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_catalogue_titles_wikipedia_page
  ON catalogue_titles(wikipedia_page_id)
  WHERE wikipedia_page_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_catalogue_titles_year_title
  ON catalogue_titles(release_year DESC, title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_catalogue_titles_country_year
  ON catalogue_titles(country_code, release_year DESC);
CREATE INDEX IF NOT EXISTS idx_catalogue_titles_language_year
  ON catalogue_titles(language_name, release_year DESC);
