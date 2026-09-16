-- Remove the one website-monitor observation written before same-source
-- verified-date deduplication was introduced. Both dates on this Dharma
-- homepage observation are already curated in data/official/releases.json.
DELETE FROM source_observations
WHERE source_key = 'dharma_productions'
  AND external_id = 'web-8fdee458c3015804730ce943';
