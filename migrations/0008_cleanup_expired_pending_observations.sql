-- Keep the live review queue future-facing.
--
-- Pending observations are provisional monitoring signals only. Once their
-- candidate release date is in the past, they are no longer useful to the
-- active review queue and were never accepted as verification evidence.
-- The monitors now reject already-past dates at scan time, so this migration
-- removes legacy rows created before that guard existed.
DELETE FROM source_observations
WHERE review_status = 'pending_review'
  AND candidate_release_date IS NOT NULL
  AND date(candidate_release_date) < date('now');
