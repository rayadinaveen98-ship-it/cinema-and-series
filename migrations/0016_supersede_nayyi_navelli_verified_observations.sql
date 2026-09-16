-- Resolve legacy Amazon MGM Studios India observations for Nayyi Navelli that
-- are already represented by the curated, first-party verified 2026-10-16
-- release record. Preserve the observations for audit history.

UPDATE source_observations
SET review_status = 'superseded',
    reviewed_at = CURRENT_TIMESTAMP,
    review_notes = 'Superseded by curated Nayyi Navelli 2026-10-16 verification from Amazon MGM Studios India official first-party evidence.'
WHERE source_key = 'amazon_mgm_studios_india'
  AND candidate_release_date = '2026-10-16'
  AND title LIKE '%Nayyi Navelli%'
  AND review_status = 'pending_review';
