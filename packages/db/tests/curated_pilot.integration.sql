-- Validate the curated source-reviewed pilot after running seed 0002 twice.
-- Runs only in disposable PostgreSQL, never touches an existing hosted catalogue.
DO $assert_pilot$
DECLARE
 n integer;
BEGIN
 SELECT count(*) INTO n FROM titles
 WHERE id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND title_type='movie' AND publication_status='published';
 IF n<>6 THEN RAISE EXCEPTION 'Expected six verified multilingual titles, got %',n; END IF;

 SELECT count(DISTINCT language_code) INTO n
 FROM title_languages WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND relation='original';
 IF n<>5 THEN RAISE EXCEPTION 'Expected 5 original languages, got %',n; END IF;

 SELECT count(*) INTO n FROM title_languages
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND relation='original';
 IF n<>6 THEN RAISE EXCEPTION 'Original language duplication: %',n; END IF;

 SELECT count(*) INTO n FROM release_events
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%';
 IF n<>6 THEN RAISE EXCEPTION 'Release event duplication or unexpected event: %',n; END IF;

 SELECT count(*) INTO n FROM release_events
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND event_type='original_premiere'
   AND territory_code='IN' AND verified=true;
 IF n<>6 THEN RAISE EXCEPTION 'Incorrect premiere classification: %',n; END IF;

 SELECT count(*) INTO n FROM field_provenance
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%';
 IF n<>18 THEN RAISE EXCEPTION 'Provenance must be three scoped fields per title: %',n; END IF;

 SELECT count(*) INTO n FROM catalogue_audit_log
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND actor_type='curation_script' AND action='curated_pilot_seed';
 IF n<>6 THEN RAISE EXCEPTION 'Duplicate or missing seeded audit entries: %',n; END IF;

 SELECT count(*) INTO n FROM streaming_offers
 WHERE title_id::text LIKE 'b61d0a11-0000-4000-8000-%';
 IF n<>0 THEN RAISE EXCEPTION 'Unverified live streaming offers inserted: %',n; END IF;

 SELECT count(*) INTO n FROM source_records
 WHERE id::text LIKE 'b61d0a11-0000-4000-8000-%';
 IF n<>14 THEN RAISE EXCEPTION 'Expected 14 producer/certifier/journalistic pointers: %',n; END IF;

 SELECT count(*) INTO n FROM source_records
 WHERE id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND (raw_payload IS NOT NULL OR retrieved_at IS NOT NULL);
 IF n<>0 THEN RAISE EXCEPTION 'Falsely claimed raw fetch for curated references: %',n; END IF;

 SELECT count(*) INTO n FROM release_events r
 JOIN source_records s ON r.source_record_id=s.id
 WHERE r.title_id::text LIKE 'b61d0a11-0000-4000-8000-%'
   AND s.license_code='FACT_REFERENCE_ONLY';
 IF n<>6 THEN RAISE EXCEPTION 'Every premiere requires a source pointer: %',n; END IF;

 SELECT count(*) INTO n FROM titles WHERE original_title='RRR' AND publication_status='published';
 IF n<>1 THEN RAISE EXCEPTION 'Existing RRR disappeared after multilingual seed'; END IF;
END
$assert_pilot$;
