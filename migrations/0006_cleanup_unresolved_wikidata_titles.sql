-- Remove unresolved open-data rows whose public title is only the Wikidata QID.
-- Verified/curated rows are never touched. release_evidence cascades on delete.
DELETE FROM movies
WHERE verification_status = 'unconfirmed'
  AND wikidata_qid IS NOT NULL
  AND title = wikidata_qid;
