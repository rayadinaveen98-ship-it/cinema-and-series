-- 0002: source-reviewed films, factual metadata only. Exact release evidence in docs.
-- Do not infer OTT availability, dubbing, festival screenings or dubbed-language identity.
-- Official producers/distributors, certification and contemporary film reporting checked 2026-11-18.
-- This is a curated, deterministic, additive seed; never an automatic source importer.
BEGIN;
INSERT INTO languages(code,name) VALUES
 ('hi','Hindi'),
 ('kn','Kannada'),
 ('te','Telugu'),
 ('ml','Malayalam'),
 ('ta','Tamil')
ON CONFLICT DO NOTHING;

INSERT INTO countries(code,display_name) VALUES
 ('IN','India')
ON CONFLICT DO NOTHING;

INSERT INTO genres(code,display_name) VALUES
 ('action','Action'),
 ('thriller','Thriller'),
 ('drama','Drama'),
 ('comedy','Comedy'),
 ('romance','Romance')
ON CONFLICT DO NOTHING;

INSERT INTO source_records(id,source_key,external_record_id,source_url,license_code,retrieved_at) VALUES
 ('b61d0a11-0000-4000-8000-000000001011','redchillies','jawan','https://www.redchillies.com/movies/jawan','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001012','yrf','jawan','https://www.yashrajfilms.com/movies/jawan','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001021','hombale','k-g-f-chapter-2','https://www.hombalefilms.com/movies/k-g-f-chapter-2','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001022','cbfc','DIL/2/32/2022-BAN','https://cbfcindia.gov.in/cbfcAdmin/search-result.php?recid=Q0EwMjA2MDMyMDIyMDAwMjQ%3D','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001031','hombale','kantara-2022','https://hombalefilms.com/movies/kantara','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001032','financialexpress','2892725','https://www.financialexpress.com/life/entertainment-rishab-shettys-kantara-will-also-be-released-in-english-chaluve-gowda-of-hombale-films-2892725/','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001033','hombale','kantara-movies-index','https://www.hombalefilms.com/movies','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001041','mythri','pushpa','https://mythrimoviemakers.com/pushpa/','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001042','indianexpress','7547843','https://indianexpress.com/article/entertainment/telugu/allu-arjun-pushpa-the-rise-release-date-7547843/lite/','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001043','googleplay','2BEA13F406AC4107MV','https://play.google.com/store/movies/details/Pushpa_The_Rise_Part_1?id=2BEA13F406AC4107MV','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001051','indianexpress','premalu-release-3655753','https://malayalam.indianexpress.com/entertainment/premalu-anweshippin-kandethum-lal-salaam-release-review-live-updates-3655753','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001052','toi','107363035','https://timesofindia.indiatimes.com/entertainment/malayalam/movies/news/naslen-and-mamitha-baijus-premalu-gets-a-release-date/amp_articleshow/107363035.cms','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001061','sunpictures','jailer','https://www.sunpictures.in/?sunpict_movies=jailer','FACT_REFERENCE_ONLY',NULL),
 ('b61d0a11-0000-4000-8000-000000001062','cbfc','DIL/2/118/2023-Che','https://cbfcindia.gov.in/cbfcAdmin/search-result.php?recid=Q0EwMzEzMDcyMDIzMDAwMjE%3D','FACT_REFERENCE_ONLY',NULL)
ON CONFLICT DO NOTHING;

INSERT INTO titles(id,title_type,original_title,publication_status,first_release_year) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','movie','Jawan','published','2023'),
 ('b61d0a11-0000-4000-8000-000000000102','movie','K.G.F: Chapter 2','published','2022'),
 ('b61d0a11-0000-4000-8000-000000000103','movie','Kantara','published','2022'),
 ('b61d0a11-0000-4000-8000-000000000104','movie','Pushpa: The Rise','published','2021'),
 ('b61d0a11-0000-4000-8000-000000000105','movie','Premalu','published','2024'),
 ('b61d0a11-0000-4000-8000-000000000106','movie','Jailer','published','2023')
ON CONFLICT DO NOTHING;

INSERT INTO title_languages(title_id,language_code,relation) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','hi','original'),
 ('b61d0a11-0000-4000-8000-000000000102','kn','original'),
 ('b61d0a11-0000-4000-8000-000000000103','kn','original'),
 ('b61d0a11-0000-4000-8000-000000000104','te','original'),
 ('b61d0a11-0000-4000-8000-000000000105','ml','original'),
 ('b61d0a11-0000-4000-8000-000000000106','ta','original')
ON CONFLICT DO NOTHING;

INSERT INTO title_countries(title_id,country_code) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','IN'),
 ('b61d0a11-0000-4000-8000-000000000102','IN'),
 ('b61d0a11-0000-4000-8000-000000000103','IN'),
 ('b61d0a11-0000-4000-8000-000000000104','IN'),
 ('b61d0a11-0000-4000-8000-000000000105','IN'),
 ('b61d0a11-0000-4000-8000-000000000106','IN')
ON CONFLICT DO NOTHING;

INSERT INTO title_genres(title_id,genre_code) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','action'),
 ('b61d0a11-0000-4000-8000-000000000101','thriller'),
 ('b61d0a11-0000-4000-8000-000000000102','action'),
 ('b61d0a11-0000-4000-8000-000000000102','thriller'),
 ('b61d0a11-0000-4000-8000-000000000103','action'),
 ('b61d0a11-0000-4000-8000-000000000103','thriller'),
 ('b61d0a11-0000-4000-8000-000000000104','action'),
 ('b61d0a11-0000-4000-8000-000000000104','drama'),
 ('b61d0a11-0000-4000-8000-000000000105','comedy'),
 ('b61d0a11-0000-4000-8000-000000000105','romance'),
 ('b61d0a11-0000-4000-8000-000000000106','action')
ON CONFLICT DO NOTHING;

INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id,provider_code) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','2023-09-07','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001012',NULL),
 ('b61d0a11-0000-4000-8000-000000000102','2022-04-14','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001021',NULL),
 ('b61d0a11-0000-4000-8000-000000000103','2022-09-30','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001033',NULL),
 ('b61d0a11-0000-4000-8000-000000000104','2021-12-17','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001042',NULL),
 ('b61d0a11-0000-4000-8000-000000000105','2024-02-09','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001051',NULL),
 ('b61d0a11-0000-4000-8000-000000000106','2023-08-10','original_premiere','IN',true,'b61d0a11-0000-4000-8000-000000001061',NULL)
ON CONFLICT DO NOTHING;

INSERT INTO field_provenance(title_id,field_path,source_record_id,verification_status,reviewed_at) VALUES
 ('b61d0a11-0000-4000-8000-000000000101','original_title','b61d0a11-0000-4000-8000-000000001011','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000101','original_language.hi','b61d0a11-0000-4000-8000-000000001012','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000101','release.original_premiere','b61d0a11-0000-4000-8000-000000001012','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000102','original_title','b61d0a11-0000-4000-8000-000000001021','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000102','original_language.kn','b61d0a11-0000-4000-8000-000000001022','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000102','release.original_premiere','b61d0a11-0000-4000-8000-000000001021','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000103','original_title','b61d0a11-0000-4000-8000-000000001031','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000103','original_language.kn','b61d0a11-0000-4000-8000-000000001032','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000103','release.original_premiere','b61d0a11-0000-4000-8000-000000001033','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000104','original_title','b61d0a11-0000-4000-8000-000000001041','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000104','original_language.te','b61d0a11-0000-4000-8000-000000001043','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000104','release.original_premiere','b61d0a11-0000-4000-8000-000000001042','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000105','original_title','b61d0a11-0000-4000-8000-000000001051','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000105','original_language.ml','b61d0a11-0000-4000-8000-000000001052','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000105','release.original_premiere','b61d0a11-0000-4000-8000-000000001051','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000106','original_title','b61d0a11-0000-4000-8000-000000001061','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000106','original_language.ta','b61d0a11-0000-4000-8000-000000001062','verified',now()),
 ('b61d0a11-0000-4000-8000-000000000106','release.original_premiere','b61d0a11-0000-4000-8000-000000001061','verified',now())
ON CONFLICT DO NOTHING;

-- Reject the seed if a fixed ID has been reused or its canonical claim has changed.
DO $certify$
BEGIN
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000101'::uuid AND t.title_type='movie'
     AND t.original_title='Jawan' AND t.first_release_year=2023
     AND t.publication_status='published' AND tl.language_code='hi'
     AND re.release_date='2023-09-07'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 101'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000102'::uuid AND t.title_type='movie'
     AND t.original_title='K.G.F: Chapter 2' AND t.first_release_year=2022
     AND t.publication_status='published' AND tl.language_code='kn'
     AND re.release_date='2022-04-14'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 102'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000103'::uuid AND t.title_type='movie'
     AND t.original_title='Kantara' AND t.first_release_year=2022
     AND t.publication_status='published' AND tl.language_code='kn'
     AND re.release_date='2022-09-30'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 103'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000104'::uuid AND t.title_type='movie'
     AND t.original_title='Pushpa: The Rise' AND t.first_release_year=2021
     AND t.publication_status='published' AND tl.language_code='te'
     AND re.release_date='2021-12-17'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 104'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000105'::uuid AND t.title_type='movie'
     AND t.original_title='Premalu' AND t.first_release_year=2024
     AND t.publication_status='published' AND tl.language_code='ml'
     AND re.release_date='2024-02-09'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 105'; END IF;
 IF NOT EXISTS (
   SELECT 1 FROM titles t
   JOIN title_languages tl ON tl.title_id=t.id AND tl.relation='original'
   JOIN release_events re ON re.title_id=t.id AND re.event_type='original_premiere'
   WHERE t.id='b61d0a11-0000-4000-8000-000000000106'::uuid AND t.title_type='movie'
     AND t.original_title='Jailer' AND t.first_release_year=2023
     AND t.publication_status='published' AND tl.language_code='ta'
     AND re.release_date='2023-08-10'::date AND re.verified=true
 ) THEN RAISE EXCEPTION 'Curated identity/release mismatch: 106'; END IF;
END
$certify$;

-- Audit only the fact that the curated source-reviewed seed inserted the canonical
-- title; reviewer identities and current OTT availability are not asserted.
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000101'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','Jawan','theatricalDate','2023-09-07','language','hi','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000101'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000102'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','K.G.F: Chapter 2','theatricalDate','2022-04-14','language','kn','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000102'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000103'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','Kantara','theatricalDate','2022-09-30','language','kn','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000103'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000104'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','Pushpa: The Rise','theatricalDate','2021-12-17','language','te','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000104'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000105'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','Premalu','theatricalDate','2024-02-09','language','ml','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000105'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'b61d0a11-0000-4000-8000-000000000106'::uuid,'curation_script','curated_pilot_seed',
  jsonb_build_object('title','Jailer','theatricalDate','2023-08-10','language','ta','provenance','manual_source_review')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log
  WHERE title_id='b61d0a11-0000-4000-8000-000000000106'::uuid AND actor_type='curation_script' AND action='curated_pilot_seed'
);
COMMIT;
