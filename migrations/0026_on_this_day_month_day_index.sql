-- Optimize /api/on-this-day anniversary lookups in Cloudflare D1.
-- The route filters by substr(release_date, 6, 5) (MM-DD), which does not
-- benefit from indexes on the full release_date column. Every request
-- previously risked a broad table scan, increasing daily row-read usage.
-- This expression index supports the exact existing predicate, descending
-- date ordering and the title tie-breaker. It does not alter any rows.
CREATE INDEX IF NOT EXISTS idx_movies_on_this_day_month_date
ON movies (substr(release_date, 6, 5), release_date DESC, title COLLATE NOCASE ASC);
