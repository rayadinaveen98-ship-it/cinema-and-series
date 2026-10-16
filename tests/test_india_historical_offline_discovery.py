"""Offline Indian movie discovery never mislabels raw leads as net-new films."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from discover_india_historical_offline import build_report, markdown


class OfflineDiscoveryTests(unittest.TestCase):
    def test_labels_all_candidates_as_unreconciled_without_db_access(self):
        rows = [
            {"page_id": 9, "title": "Film A", "wikidata_qid": "Q9",
             "language": "Telugu", "india_category": True},
            {"page_id": 10, "title": "Film B", "wikidata_qid": None,
             "language": "Hindi", "india_category": False},
        ]
        source = {"categories_failed": 0, "source_incomplete": True,
                  "next_category_offset": 20}
        report = build_report(rows, source, 1990, 1999)
        self.assertFalse(report["production_snapshot_available"])
        self.assertFalse(report["production_import_authorized"])
        self.assertIsNone(report["summary"]["verified_net_new_movies"])
        self.assertEqual(report["summary"]["imported_movies"], 0)
        self.assertEqual(report["summary"]["india_category_leads"], 1)
        self.assertTrue(all(
            x["classification"] == "unreconciled_needs_production_dedup"
            for x in report["candidates"]
        ))
        self.assertIn("not an import or a net-new count", markdown(report))
        self.assertIn("ZERO", markdown(report))


if __name__ == "__main__":
    unittest.main()
