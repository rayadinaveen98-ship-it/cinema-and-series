PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movies (
  id TEXT PRIMARY KEY,
  wikidata_qid TEXT UNIQUE,
  title TEXT NOT NULL,
  native_title TEXT,
  language_code TEXT,
  language_name TEXT NOT NULL DEFAULT 'Unknown',
  country_code TEXT NOT NULL DEFAULT 'IN',
  release_date TEXT NOT NULL,
  verification_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (verification_status IN ('verified','supported','unconfirmed')),
  release_date_source TEXT NOT NULL DEFAULT 'wikidata',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_release_date ON movies(release_date);
CREATE INDEX IF NOT EXISTS idx_movies_language_release ON movies(language_code, release_date);

CREATE TABLE IF NOT EXISTS release_evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  movie_id TEXT NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
  claimed_release_date TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_title TEXT,
  is_official INTEGER NOT NULL DEFAULT 0 CHECK (is_official IN (0,1)),
  retrieved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(movie_id, source_url, claimed_release_date)
);

CREATE INDEX IF NOT EXISTS idx_release_evidence_movie ON release_evidence(movie_id);
