-- Remove the exact observations emitted by the first live YouTube monitor run
-- before stale catalogue-date filtering was added. These rows were review-only
-- and never promoted to verified movie release dates.
DELETE FROM source_observations
WHERE review_status = 'pending_review'
  AND (
    (source_key = 'yash_raj_films' AND external_id IN (
      'bQL9_VZPqeY',
      'Ceo3l26Dh4g',
      'Prltxy6qdS0',
      'IJFHVK1QV5Y',
      'e86YPgmbQeM',
      'LJjkZ70kfmw',
      'LlZIbvoBNyw',
      'mhJKw4zt6TU',
      'NZhZJZujAig',
      'K3epHDQ5rKM',
      '4WL4J8M3Fx4'
    ))
    OR (source_key = 'hombale_films' AND external_id = 'psSeBkqGVi0')
  );
