"""Guarantee no background catalogue, artwork or P1 production writes during V2."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAUSED = {
    "wikidata-backfill.yml": "backfill",
    "wikidata-refresh.yml": "refresh",
    "series-catalogue.yml": "catalogue",
    "wikipedia-year-catalogue.yml": "catalogue",
    "catalogue-growth-15k.yml": "grow",
    "website-monitor.yml": "monitor",
    "youtube-monitor.yml": "monitor",
    "p1-quota-safe-daily-resume.yml": "plan-and-dispatch",
    "p1-background-write-coordinator.yml": "coordinate",
    "india-catalogue-autopilot.yml": "daily",
    "vrt-indian-poster-batch-02.yml": "publish",
    "artwork-bulk-500.yml": "discover",
    "existing-title-artwork-100-pilot.yml": "review",
    "artwork-fast-70.yml": "pilot",
}


class FoundationFreezeTests(unittest.TestCase):
    def test_freeze_marker_is_explicit_and_active(self):
        marker = json.loads((ROOT / "ops/data-foundation-v2-freeze.json").read_text())
        self.assertEqual(marker["schema"], "data-foundation-v2-freeze-v1")
        self.assertIs(marker["active"], True)
        self.assertTrue(marker["review_required_before_unfreeze"])

    def test_all_mutating_and_legacy_manual_pipelines_are_paused(self):
        for filename, job in PAUSED.items():
            with self.subTest(filename=filename):
                content = (ROOT / ".github/workflows" / filename).read_text()
                snippet = "jobs:\n  " + job + ":\n"
                self.assertIn(snippet, content)
                first = content.split(snippet, 1)[1].split("\n", 7)
                self.assertIn("    if: ${{ false }}", first)

    def test_data_quality_audit_remains_read_only(self):
        workflow = (ROOT / ".github/workflows/catalogue-quality-v1.yml").read_text()
        self.assertIn("production_catalogue_quality.py", workflow)
        self.assertIn("ops/data-foundation-v2-freeze.json", workflow)
        self.assertNotIn("wrangler d1 migrations apply", workflow)
        self.assertNotIn("wrangler d1 execute cinema-and-series --remote --file=", workflow)


if __name__ == "__main__":
    unittest.main()
