"""Historical source reconciliation must not import or miscount existing QIDs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reconcile_india_historical_manifest import reconcile


def item(page, qid, year):
    return {"page_id": page, "wikidata_qid": qid,
            "title": f"Film {page}", "year": year,
            "observed_years": [year], "language": "Telugu",
            "observed_languages": ["Telugu"],
            "india_category": True,
            "source_categories": [f"Category:{year} Indian films"],
            "classification": "unreconciled_needs_production_dedup"}


class ReconcileHistoricalTests(unittest.TestCase):
    def test_production_identity_is_deduped_and_sql_is_preview_only(self):
        manifest = {
            "schema_version": "indian-historical-source-merge-v1",
            "production_snapshot_available": False,
            "production_import_authorized": False,
            "candidates": [item(10, "Q10", 1980), item(11, "Q11", 1981)],
        }
        report, plan, statements = reconcile(
            manifest, [],
            [{"id": "wd-Q10", "wikidata_qid": "Q10", "wikipedia_page_id": 10,
              "title": "Film 10", "release_year": 1980}], 100,
        )
        self.assertEqual(report["summary"]["already_in_production"], 1)
        self.assertEqual(report["summary"]["total_net_new_discovery_candidates"], 1)
        self.assertEqual(len(plan["selected"]), 1)
        self.assertEqual(plan["selected"][0]["wikidata_qid"], "Q11")
        self.assertEqual(len(statements), 1)
        self.assertIn("INSERT OR IGNORE", statements[0])
        self.assertIn("NOT EXISTS", statements[0])

    def test_unrecognized_manifest_refused(self):
        with self.assertRaises(ValueError):
            reconcile({"schema_version": "unknown"}, [], [])


if __name__ == "__main__":
    unittest.main()
