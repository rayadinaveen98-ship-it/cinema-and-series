UPDATE source_observations
SET review_status = 'superseded',
    reviewed_at = CURRENT_TIMESTAMP,
    review_notes = 'Superseded: T-Series independently corroborates the already verified RANABAALI release date from Mythri Movie Makers; retained as first-party corroboration, not active review debt.'
WHERE source_key = 't_series'
  AND review_status = 'pending_review'
  AND lower(title) LIKE '%ranabaali%'
  AND (
    candidate_release_date = '2026-10-16'
    OR candidate_dates_json LIKE '%2026-10-16%'
  );
