"""Offline historical source merge never claims production dedup."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from combine_india_historical_sources import merge_source_reports, markdown


def report(decade, rows):
    return {"schema_version": "indian-offline-discovery-v1",
            "years": [decade, decade + 9],
            "production_snapshot_available": False,
            "production_import_authorized": False,
            "summary": {"discovered_unique_pages": len(rows)},
            "source": {"source_incomplete": True, "next_category_offset": 10},
            "candidates": rows}


def lead(page, qid, year):
    return {"page_id": page, "wikidata_qid": qid, "title": "Example Film",
            "year": year, "observed_years": [year],
            "observed_languages": ["Telugu"], "language": "Telugu",
            "source_categories": [f"Category:{year} Indian films"],
            "india_category": True}


class HistoricalSourceMergeTests(unittest.TestCase):
    def test_dedupes_by_wikidata_and_marks_year_conflicts(self):
        combined = merge_source_reports([
            report(1980, [lead(100, "Q50", 1989)]),
            report(1990, [lead(120, "Q50", 1990), lead(200, "Q60", 1991)]),
        ])
        s = combined["summary"]
        self.assertEqual(s["input_page_leads"], 3)
        self.assertEqual(s["deduplicated_source_identities"], 2)
        self.assertEqual(s["duplicates_across_reports"], 1)
        self.assertEqual(s["conflicting_observed_years"], 1)
        self.assertFalse(combined["production_snapshot_available"])
        self.assertFalse(combined["production_import_authorized"])
        self.assertIsNone(s["net_new_confirmed_against_production"])
        self.assertEqual(s["production_rows_imported"], 0)
        q50 = next(x for x in combined["candidates"] if x["wikidata_qid"] == "Q50")
        self.assertIsNone(q50["year"])
        self.assertEqual(q50["observed_years"], [1989, 1990])
        self.assertTrue(all(x["classification"] == "unreconciled_needs_production_dedup"
                            for x in combined["candidates"]))
        self.assertIn("NOT CHECKED", markdown(combined))

    def test_rejects_claims_of_production_reconciliation(self):
        with self.assertRaises(ValueError):
            merge_source_reports([{**report(1970, [lead(10, "Q11", 1978)]),
                                   "production_snapshot_available": True}])


if __name__ == "__main__":
    unittest.main()
