-- Series Native Title Enrichment V1 provenance.
-- Current Series native-title coverage is zero, so no legacy value requires backfill.
-- New values are written only from explicit Wikidata P1705 native-label claims.

ALTER TABLE series_titles ADD COLUMN native_title_language_code TEXT;
ALTER TABLE series_titles ADD COLUMN native_title_source TEXT;
ALTER TABLE series_titles ADD COLUMN native_title_source_url TEXT;
