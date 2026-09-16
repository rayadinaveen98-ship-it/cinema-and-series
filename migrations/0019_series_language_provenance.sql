ALTER TABLE series_titles ADD COLUMN language_source TEXT;
ALTER TABLE series_titles ADD COLUMN language_source_url TEXT;

-- Existing explicit languages came from language-specific Wikipedia discovery
-- categories. Preserve that provenance before Wikidata enrichment begins.
UPDATE series_titles
SET language_source = COALESCE(language_source, 'wikipedia_category'),
    language_source_url = COALESCE(language_source_url, source_url)
WHERE language_name IS NOT NULL
  AND TRIM(language_name) <> ''
  AND LOWER(language_name) <> 'unknown';
