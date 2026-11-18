-- Synthetic, disposable PostgreSQL test. Transaction is intentionally rolled back.
BEGIN;
INSERT INTO languages(code,name) VALUES ('te','Telugu'),('en','English');
INSERT INTO countries(code,display_name) VALUES ('IN','India');
INSERT INTO genres(code,display_name) VALUES ('action','Action');
INSERT INTO titles(id,title_type,original_title,publication_status,first_release_year)
VALUES ('00000000-0000-4000-8000-000000000001','movie','Synthetic Telugu Film','published',2020);
INSERT INTO title_languages(title_id,language_code,relation)
VALUES ('00000000-0000-4000-8000-000000000001','te','original');
INSERT INTO title_genres(title_id,genre_code)
VALUES ('00000000-0000-4000-8000-000000000001','action');
INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
VALUES ('00000000-0000-4000-8000-000000000001',NULL,'Synthetic Telugu Film','original');
INSERT INTO source_records(id,source_key,external_record_id,source_url,license_code)
VALUES ('00000000-0000-4000-8000-000000000002','synthetic','demo-001','https://example.org/demo','TEST_ONLY');
INSERT INTO external_ids(title_id,source_key,external_id,source_record_id)
VALUES ('00000000-0000-4000-8000-000000000001','synthetic','demo-001','00000000-0000-4000-8000-000000000002');

INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id)
VALUES
('00000000-0000-4000-8000-000000000001','2020-02-29','original_premiere',NULL,true,'00000000-0000-4000-8000-000000000002'),
('00000000-0000-4000-8000-000000000001','2020-02-29','territory_theatrical','IN',true,'00000000-0000-4000-8000-000000000002'),
('00000000-0000-4000-8000-000000000001','2020-02-29','ott_premiere','IN',true,'00000000-0000-4000-8000-000000000002');

DO $verify_calendar$
DECLARE count_value integer;
BEGIN
  SELECT count(*) INTO count_value
  FROM release_events
  WHERE event_type='original_premiere' AND verified=true
    AND extract(month from release_date)=2 AND extract(day from release_date)=29;
  IF count_value<>1 THEN RAISE EXCEPTION 'Original-premiere calendar mixed other release types: %',count_value; END IF;
END
$verify_calendar$;

DO $verify_uniqueness$
DECLARE blocked boolean := false;
BEGIN
  BEGIN
    INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id)
    VALUES ('00000000-0000-4000-8000-000000000001','2020-02-29','original_premiere',NULL,true,'00000000-0000-4000-8000-000000000002');
  EXCEPTION WHEN unique_violation THEN blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Duplicate NULL-territory original premiere accepted'; END IF;
  blocked := false;
  BEGIN
    INSERT INTO external_ids(title_id,source_key,external_id,source_record_id)
    VALUES ('00000000-0000-4000-8000-000000000001','synthetic','demo-001','00000000-0000-4000-8000-000000000002');
  EXCEPTION WHEN unique_violation THEN blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Duplicate source external identity accepted'; END IF;
  blocked := false;
  BEGIN
    INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
    VALUES ('00000000-0000-4000-8000-000000000001',NULL,'Synthetic Telugu Film','original');
  EXCEPTION WHEN unique_violation THEN blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Duplicate NULL-language title localization accepted'; END IF;
END
$verify_uniqueness$;

DO $verify_constraints$
DECLARE blocked boolean := false;
BEGIN
  BEGIN
    INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id)
    VALUES ('00000000-0000-4000-8000-000000000001','2020-02-29','invented_type',NULL,true,'00000000-0000-4000-8000-000000000002');
  EXCEPTION WHEN check_violation THEN blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'Invalid release event type accepted'; END IF;
END
$verify_constraints$;

ROLLBACK;
