ALTER TABLE source_observations
ADD COLUMN evidence_contexts_json TEXT NOT NULL DEFAULT '[]';
