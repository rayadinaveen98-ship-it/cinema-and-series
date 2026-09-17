-- Series First-Air-Year Enrichment V1 provenance.
-- Existing first_air_year values predate field-level provenance and are intentionally
-- not backfilled here: their exact year-bearing discovery category cannot always be
-- reconstructed after later catalogue merges. New enrichment writes record explicit
-- Wikidata P580 provenance without rewriting historical values.

ALTER TABLE series_titles ADD COLUMN first_air_year_source TEXT;
ALTER TABLE series_titles ADD COLUMN first_air_year_source_url TEXT;
