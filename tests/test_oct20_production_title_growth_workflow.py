"""Guardrails for explicitly authorized net-new Indian title import."""
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / ".github/workflows/oct20-production-title-growth.yml"


class Oct20ProductionGrowthContract(unittest.TestCase):
    def test_one_day_only_and_reuses_deduped_source_stage(self):
        s = PATH.read_text(encoding="utf-8")
        self.assertIn('== "2026-10-20"', s)
        self.assertIn('echo "allowed=false"', s)
        self.assertIn("steps.date.outputs.allowed == 'true'", s)
        self.assertIn("group: india-catalogue-autopilot", s)
        self.assertIn("automation/wikidata-bulk-stage", s)
        self.assertIn("scripts/wikidata_bulk_import_sql.py", s)
        self.assertIn("scripts/wikidata_bulk_execute.py", s)
        self.assertIn("--max-preview 10000", s)
        self.assertIn("--max-row-reads 1500000 --apply", s)
        self.assertIn('"date":"2026-10-20"', s)
        self.assertIn('source_only_candidates_count_as_additions', s)

    def test_explicitly_imports_unconfirmed_film_years_only(self):
        s = PATH.read_text(encoding="utf-8")
        self.assertIn('unconfirmed_release_dates_only', s)
        self.assertIn('full_exact_release_date_claims_added', s)
        self.assertIn('net_new_staged_candidates', s)
        self.assertIn('new_production_movies_added', s)
        self.assertIn('AFTER', s.upper())
        self.assertNotIn("DROP TABLE", s)
        self.assertNotIn("DELETE FROM", s)
        self.assertNotIn("UPDATE catalogue_titles", s)
        self.assertNotIn("tmdb", s.lower())


if __name__ == "__main__":
    unittest.main()
