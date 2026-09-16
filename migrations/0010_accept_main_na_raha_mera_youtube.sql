UPDATE source_observations
SET review_status = 'accepted',
    reviewed_at = CURRENT_TIMESTAMP,
    review_notes = 'Accepted after first-party T-Series teaser description explicitly stated: In cinemas 23 October 2026.'
WHERE source_key = 't_series'
  AND external_id = 'sinO13Uvofg'
  AND candidate_release_date = '2026-10-23'
  AND review_status = 'pending_review';
