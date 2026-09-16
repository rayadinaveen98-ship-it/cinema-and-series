CREATE TABLE IF NOT EXISTS source_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_key TEXT NOT NULL,
  external_id TEXT NOT NULL,
  external_url TEXT NOT NULL,
  title TEXT NOT NULL,
  published_at TEXT,
  candidate_release_date TEXT,
  candidate_dates_json TEXT NOT NULL DEFAULT '[]',
  review_status TEXT NOT NULL DEFAULT 'pending_review'
    CHECK (review_status IN ('pending_review','accepted','rejected','superseded')),
  observed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TEXT,
  review_notes TEXT,
  FOREIGN KEY (source_key) REFERENCES source_channels(source_key) ON DELETE CASCADE,
  UNIQUE (source_key, external_id)
);

CREATE INDEX IF NOT EXISTS idx_source_observations_review
  ON source_observations(review_status, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_source_observations_candidate_date
  ON source_observations(candidate_release_date)
  WHERE candidate_release_date IS NOT NULL;
