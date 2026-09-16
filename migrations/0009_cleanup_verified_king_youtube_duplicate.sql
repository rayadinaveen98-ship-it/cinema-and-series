-- KING is now curated from Red Chillies Entertainment's first-party website.
-- Remove pending YouTube reminders for the same source/date so the review
-- queue contains only evidence that can still change catalogue state.
DELETE FROM source_observations
WHERE source_key = 'red_chillies_entertainment'
  AND review_status = 'pending_review'
  AND candidate_release_date = '2026-12-24';
