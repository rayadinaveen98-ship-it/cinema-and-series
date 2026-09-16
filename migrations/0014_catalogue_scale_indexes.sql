CREATE INDEX IF NOT EXISTS idx_movies_title_nocase ON movies(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_movies_country_release ON movies(country_code, release_date);
CREATE INDEX IF NOT EXISTS idx_movies_verification_release ON movies(verification_status, release_date);
