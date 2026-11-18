-- Execute after seed 0001 RRR, 0002 Indian batch, and 0003 international batch
-- each of the curated batches replayed twice. Database is disposable.
DO $verify_international$
DECLARE total integer;
BEGIN
  SELECT count(*) INTO total FROM titles
    WHERE id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>6 THEN RAISE EXCEPTION 'Expected 6 additional international titles, found %',total; END IF;

  SELECT count(*) INTO total FROM titles
    WHERE id::text LIKE 'c73e1404-0000-4000-8000-%' AND title_type='series';
  IF total<>2 THEN RAISE EXCEPTION 'Expected exactly 2 first-series entries, found %',total; END IF;

  SELECT count(*) INTO total FROM titles
    WHERE id::text LIKE 'c73e1404-0000-4000-8000-%' AND title_type='movie';
  IF total<>4 THEN RAISE EXCEPTION 'Expected exactly 4 film entries, found %',total; END IF;

  SELECT count(DISTINCT language_code) INTO total FROM title_languages
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%' AND relation='original';
  IF total<>5 THEN RAISE EXCEPTION 'Expected 5 international original languages, found %',total; END IF;

  SELECT count(*) INTO total FROM title_languages
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%' AND relation='original';
  IF total<>6 THEN RAISE EXCEPTION 'Unexpected duplicate/missing original language, found %',total; END IF;

  SELECT count(*) INTO total FROM title_localizations
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%'
      AND language_code='en' AND title_kind='official';
  IF total<>4 THEN RAISE EXCEPTION 'Incorrect searchable English aliases, found %',total; END IF;

  SELECT count(*) INTO total FROM release_events
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>4 THEN RAISE EXCEPTION 'Expected 4 international theatrical releases, found %',total; END IF;

  SELECT count(*) INTO total FROM series_debuts
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>2 THEN RAISE EXCEPTION 'Expected 2 first-season debuts, found %',total; END IF;

  SELECT count(*) INTO total FROM release_events e
    JOIN titles t ON t.id=e.title_id
    WHERE e.title_id::text LIKE 'c73e1404-0000-4000-8000-%'
      AND t.title_type='movie' AND e.event_type='original_premiere'
      AND e.verified=true AND e.provider_code IS NULL;
  IF total<>4 THEN RAISE EXCEPTION 'Film theatrical release classification is incorrect: %',total; END IF;

  SELECT count(*) INTO total FROM series_debuts e
    JOIN titles t ON t.id=e.title_id
    WHERE e.title_id::text LIKE 'c73e1404-0000-4000-8000-%'
      AND t.title_type='series'
      AND e.verified=true AND e.provider_code='netflix' AND e.territory_code IS NULL;
  IF total<>2 THEN RAISE EXCEPTION 'Netflix series debut classification is incorrect: %',total; END IF;

  SELECT count(*) INTO total FROM release_events e JOIN titles t ON t.id=e.title_id
    WHERE t.title_type='series' AND e.event_type='original_premiere';
  IF total<>0 THEN RAISE EXCEPTION 'Series incorrectly mixed into theatrical On This Day calendar: %',total; END IF;

  SELECT count(*) INTO total FROM streaming_offers
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>0 THEN RAISE EXCEPTION 'Historical Netflix launch created a current-streaming claim: %',total; END IF;

  SELECT count(*) INTO total FROM source_records
    WHERE id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>12 THEN RAISE EXCEPTION 'Expected 12 first-party/registry source pointers, found %',total; END IF;

  SELECT count(*) INTO total FROM source_records
    WHERE id::text LIKE 'c73e1404-0000-4000-8000-%'
      AND (retrieved_at IS NOT NULL OR raw_payload IS NOT NULL OR license_code<>'FACT_REFERENCE_ONLY');
  IF total<>0 THEN RAISE EXCEPTION 'Invalid raw-fetch or licensed-work claim in reference rows: %',total; END IF;

  SELECT count(*) INTO total FROM field_provenance
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>18 THEN RAISE EXCEPTION 'Expected 18 release/language/title field provenance rows, found %',total; END IF;

  SELECT count(*) INTO total FROM catalogue_audit_log
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%'
      AND action='curated_international_pilot';
  IF total<>6 THEN RAISE EXCEPTION 'Curation audit is not idempotent: %',total; END IF;

  SELECT count(*) INTO total FROM external_ids
    WHERE title_id::text LIKE 'c73e1404-0000-4000-8000-%';
  IF total<>3 THEN RAISE EXCEPTION 'Incorrect authoritative KOFIC/Netflix external identity count: %',total; END IF;

  SELECT count(*) INTO total FROM titles WHERE publication_status='published';
  IF total<>13 THEN RAISE EXCEPTION 'Expected 13 total source-reviewed pilot titles, found %',total; END IF;

  SELECT count(DISTINCT language_code) INTO total FROM title_languages WHERE relation='original';
  IF total<>10 THEN RAISE EXCEPTION 'Expected 10 original languages after batch 0003, found %',total; END IF;

  SELECT count(*) INTO total FROM titles WHERE original_title='RRR' AND publication_status='published';
  IF total<>1 THEN RAISE EXCEPTION 'RRR original baseline was changed or duplicated'; END IF;
END
$verify_international$;
