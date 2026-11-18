-- Curated international pilot batch 0003: 4 films + 2 series, copyright-free factual pointers.
-- Film original_premiere means *first theatrical release in originating market*.
-- series_debut is the first public Netflix season launch, NOT festival or theatrical screening.
-- Links are informational source pointers, not rights to copy images or programmes.
-- No current streaming_offer rows and no claim of present licensing.
BEGIN;
INSERT INTO languages(code,name) VALUES
 ('ko','Korean'),
 ('ja','Japanese'),
 ('fr','French'),
 ('en','English'),
 ('de','German')
ON CONFLICT DO NOTHING;

INSERT INTO countries(code,display_name) VALUES
 ('KR','South Korea'),
 ('JP','Japan'),
 ('FR','France'),
 ('US','United States'),
 ('DE','Germany')
ON CONFLICT DO NOTHING;

INSERT INTO genres(code,display_name) VALUES
 ('drama','Drama'),
 ('thriller','Thriller'),
 ('animation','Animation'),
 ('fantasy','Fantasy'),
 ('comedy','Comedy'),
 ('science-fiction','Science Fiction'),
 ('mystery','Mystery')
ON CONFLICT DO NOTHING;

INSERT INTO providers(code,display_name) VALUES
 ('netflix','Netflix')
ON CONFLICT DO NOTHING;

INSERT INTO source_records(id,source_key,external_record_id,source_url,license_code,retrieved_at) VALUES
 ('c73e1404-0000-4000-8000-000000002011','kofic','20183782','https://www.koreanfilm.or.kr/eng/films/index/filmsView.jsp?movieCd=20183782','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002012','kofic-news','parasite-356','https://www.koreanfilm.or.kr/eng/news/newfilm.jsp?mode=VIEW&pageRowSize=10&seq=356','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002021','ghibli','chihiro','https://www.ghibli.jp/works/chihiro/','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002022','ghibli','chronology','https://www.ghibli.jp/chronology/','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002031','unifrance','31884-en','https://en.unifrance.org/movie/31884/the-intouchables','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002032','unifrance','31884-jp','https://japan.unifrance.org/%E6%98%A0%E7%94%BB/31884/the-intouchables','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002041','afi','inception','https://watch.afi.com/movie/inception','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002042','thenumbers','inception-2010','https://www.the-numbers.com/movie/Inception','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002051','netflix-news','dark-first-season-launch-2017','https://about.netflix.com/en/news/dark-is-coming-12-1-see-the-spellbinding-date-announcement','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002052','netflix','80100172','https://www.netflix.com/title/80100172','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002061','netflix-news','squid-game-first-season-2021','https://about.netflix.com/en/news/squid-game-invites-you-to-deadly-childhood-games-on-september-17','FACT_REFERENCE_ONLY',NULL),
 ('c73e1404-0000-4000-8000-000000002062','netflix','81040344','https://www.netflix.com/title/81040344','FACT_REFERENCE_ONLY',NULL)
ON CONFLICT DO NOTHING;

INSERT INTO titles(id,title_type,original_title,publication_status,first_release_year) VALUES
 ('c73e1404-0000-4000-8000-000000000201','movie','기생충','published','2019'),
 ('c73e1404-0000-4000-8000-000000000202','movie','千と千尋の神隠し','published','2001'),
 ('c73e1404-0000-4000-8000-000000000203','movie','Intouchables','published','2011'),
 ('c73e1404-0000-4000-8000-000000000204','movie','Inception','published','2010'),
 ('c73e1404-0000-4000-8000-000000000205','series','Dark','published','2017'),
 ('c73e1404-0000-4000-8000-000000000206','series','오징어 게임','published','2021')
ON CONFLICT DO NOTHING;

INSERT INTO title_languages(title_id,language_code,relation) VALUES
 ('c73e1404-0000-4000-8000-000000000201','ko','original'),
 ('c73e1404-0000-4000-8000-000000000202','ja','original'),
 ('c73e1404-0000-4000-8000-000000000203','fr','original'),
 ('c73e1404-0000-4000-8000-000000000204','en','original'),
 ('c73e1404-0000-4000-8000-000000000205','de','original'),
 ('c73e1404-0000-4000-8000-000000000206','ko','original')
ON CONFLICT DO NOTHING;

INSERT INTO title_countries(title_id,country_code) VALUES
 ('c73e1404-0000-4000-8000-000000000201','KR'),
 ('c73e1404-0000-4000-8000-000000000202','JP'),
 ('c73e1404-0000-4000-8000-000000000203','FR'),
 ('c73e1404-0000-4000-8000-000000000204','US'),
 ('c73e1404-0000-4000-8000-000000000205','DE'),
 ('c73e1404-0000-4000-8000-000000000206','KR')
ON CONFLICT DO NOTHING;

INSERT INTO title_genres(title_id,genre_code) VALUES
 ('c73e1404-0000-4000-8000-000000000201','drama'),
 ('c73e1404-0000-4000-8000-000000000201','thriller'),
 ('c73e1404-0000-4000-8000-000000000202','animation'),
 ('c73e1404-0000-4000-8000-000000000202','fantasy'),
 ('c73e1404-0000-4000-8000-000000000203','comedy'),
 ('c73e1404-0000-4000-8000-000000000203','drama'),
 ('c73e1404-0000-4000-8000-000000000204','science-fiction'),
 ('c73e1404-0000-4000-8000-000000000204','thriller'),
 ('c73e1404-0000-4000-8000-000000000205','science-fiction'),
 ('c73e1404-0000-4000-8000-000000000205','mystery'),
 ('c73e1404-0000-4000-8000-000000000206','thriller'),
 ('c73e1404-0000-4000-8000-000000000206','drama')
ON CONFLICT DO NOTHING;

INSERT INTO title_localizations(title_id,language_code,display_title,title_kind) VALUES
 ('c73e1404-0000-4000-8000-000000000201','en','Parasite','official'),
 ('c73e1404-0000-4000-8000-000000000202','en','Spirited Away','official'),
 ('c73e1404-0000-4000-8000-000000000203','en','The Intouchables','official'),
 ('c73e1404-0000-4000-8000-000000000206','en','Squid Game','official')
ON CONFLICT DO NOTHING;

INSERT INTO external_ids(title_id,source_key,external_id,source_record_id) VALUES
 ('c73e1404-0000-4000-8000-000000000201','kofic','20183782','c73e1404-0000-4000-8000-000000002011'),
 ('c73e1404-0000-4000-8000-000000000205','netflix','80100172','c73e1404-0000-4000-8000-000000002052'),
 ('c73e1404-0000-4000-8000-000000000206','netflix','81040344','c73e1404-0000-4000-8000-000000002062')
ON CONFLICT DO NOTHING;

INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id,provider_code) VALUES
 ('c73e1404-0000-4000-8000-000000000201','2019-05-30','original_premiere','KR',true,'c73e1404-0000-4000-8000-000000002011',NULL),
 ('c73e1404-0000-4000-8000-000000000202','2001-07-20','original_premiere','JP',true,'c73e1404-0000-4000-8000-000000002021',NULL),
 ('c73e1404-0000-4000-8000-000000000203','2011-11-02','original_premiere','FR',true,'c73e1404-0000-4000-8000-000000002031',NULL),
 ('c73e1404-0000-4000-8000-000000000204','2010-07-16','original_premiere','US',true,'c73e1404-0000-4000-8000-000000002041',NULL)
ON CONFLICT DO NOTHING;

INSERT INTO series_debuts(title_id,debut_date,provider_code,territory_code,verified,source_record_id) VALUES
 ('c73e1404-0000-4000-8000-000000000205','2017-12-01','netflix',NULL,true,'c73e1404-0000-4000-8000-000000002051'),
 ('c73e1404-0000-4000-8000-000000000206','2021-09-17','netflix',NULL,true,'c73e1404-0000-4000-8000-000000002061')
ON CONFLICT DO NOTHING;

INSERT INTO field_provenance(title_id,field_path,source_record_id,verification_status,reviewed_at) VALUES
 ('c73e1404-0000-4000-8000-000000000201','original_title','c73e1404-0000-4000-8000-000000002011','verified',now()),
 ('c73e1404-0000-4000-8000-000000000201','original_language.ko','c73e1404-0000-4000-8000-000000002011','verified',now()),
 ('c73e1404-0000-4000-8000-000000000201','release.original_premiere','c73e1404-0000-4000-8000-000000002011','verified',now()),
 ('c73e1404-0000-4000-8000-000000000202','original_title','c73e1404-0000-4000-8000-000000002021','verified',now()),
 ('c73e1404-0000-4000-8000-000000000202','original_language.ja','c73e1404-0000-4000-8000-000000002021','verified',now()),
 ('c73e1404-0000-4000-8000-000000000202','release.original_premiere','c73e1404-0000-4000-8000-000000002021','verified',now()),
 ('c73e1404-0000-4000-8000-000000000203','original_title','c73e1404-0000-4000-8000-000000002031','verified',now()),
 ('c73e1404-0000-4000-8000-000000000203','original_language.fr','c73e1404-0000-4000-8000-000000002032','verified',now()),
 ('c73e1404-0000-4000-8000-000000000203','release.original_premiere','c73e1404-0000-4000-8000-000000002031','verified',now()),
 ('c73e1404-0000-4000-8000-000000000204','original_title','c73e1404-0000-4000-8000-000000002041','verified',now()),
 ('c73e1404-0000-4000-8000-000000000204','original_language.en','c73e1404-0000-4000-8000-000000002041','verified',now()),
 ('c73e1404-0000-4000-8000-000000000204','release.original_premiere','c73e1404-0000-4000-8000-000000002041','verified',now()),
 ('c73e1404-0000-4000-8000-000000000205','original_title','c73e1404-0000-4000-8000-000000002051','verified',now()),
 ('c73e1404-0000-4000-8000-000000000205','original_language.de','c73e1404-0000-4000-8000-000000002052','verified',now()),
 ('c73e1404-0000-4000-8000-000000000205','release.series_debut','c73e1404-0000-4000-8000-000000002051','verified',now()),
 ('c73e1404-0000-4000-8000-000000000206','original_title','c73e1404-0000-4000-8000-000000002061','verified',now()),
 ('c73e1404-0000-4000-8000-000000000206','original_language.ko','c73e1404-0000-4000-8000-000000002062','verified',now()),
 ('c73e1404-0000-4000-8000-000000000206','release.series_debut','c73e1404-0000-4000-8000-000000002061','verified',now())
ON CONFLICT DO NOTHING;

DO $validate_international$
BEGIN
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN release_events e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000201'::uuid AND t.original_title='기생충'
    AND t.title_type='movie' AND t.publication_status='published'
    AND t.first_release_year=2019 AND l.language_code='ko'
    AND e.release_date='2019-05-30'::date
    AND e.event_type='original_premiere'
    AND e.territory_code='KR' AND e.provider_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 201'; END IF;
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN release_events e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000202'::uuid AND t.original_title='千と千尋の神隠し'
    AND t.title_type='movie' AND t.publication_status='published'
    AND t.first_release_year=2001 AND l.language_code='ja'
    AND e.release_date='2001-07-20'::date
    AND e.event_type='original_premiere'
    AND e.territory_code='JP' AND e.provider_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 202'; END IF;
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN release_events e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000203'::uuid AND t.original_title='Intouchables'
    AND t.title_type='movie' AND t.publication_status='published'
    AND t.first_release_year=2011 AND l.language_code='fr'
    AND e.release_date='2011-11-02'::date
    AND e.event_type='original_premiere'
    AND e.territory_code='FR' AND e.provider_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 203'; END IF;
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN release_events e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000204'::uuid AND t.original_title='Inception'
    AND t.title_type='movie' AND t.publication_status='published'
    AND t.first_release_year=2010 AND l.language_code='en'
    AND e.release_date='2010-07-16'::date
    AND e.event_type='original_premiere'
    AND e.territory_code='US' AND e.provider_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 204'; END IF;
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN series_debuts e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000205'::uuid AND t.original_title='Dark'
    AND t.title_type='series' AND t.publication_status='published'
    AND t.first_release_year=2017 AND l.language_code='de'
    AND e.debut_date='2017-12-01'::date
    AND e.provider_code='netflix' AND e.territory_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 205'; END IF;
IF NOT EXISTS (
  SELECT 1 FROM titles t
  JOIN title_languages l ON l.title_id=t.id AND l.relation='original'
  JOIN series_debuts e ON e.title_id=t.id AND e.verified=true
  WHERE t.id='c73e1404-0000-4000-8000-000000000206'::uuid AND t.original_title='오징어 게임'
    AND t.title_type='series' AND t.publication_status='published'
    AND t.first_release_year=2021 AND l.language_code='ko'
    AND e.debut_date='2021-09-17'::date
    AND e.provider_code='netflix' AND e.territory_code IS NULL
) THEN RAISE EXCEPTION 'International title/date mismatch: 206'; END IF;
END
$validate_international$;
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000201'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','기생충','displayTitle','Parasite',
    'type','movie','date','2019-05-30','eventKind','original_premiere','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000201'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000202'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','千と千尋の神隠し','displayTitle','Spirited Away',
    'type','movie','date','2001-07-20','eventKind','original_premiere','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000202'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000203'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','Intouchables','displayTitle','The Intouchables',
    'type','movie','date','2011-11-02','eventKind','original_premiere','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000203'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000204'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','Inception','displayTitle','Inception',
    'type','movie','date','2010-07-16','eventKind','original_premiere','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000204'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000205'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','Dark','displayTitle','Dark',
    'type','series','date','2017-12-01','eventKind','series_debut','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000205'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
INSERT INTO catalogue_audit_log(title_id,actor_type,action,changes)
SELECT 'c73e1404-0000-4000-8000-000000000206'::uuid,'curation_script','curated_international_pilot',
  jsonb_build_object('originalTitle','오징어 게임','displayTitle','Squid Game',
    'type','series','date','2021-09-17','eventKind','series_debut','sourcePolicy','manual-source-reviewed')
WHERE NOT EXISTS (
  SELECT 1 FROM catalogue_audit_log WHERE title_id='c73e1404-0000-4000-8000-000000000206'::uuid
    AND actor_type='curation_script' AND action='curated_international_pilot'
);
COMMIT;
