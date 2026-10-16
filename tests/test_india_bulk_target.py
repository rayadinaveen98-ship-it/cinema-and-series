"""Shared QID-confirmed 10K target across daily and bulk importers."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from india_bulk_target import growth_progress, max_additional_bulk_rows
from wikidata_bulk_import_sql import reconcile


class SharedTargetTests(unittest.TestCase):
    def test_cohorts_are_qid_confirmed_and_disjoint(self):
        year = [
            {"wikidata_qid": "Q11", "source_category": "Category:2001 Indian films"},
            {"wikidata_qid": "Q12", "source_category": "Category:1980 Indian films"},
            {"wikidata_qid": "Q13", "source_category": "wikidata:P31=film;P495=India;P577=release_year"},
            # A QID in both autopilot and the bulk provenance is only counted once.
            {"wikidata_qid": "Q14", "source_category": "wikidata:P31=film;P495=India;P577=release_year"},
        ]
        state = {"2000s_seed_qids": ["Q11", "Q100"],
                 "attempted_by_autopilot": ["Q12", "Q14", "Q100"]}
        report = growth_progress(year, state)
        self.assertEqual(report["confirmed_pre_autopilot"], 1552)
        self.assertEqual(report["confirmed_2000s_cohort"], 1)
        self.assertEqual(report["confirmed_daily_autopilot"], 2)
        self.assertEqual(report["confirmed_wikidata_bulk_imports"], 1)
        self.assertEqual(report["confirmed_total"], 1556)
        self.assertEqual(report["remaining"], 8444)

    def test_goal_prevents_any_further_bulk_sql_preview(self):
        state = {"2000s_seed_qids": [], "attempted_by_autopilot": []}
        stage_rows = [
            {"wikidata_qid": f"Q{i + 1000}",
             "source_category": "wikidata:P31=film;P495=India;P577=release_year"}
            for i in range(8448)
        ]
        allowed = max_additional_bulk_rows(stage_rows, state, 4000)
        self.assertEqual(allowed["confirmed_total"], 10000)
        self.assertEqual(allowed["bulk_allowed_now"], 0)
        selected, summary = reconcile(
            [{"qid": "Q90000", "title": "Remaining", "year": 2020}],
            [], [], [], max_preview=0)
        self.assertEqual(selected, [])
        self.assertEqual(summary["sql_preview_rows"], 0)

    def test_no_unverified_ids_counted(self):
        report = growth_progress([], {"2000s_seed_qids": ["Q100"],
                                      "attempted_by_autopilot": ["Q200"]})
        self.assertEqual(report["confirmed_total"], 1552)


if __name__ == "__main__":
    unittest.main()
