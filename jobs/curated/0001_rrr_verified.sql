-- Curated factual pilot record; NOT a bulk scraper or auto-import.
-- Verified: Wikidata Q60424165 (CC0) and official ZEE5 title page (facts/link only).
-- The historical ZEE5 premiere is distinct from CURRENT streaming availability.
-- This script is idempotent and only adds missing values. No destructive overwrites.
BEGIN;
INSERT INTO languages(code,name) VALUES ('te','Telugu'),('en','English')
  ON CONFLICT DO NOTHING;
INSERT INTO countries(code,display_name) VALUES ('IN','India')
  ON CONFLICT DO NOTHING;
INSERT INTO genres(code,display_name) VALUES ('action','Action'),('drama','Drama')
  ON CONFLICT DO NOTHING;
INSERT INTO providers(code,display_name) VALUES ('zee5','ZEE5')
  ON CONFLICT DO NOTHING;

INSERT INTO source_records(id,source_key,external_record_id,source_url,license_code)
VALUES
 ('7fe240ab-0b6f-4691-a614-a56a90422031','wikidata','Q60424165','https://www.wikidata.org/wiki/Q60424165','CC0'),
 ('7fe240ab-0b6f-4691-a614-a56a90422032','zee5','0-0-1z5145092','https://www.zee5.com/movies/details/rrr/0-0-1z5145092','FACT_REFERENCE_ONLY')
ON CONFLICT DO NOTHING;

INSERT INTO titles(id,title_type,original_title,publication_status,first_release_year)
VALUES ('7fe240ab-0b6f-4691-a614-a56a90422022','movie','RRR','published',2022)
ON CONFLICT DO NOTHING;

INSERT INTO title_languages(title_id,language_code,relation)
VALUES ('7fe240ab-0b6f-4691-a614-a56a90422022','te','original')
ON CONFLICT DO NOTHING;
INSERT INTO title_countries(title_id,country_code)
VALUES ('7fe240ab-0b6f-4691-a614-a56a90422022','IN')
ON CONFLICT DO NOTHING;
INSERT INTO title_genres(title_id,genre_code)
VALUES
 ('7fe240ab-0b6f-4691-a614-a56a90422022','action'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','drama')
ON CONFLICT DO NOTHING;
INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
VALUES ('7fe240ab-0b6f-4691-a614-a56a90422022','en','RRR','official')
ON CONFLICT DO NOTHING;
INSERT INTO external_ids(title_id,source_key,external_id,source_record_id)
VALUES
 ('7fe240ab-0b6f-4691-a614-a56a90422022','wikidata','Q60424165','7fe240ab-0b6f-4691-a614-a56a90422031'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','zee5','0-0-1z5145092','7fe240ab-0b6f-4691-a614-a56a90422032')
ON CONFLICT DO NOTHING;

INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id,provider_code)
VALUES
 ('7fe240ab-0b6f-4691-a614-a56a90422022','2022-03-25','original_premiere','IN',true,'7fe240ab-0b6f-4691-a614-a56a90422031',NULL),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','2022-05-20','ott_premiere','IN',true,'7fe240ab-0b6f-4691-a614-a56a90422032','zee5')
ON CONFLICT DO NOTHING;

-- Current provider listing is NOT declared verified without territory-specific playback check.
INSERT INTO streaming_offers(title_id,provider_code,territory_code,audio_language_code,verification_status,verified_at,source_record_id)
VALUES ('7fe240ab-0b6f-4691-a614-a56a90422022','zee5','IN','te','unverified',NULL,'7fe240ab-0b6f-4691-a614-a56a90422032')
ON CONFLICT DO NOTHING;

INSERT INTO field_provenance(title_id,field_path,source_record_id,verification_status)
VALUES
 ('7fe240ab-0b6f-4691-a614-a56a90422022','original_title','7fe240ab-0b6f-4691-a614-a56a90422031','verified'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','original_language.te','7fe240ab-0b6f-4691-a614-a56a90422031','verified'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','genre.action','7fe240ab-0b6f-4691-a614-a56a90422031','verified'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','genre.drama','7fe240ab-0b6f-4691-a614-a56a90422032','verified'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','release.original_premiere','7fe240ab-0b6f-4691-a614-a56a90422031','verified'),
 ('7fe240ab-0b6f-4691-a614-a56a90422022','release.ott_premiere','7fe240ab-0b6f-4691-a614-a56a90422032','verified')
ON CONFLICT DO NOTHING;
COMMIT;
