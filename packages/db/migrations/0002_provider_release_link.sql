-- 0002: historical OTT premiere provider linkage and idempotent scoped offers.
-- Depends on 0001_catalogue.sql; additive, no existing catalogue rows rewritten.
BEGIN;
ALTER TABLE release_events
  ADD COLUMN provider_code text REFERENCES providers(code);
CREATE INDEX release_events_provider_idx
  ON release_events (provider_code, release_date)
  WHERE provider_code IS NOT NULL;
CREATE UNIQUE INDEX offers_unique_scope_idx
  ON streaming_offers (title_id, provider_code, territory_code, audio_language_code)
  NULLS NOT DISTINCT;
COMMIT;
