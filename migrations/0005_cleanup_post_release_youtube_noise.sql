-- Remove review-only observations discovered during monitor tuning that are
-- clearly post-release/promotional chatter rather than release announcements.
-- These rows were never accepted or used to verify a public movie date.
DELETE FROM source_observations
WHERE source_key = 'uv_creations'
  AND review_status = 'pending_review'
  AND external_id IN (
    '2KL-ns-O9Co',
    'kvoog-t3ELw',
    '6LaIOJHtVZE'
  );
