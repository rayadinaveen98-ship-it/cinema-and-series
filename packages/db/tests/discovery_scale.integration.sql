-- Disposable PostgreSQL 17 ONLY: analytical synthetic catalogue regression.
-- All generated rows are inside one transaction and ROLLBACK at the end.
-- No hosted Neon writes, real film facts, or performance time guarantees.
BEGIN;
SET LOCAL statement_timeout='30s';

INSERT INTO source_records(id,source_key,external_record_id,source_url,license_code,retrieved_at)
VALUES ('fa000002-0000-4000-8000-000000000001','synthetic','performance-only',
        'https://example.org/synthetic-perf','TEST_ONLY',NULL);

INSERT INTO titles(id,title_type,original_title,publication_status,first_release_year)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       CASE WHEN gs%5=0 THEN 'series' ELSE 'movie' END,
       'Synthetic Load Title '||gs,'published',2000+(gs%25)
FROM generate_series(1,10000) gs;

INSERT INTO title_languages(title_id,language_code,relation)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       CASE gs%3 WHEN 0 THEN 'en' WHEN 1 THEN 'ko' ELSE 'te' END,'original'
FROM generate_series(1,10000) gs;

INSERT INTO title_genres(title_id,genre_code)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       CASE WHEN gs%2=0 THEN 'thriller' ELSE 'drama' END
FROM generate_series(1,10000) gs;

INSERT INTO title_localizations(title_id,language_code,display_title,title_kind)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       'en','Synthetic Alias '||gs,'alternative'
FROM generate_series(5,10000,5) gs;

INSERT INTO release_events(title_id,release_date,event_type,territory_code,verified,source_record_id)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       date '2005-01-01'+(gs%7000),'original_premiere','US',true,
       'fa000002-0000-4000-8000-000000000001'::uuid
FROM generate_series(1,10000) gs WHERE gs%5<>0;

INSERT INTO series_debuts(title_id,debut_date,provider_code,territory_code,verified,source_record_id)
SELECT ('fa000001-0000-4000-8000-' || lpad(gs::text,12,'0'))::uuid,
       date '2005-01-01'+(gs%7000),'netflix',NULL,true,
       'fa000002-0000-4000-8000-000000000001'::uuid
FROM generate_series(1,10000) gs WHERE gs%5=0;

ANALYZE titles;
ANALYZE title_languages;
ANALYZE title_genres;
ANALYZE title_localizations;
ANALYZE release_events;
ANALYZE series_debuts;

DO $assert_synthetic$
DECLARE n integer;
BEGIN
 SELECT count(*) INTO n FROM titles WHERE publication_status='published';
 IF n<>10013 THEN RAISE EXCEPTION 'Expected 10013 published titles, got %',n; END IF;
 SELECT count(*) INTO n FROM titles WHERE publication_status='published' AND title_type='series';
 IF n<>2002 THEN RAISE EXCEPTION 'Expected 2002 series, got %',n; END IF;
 SELECT count(*) INTO n FROM release_events WHERE title_id::text LIKE 'fa000001-0000-4000-8000-%';
 IF n<>8000 THEN RAISE EXCEPTION 'Expected 8000 synthetic film premieres, got %',n; END IF;
 SELECT count(*) INTO n FROM series_debuts WHERE title_id::text LIKE 'fa000001-0000-4000-8000-%';
 IF n<>2000 THEN RAISE EXCEPTION 'Expected 2000 synthetic series debuts, got %',n; END IF;
 SELECT count(*) INTO n FROM title_localizations
 WHERE display_title ILIKE '%Synthetic Alias 10000%';
 IF n<>1 THEN RAISE EXCEPTION 'Alias search mismatch, got %',n; END IF;
 SELECT count(*) INTO n FROM titles t
 WHERE t.publication_status='published' AND
   (t.original_title ILIKE '%Synthetic Load Title 9999%'
    OR EXISTS (SELECT 1 FROM title_localizations l
               WHERE l.title_id=t.id AND l.display_title ILIKE '%Synthetic Load Title 9999%'));
 IF n<>1 THEN RAISE EXCEPTION 'Canonical search mismatch, got %',n; END IF;
 SELECT count(*) INTO n FROM release_events r JOIN titles t ON t.id=r.title_id
 WHERE r.event_type='original_premiere' AND t.title_type='series';
 IF n<>0 THEN RAISE EXCEPTION 'Series leaked into film original premieres, got %',n; END IF;
 SELECT count(*) INTO n FROM streaming_offers WHERE title_id::text LIKE 'fa000001-0000-4000-8000-%';
 IF n<>0 THEN RAISE EXCEPTION 'Synthetic release created a streaming-offer claim: %',n; END IF;
 SELECT count(*) INTO n FROM (
   SELECT id FROM titles WHERE publication_status='published' ORDER BY id LIMIT 51
 ) page;
 IF n<>51 THEN RAISE EXCEPTION 'Unexpected first-page row count, got %',n; END IF;
 SELECT count(*) INTO n FROM (
   SELECT t.id,
     (CASE WHEN EXISTS(
       SELECT 1 FROM title_languages l
       WHERE l.title_id=t.id AND l.relation='original' AND l.language_code='ko'
     ) THEN 5 ELSE 0 END)
     + (SELECT COUNT(*)::integer*3 FROM title_genres g
         WHERE g.title_id=t.id AND g.genre_code IN ('thriller','drama')) AS score
   FROM titles t WHERE t.publication_status='published'
   AND (EXISTS(
      SELECT 1 FROM title_languages l
      WHERE l.title_id=t.id AND l.relation='original' AND l.language_code='ko'
   ) OR EXISTS(
      SELECT 1 FROM title_genres g WHERE g.title_id=t.id
       AND g.genre_code IN ('thriller','drama')
   ))
   ORDER BY score DESC,t.id LIMIT 20
 ) ranked;
 IF n<>20 THEN RAISE EXCEPTION 'Ranking query returned an unexpected count: %',n; END IF;
END
$assert_synthetic$;

\echo '[PERF] 10,000 synthetic titles + 13 curated titles. These are SQL execution profiles, not API/Android latency budgets.'
\echo '[PERF] Browse original-language filter'
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON)
SELECT t.id,t.original_title FROM titles t
WHERE t.publication_status='published'
 AND EXISTS(SELECT 1 FROM title_languages l WHERE l.title_id=t.id
             AND l.relation='original' AND l.language_code='ko')
ORDER BY t.id LIMIT 51;

\echo '[PERF] Search canonical and English alias'
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON)
SELECT t.id,t.original_title FROM titles t WHERE t.publication_status='published'
 AND (t.original_title ILIKE '%Synthetic Alias 10000%'
   OR EXISTS(SELECT 1 FROM title_localizations l WHERE l.title_id=t.id
             AND l.display_title ILIKE '%Synthetic Alias 10000%'))
ORDER BY CASE WHEN lower(t.original_title)=lower('Synthetic Alias 10000') THEN 0 ELSE 1 END,
         t.original_title,t.id LIMIT 30;

\echo '[PERF] Film-only historical original premiere lookup'
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON)
SELECT t.id,t.original_title,r.release_date
FROM release_events r JOIN titles t ON t.id=r.title_id
WHERE t.publication_status='published' AND t.title_type='movie'
 AND r.event_type='original_premiere' AND r.verified=true
 AND r.release_date<'2026-01-01'
 AND EXTRACT(MONTH FROM r.release_date)=3 AND EXTRACT(DAY FROM r.release_date)=25
ORDER BY r.release_date DESC,t.id LIMIT 30;

\echo '[PERF] Guest recommendations source-side scoring'
EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, SUMMARY ON)
SELECT t.id,t.original_title,
 ((CASE WHEN EXISTS(SELECT 1 FROM title_languages l WHERE l.title_id=t.id
    AND l.relation='original' AND l.language_code='ko') THEN 5 ELSE 0 END)
  + (SELECT COUNT(*)::integer*3 FROM title_genres g WHERE g.title_id=t.id
     AND g.genre_code IN ('thriller','drama'))) AS score
FROM titles t
WHERE t.publication_status='published' AND
 (EXISTS(SELECT 1 FROM title_languages l WHERE l.title_id=t.id
    AND l.relation='original' AND l.language_code='ko')
 OR EXISTS(SELECT 1 FROM title_genres g WHERE g.title_id=t.id
    AND g.genre_code IN ('thriller','drama')))
ORDER BY score DESC,t.id LIMIT 20;

ROLLBACK;
