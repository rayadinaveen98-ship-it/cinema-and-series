CREATE TABLE IF NOT EXISTS source_channels (
  source_key TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  website_url TEXT,
  youtube_channel_id TEXT,
  youtube_handle TEXT,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  last_checked_at TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_channels_active ON source_channels(active, source_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_source_channels_youtube_id
  ON source_channels(youtube_channel_id)
  WHERE youtube_channel_id IS NOT NULL;
