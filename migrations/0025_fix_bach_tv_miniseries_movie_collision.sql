-- Reviewed cross-type media correction: 1985 German 4-part miniseries.
-- Source audit: GitHub Actions run 38851453997; English Wikipedia and IMDb
-- both classify Q1475491 as an episodic TV series, already present in series_titles.
-- Remove ONLY the mislabeled year-precision Movie projection.
-- The correct Series record is unchanged.
DELETE FROM catalogue_titles
WHERE wikidata_qid = 'Q1475491'
  AND title = 'Johann Sebastian Bach (TV series)'
  AND release_year = 1985
  AND source_category = 'Category:1985 German films';
