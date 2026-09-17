-- Series Native Title Enrichment V1 provenance.
-- Current Series native-title coverage is zero, so no legacy value requires backfill.
-- New values are written only from explicit Wikidata title semantics:
--   1) P1705 native label, or
--   2) P1476 title explicitly qualified with P3831=Q1294573 (original title).

ALTER TABLE series_titles ADD COLUMN native_title_language_code TEXT;
ALTER TABLE series_titles ADD COLUMN native_title_source TEXT;
ALTER TABLE series_titles ADD COLUMN native_title_source_url TEXT;
