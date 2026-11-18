-- 0005: accurately represent the first publicly accessible TV season launch.
-- Dark was screened at a festival before Netflix release; Netflix launch must
-- not be classified as the first theatrical film premiere.
-- Additive schema change; does not rewrite any existing title or premiere.
BEGIN;
ALTER TABLE release_events DROP CONSTRAINT release_events_event_type_check;
ALTER TABLE release_events ADD CONSTRAINT release_events_event_type_check
  CHECK (event_type IN (
    'original_premiere','territory_theatrical','ott_premiere','rerelease','series_debut'
  ));
COMMIT;
