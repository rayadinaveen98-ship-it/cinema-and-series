import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/0024_artwork_sources_and_rights_evidence.sql"

class P2ArtworkSourceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8")

    def test_registry_is_fail_closed_by_default(self):
        self.assertIn("enabled_for_discovery INTEGER NOT NULL DEFAULT 0", self.sql)
        self.assertIn("enabled_for_publication INTEGER NOT NULL DEFAULT 0", self.sql)
        self.assertIn("'UNREVIEWED'", self.sql)

    def test_rights_evidence_is_asset_bound(self):
        self.assertIn("asset_id TEXT NOT NULL REFERENCES artwork_assets(id)", self.sql)
        self.assertIn("evidence_url TEXT NOT NULL", self.sql)
        self.assertIn("evidence_kind TEXT NOT NULL CHECK", self.sql)

    def test_only_real_source_endpoints_are_seeded(self):
        self.assertIn("https://commons.wikimedia.org/", self.sql)
        self.assertIn("https://archive.org/", self.sql)
        self.assertNotIn("example.invalid", self.sql)

if __name__ == "__main__":
    unittest.main()
