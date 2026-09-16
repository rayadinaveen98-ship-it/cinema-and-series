ALTER TABLE movies ADD COLUMN poster_url TEXT;
ALTER TABLE movies ADD COLUMN backdrop_url TEXT;
ALTER TABLE movies ADD COLUMN artwork_source TEXT;
ALTER TABLE movies ADD COLUMN artwork_source_url TEXT;
ALTER TABLE movies ADD COLUMN artwork_updated_at TEXT;

CREATE INDEX IF NOT EXISTS idx_movies_artwork_source ON movies(artwork_source);
