-- Resolve pre-dedupe review debt that is already represented by curated,
-- first-party verified release records.
--
-- These observations remain in source_observations for audit history, but they
-- are no longer actionable review items.

UPDATE source_observations
SET review_status = 'superseded',
    reviewed_at = CURRENT_TIMESTAMP,
    review_notes = 'Superseded by curated KING release verification from Red Chillies Entertainment official first-party evidence.'
WHERE source_key = 'red_chillies_entertainment'
  AND external_id = 'VU0hDIiL0xY'
  AND candidate_release_date = '2026-12-24'
  AND review_status = 'pending_review';

UPDATE source_observations
SET review_status = 'superseded',
    reviewed_at = CURRENT_TIMESTAMP,
    review_notes = 'Superseded by curated Dharma Productions release records for UDTA TEER (2026-10-09) and Naagzilla (2027-02-12).'
WHERE source_key = 'dharma_productions'
  AND external_url = 'https://dharma-production.com/'
  AND candidate_release_date IS NULL
  AND candidate_dates_json LIKE '%2026-10-09%'
  AND candidate_dates_json LIKE '%2027-02-12%'
  AND review_status = 'pending_review';
