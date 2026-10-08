-- P2.1 shared Movie + Series artwork foundation.
-- This migration creates the canonical artwork/evidence model only.
-- It intentionally does not ingest, approve, or publish any artwork.

CREATE TABLE IF NOT EXISTS artwork_assets (
  id TEXT PRIMARY KEY,
  asset_type TEXT NOT NULL CHECK (asset_type IN ('poster','backdrop','logo','thumbnail','still')),
  source_key TEXT NOT NULL,
  source_asset_id TEXT,
  source_page_url TEXT,
  delivery_url TEXT,
  language_code TEXT NOT NULL DEFAULT '',
  territory_code TEXT NOT NULL DEFAULT '',
  publication_state TEXT NOT NULL CHECK (
    publication_state IN (
      'DISCOVERED','PENDING_REVIEW','OPEN_LICENSE_VERIFIED','PUBLIC_DOMAIN_VERIFIED',
      'PROVIDER_LICENSED','RIGHTS_APPROVED','PROMOTIONAL_PERMISSION_VERIFIED',
      'REJECTED','EXPIRED','TAKEDOWN_PENDING','TAKEN_DOWN'
    )
  ),
  rights_basis TEXT NOT NULL CHECK (
    rights_basis IN (
      'OPEN_LICENSE','PUBLIC_DOMAIN','PROVIDER_CONTRACT','RIGHTSHOLDER_PERMISSION',
      'PROMOTIONAL_PERMISSION','PLATFORM_EMBED_AUTHORIZATION','NO_RIGHTS_BASIS'
    )
  ),
  hosting_mode TEXT NOT NULL CHECK (
    hosting_mode IN ('SELF_HOSTED','PROVIDER_CDN','EXTERNAL_ALLOWED','REFERENCE_ONLY','EMBED_ONLY')
  ),
  attribution_required INTEGER NOT NULL DEFAULT 0 CHECK (attribution_required IN (0,1)),
  attribution_text TEXT,
  creator_text TEXT,
  rights_reference TEXT,
  rights_verified_at TEXT,
  rights_verified_by TEXT,
  valid_from TEXT,
  valid_until TEXT,
  takedown_status TEXT NOT NULL DEFAULT 'clear' CHECK (takedown_status IN ('clear','pending','taken_down')),
  width INTEGER CHECK (width IS NULL OR width > 0),
  height INTEGER CHECK (height IS NULL OR height > 0),
  aspect_ratio REAL CHECK (aspect_ratio IS NULL OR aspect_ratio > 0),
  quality_score REAL CHECK (quality_score IS NULL OR quality_score >= 0),
  checksum_sha256 TEXT,
  source_asset_version TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CHECK (source_asset_id IS NOT NULL OR source_page_url IS NOT NULL),
  CHECK (attribution_required = 0 OR length(trim(COALESCE(attribution_text, ''))) > 0),
  CHECK (valid_from IS NULL OR valid_until IS NULL OR valid_until > valid_from),
  CHECK (
    publication_state NOT IN (
      'OPEN_LICENSE_VERIFIED','PUBLIC_DOMAIN_VERIFIED','PROVIDER_LICENSED',
      'RIGHTS_APPROVED','PROMOTIONAL_PERMISSION_VERIFIED'
    )
    OR rights_verified_at IS NOT NULL
  ),
  CHECK (publication_state <> 'OPEN_LICENSE_VERIFIED' OR rights_basis = 'OPEN_LICENSE'),
  CHECK (publication_state <> 'PUBLIC_DOMAIN_VERIFIED' OR rights_basis = 'PUBLIC_DOMAIN'),
  CHECK (publication_state <> 'PROVIDER_LICENSED' OR rights_basis = 'PROVIDER_CONTRACT'),
  CHECK (publication_state <> 'RIGHTS_APPROVED' OR rights_basis = 'RIGHTSHOLDER_PERMISSION'),
  CHECK (publication_state <> 'PROMOTIONAL_PERMISSION_VERIFIED' OR rights_basis = 'PROMOTIONAL_PERMISSION')
);

CREATE TABLE IF NOT EXISTS title_artwork_links (
  id TEXT PRIMARY KEY,
  media_type TEXT NOT NULL CHECK (media_type IN ('movie','series')),
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  asset_id TEXT NOT NULL REFERENCES artwork_assets(id),
  presentation_role TEXT NOT NULL CHECK (presentation_role IN ('poster','backdrop')),
  language_code TEXT NOT NULL DEFAULT '',
  territory_code TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (media_type, source_table, source_id, asset_id, presentation_role, language_code, territory_code)
);

CREATE INDEX IF NOT EXISTS idx_artwork_assets_source ON artwork_assets(source_key, source_asset_id);
CREATE INDEX IF NOT EXISTS idx_artwork_assets_publicity ON artwork_assets(publication_state, rights_basis, hosting_mode, takedown_status);
CREATE INDEX IF NOT EXISTS idx_artwork_assets_locale ON artwork_assets(language_code, territory_code);
CREATE INDEX IF NOT EXISTS idx_title_artwork_links_title ON title_artwork_links(media_type, source_table, source_id, presentation_role);
CREATE INDEX IF NOT EXISTS idx_title_artwork_links_asset ON title_artwork_links(asset_id);

-- Existing movie artwork columns remain compatibility aliases/cache during P2.
-- They are not the canonical artwork model and are not populated by this migration.
