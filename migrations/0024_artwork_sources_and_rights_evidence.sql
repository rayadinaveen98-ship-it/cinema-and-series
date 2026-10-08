-- P2.3 source registry + rights evidence.
-- Registry only. No artwork discovery, ingestion, approval, or publication occurs.

CREATE TABLE IF NOT EXISTS artwork_sources (
  source_key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  source_kind TEXT NOT NULL CHECK (
    source_kind IN ('OPEN_LICENSE_REPOSITORY','PUBLIC_DOMAIN_REPOSITORY','PROVIDER_LICENSED','RIGHTSHOLDER_DIRECT')
  ),
  canonical_base_url TEXT NOT NULL,
  adapter_key TEXT NOT NULL,
  rights_policy_url TEXT,
  enabled_for_discovery INTEGER NOT NULL DEFAULT 0 CHECK (enabled_for_discovery IN (0,1)),
  enabled_for_publication INTEGER NOT NULL DEFAULT 0 CHECK (enabled_for_publication IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artwork_rights_evidence (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES artwork_assets(id),
  source_key TEXT NOT NULL REFERENCES artwork_sources(source_key),
  evidence_kind TEXT NOT NULL CHECK (
    evidence_kind IN ('LICENSE_PAGE','PUBLIC_DOMAIN_RECORD','PROVIDER_AGREEMENT','RIGHTSHOLDER_PERMISSION','PROMOTIONAL_PERMISSION')
  ),
  evidence_url TEXT NOT NULL,
  evidence_sha256 TEXT,
  captured_at TEXT NOT NULL,
  verified_at TEXT,
  verified_by TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_artwork_rights_asset ON artwork_rights_evidence(asset_id);
CREATE INDEX IF NOT EXISTS idx_artwork_rights_source ON artwork_rights_evidence(source_key, evidence_kind);

-- Seed only source policy metadata. Discovery/publication stay disabled until each source
-- passes legal/operational review and a bounded population gate.
INSERT OR IGNORE INTO artwork_sources
(source_key, display_name, source_kind, canonical_base_url, adapter_key, rights_policy_url, enabled_for_discovery, enabled_for_publication)
VALUES
('wikimedia_commons', 'Wikimedia Commons', 'OPEN_LICENSE_REPOSITORY', 'https://commons.wikimedia.org/', 'wikimedia_commons_v1', 'https://commons.wikimedia.org/wiki/Commons:Licensing', 0, 0),
('internet_archive', 'Internet Archive', 'PUBLIC_DOMAIN_REPOSITORY', 'https://archive.org/', 'internet_archive_v1', 'https://archive.org/about/terms.php', 0, 0),
('rightsholder_direct', 'Rightsholder Direct', 'RIGHTSHOLDER_DIRECT', 'https://example.invalid/', 'rightsholder_direct_v1', NULL, 0, 0);

CREATE TABLE IF NOT EXISTS artwork_source_review (
  source_key TEXT PRIMARY KEY REFERENCES artwork_sources(source_key),
  review_status TEXT NOT NULL CHECK (review_status IN ('UNREVIEWED','APPROVED','REJECTED','PAUSED')),
  reviewed_at TEXT,
  reviewed_by TEXT,
  review_reference TEXT,
  notes TEXT
);

INSERT OR IGNORE INTO artwork_source_review(source_key, review_status)
SELECT source_key, 'UNREVIEWED' FROM artwork_sources;
