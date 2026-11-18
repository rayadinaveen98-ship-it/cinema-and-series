-- Foundation DDL. UNTESTED against hosted PostgreSQL; never apply to a live database without disposable integration certification.
-- PostgreSQL 15+; pg_trgm is used for optional fuzzy title indexes.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE titles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_type text NOT NULL CHECK (title_type IN ('movie','series')),
  original_title text NOT NULL CHECK (length(btrim(original_title)) BETWEEN 1 AND 300),
  publication_status text NOT NULL DEFAULT 'staged' CHECK (publication_status IN ('staged','published','withdrawn')),
  first_release_year integer CHECK (first_release_year BETWEEN 1800 AND 2100),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE languages (
  code text PRIMARY KEY CHECK (code ~ '^[a-z]{2,3}(-[a-z0-9]{2,8})*$'),
  name text NOT NULL
);

CREATE TABLE title_languages (
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  language_code text NOT NULL REFERENCES languages(code),
  relation text NOT NULL CHECK (relation IN ('original','audio_verified')),
  PRIMARY KEY (title_id, language_code, relation)
);

CREATE TABLE title_localizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  language_code text REFERENCES languages(code),
  display_title text NOT NULL CHECK (length(btrim(display_title)) BETWEEN 1 AND 300),
  title_kind text NOT NULL CHECK (title_kind IN ('original','official','alternative','transliterated')),
  UNIQUE NULLS NOT DISTINCT (title_id, language_code, display_title, title_kind)
);

CREATE TABLE genres (
  code text PRIMARY KEY CHECK (code ~ '^[a-z][a-z0-9-]{1,39}$'),
  display_name text NOT NULL
);

CREATE TABLE title_genres (
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  genre_code text NOT NULL REFERENCES genres(code),
  PRIMARY KEY (title_id,genre_code)
);

CREATE TABLE countries (
  code char(2) PRIMARY KEY CHECK (code ~ '^[A-Z]{2}$'),
  display_name text NOT NULL
);

CREATE TABLE title_countries (
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  country_code char(2) NOT NULL REFERENCES countries(code),
  PRIMARY KEY (title_id,country_code)
);

CREATE TABLE source_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_key text NOT NULL,
  external_record_id text NOT NULL,
  source_url text NOT NULL CHECK (source_url LIKE 'https://%'),
  license_code text NOT NULL,
  raw_payload jsonb,
  retrieved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_key,external_record_id)
);

CREATE TABLE external_ids (
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  source_key text NOT NULL,
  external_id text NOT NULL,
  source_record_id uuid REFERENCES source_records(id),
  PRIMARY KEY (source_key,external_id)
);

CREATE TABLE release_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  release_date date NOT NULL,
  event_type text NOT NULL CHECK (event_type IN ('original_premiere','territory_theatrical','ott_premiere','rerelease')),
  territory_code char(2) REFERENCES countries(code),
  verified boolean NOT NULL DEFAULT false,
  source_record_id uuid NOT NULL REFERENCES source_records(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE NULLS NOT DISTINCT (title_id,release_date,event_type,territory_code,source_record_id)
);

CREATE TABLE providers (
  code text PRIMARY KEY,
  display_name text NOT NULL
);

CREATE TABLE streaming_offers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  provider_code text NOT NULL REFERENCES providers(code),
  territory_code char(2) NOT NULL REFERENCES countries(code),
  audio_language_code text REFERENCES languages(code),
  verification_status text NOT NULL DEFAULT 'unverified' CHECK (verification_status IN ('verified','unverified','rejected')),
  verified_at timestamptz,
  valid_until timestamptz,
  source_record_id uuid NOT NULL REFERENCES source_records(id),
  CHECK (valid_until IS NULL OR verified_at IS NULL OR valid_until >= verified_at)
);

CREATE TABLE field_provenance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  field_path text NOT NULL,
  source_record_id uuid NOT NULL REFERENCES source_records(id),
  verification_status text NOT NULL DEFAULT 'unverified' CHECK (verification_status IN ('verified','unverified','rejected')),
  reviewed_at timestamptz,
  UNIQUE (title_id,field_path,source_record_id)
);

CREATE TABLE ingestion_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_key text NOT NULL,
  run_status text NOT NULL CHECK (run_status IN ('running','completed','failed','cancelled')),
  checkpoint text,
  processed_count bigint NOT NULL DEFAULT 0,
  rejected_count bigint NOT NULL DEFAULT 0,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE staging_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_run_id uuid NOT NULL REFERENCES ingestion_runs(id),
  source_record_id uuid REFERENCES source_records(id),
  raw_candidate jsonb NOT NULL,
  review_status text NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending','validated','rejected','published')),
  issue_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  UNIQUE (ingestion_run_id,source_record_id)
);

CREATE TABLE review_queue (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  staging_record_id uuid NOT NULL REFERENCES staging_records(id),
  reason_code text NOT NULL,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','rejected')),
  reviewer_note text,
  created_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz
);

CREATE TABLE catalogue_audit_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid REFERENCES titles(id),
  actor_type text NOT NULL,
  action text NOT NULL,
  changes jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Primary query paths: language/genres, aliases/search, original release calendar, and verified OTT.
CREATE INDEX titles_public_type_idx ON titles (title_type,id) WHERE publication_status='published';
CREATE INDEX titles_original_trgm_idx ON titles USING gin (lower(original_title) gin_trgm_ops);
CREATE INDEX localizations_title_trgm_idx ON title_localizations USING gin (lower(display_title) gin_trgm_ops);
CREATE INDEX localizations_title_id_idx ON title_localizations (title_id);
CREATE INDEX title_languages_language_idx ON title_languages (language_code,title_id);
CREATE INDEX title_genres_genre_idx ON title_genres (genre_code,title_id);
CREATE INDEX release_event_title_idx ON release_events (title_id,release_date);
CREATE INDEX release_event_day_idx ON release_events
  ((extract(month from release_date)),(extract(day from release_date)))
  WHERE event_type='original_premiere' AND verified=true;
CREATE INDEX offers_territory_provider_idx ON streaming_offers (territory_code,provider_code,title_id);
CREATE INDEX staging_review_idx ON staging_records (review_status,ingestion_run_id);
CREATE INDEX reviews_open_idx ON review_queue (created_at) WHERE status='open';
COMMIT;
