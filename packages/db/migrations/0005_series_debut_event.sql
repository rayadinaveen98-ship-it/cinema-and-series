-- 0005: additive storage for the first publicly available TV season launch.
-- Keep the original theatrical and regional film release_events check unchanged.
-- No existing titles, releases, foreign keys or constraints are removed.
BEGIN;
CREATE TABLE series_debuts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title_id uuid NOT NULL REFERENCES titles(id) ON DELETE CASCADE,
  debut_date date NOT NULL,
  provider_code text REFERENCES providers(code),
  territory_code char(2) REFERENCES countries(code),
  verified boolean NOT NULL DEFAULT false,
  source_record_id uuid NOT NULL REFERENCES source_records(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE NULLS NOT DISTINCT (title_id,debut_date,provider_code,territory_code,source_record_id)
);
CREATE INDEX series_debuts_title_date_idx ON series_debuts(title_id,debut_date);
COMMIT;
