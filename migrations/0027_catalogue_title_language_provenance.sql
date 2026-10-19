-- Record explicit film-language evidence on year-precision catalogue rows.
-- Existing non-unknown language values are preserved; the columns alone do
-- not assign or verify any language.
ALTER TABLE catalogue_titles ADD COLUMN language_source TEXT;
ALTER TABLE catalogue_titles ADD COLUMN language_source_url TEXT;
