-- 0004: never fabricate a retrieval timestamp for unfetched source pointers.
-- Additive metadata correction; existing verified source dates preserved.
BEGIN;
ALTER TABLE source_records ALTER COLUMN retrieved_at DROP NOT NULL;
COMMENT ON COLUMN source_records.retrieved_at IS
  'Timestamp of an actual source fetch; NULL for unverified staged-only source pointers';
COMMIT;
