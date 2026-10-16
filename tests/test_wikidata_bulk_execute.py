"""Unit tests for scheduled Wikidata bulk D1 import guard."""
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from wikidata_bulk_execute import apply_batch_files
from india_daily_autopilot import D1QuotaReached


class BulkApplyTests(unittest.TestCase):
    def test_dry_run_does_not_read_or_write_d1(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("wikidata_bulk_execute.d1_execute") as d1:
                report = apply_batch_files(
                    [{"qid": "Q123", "year": 2020, "title": "A"}], Path(tmp),
                    apply=False,
                )
            self.assertEqual(report["status"], "dry_run_no_d1")
            d1.assert_not_called()

    def test_refuse_duplicate_staged_qid(self):
        with self.assertRaises(ValueError):
            apply_batch_files([{"qid": "Q123"}, {"qid": "Q123"}], Path("."))

    def test_apply_verifies_after_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)/"wikidata-00000.sql"
            f.write_text(
                "-- PREVIEW ONLY\nINSERT OR IGNORE INTO catalogue_titles SELECT 1;\n"
                "INSERT OR IGNORE INTO catalogue_titles SELECT 2;\n",
                encoding="utf-8",
            )
            with (patch("wikidata_bulk_execute.d1_execute", return_value=("", 50)) as d1,
                  patch("wikidata_bulk_execute.qids_present_in_year_table",
                        return_value={"Q123", "Q124"}) as verify):
                report = apply_batch_files([{"qid": "Q123"}, {"qid": "Q124"}],
                                           Path(tmp), apply=True)
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["verified_present_qids"], 2)
            self.assertEqual(report["rows_read_reported"], 50)
            self.assertEqual(d1.call_count, 1)
            self.assertEqual(verify.call_count, 1)

    def test_apply_stops_at_quota_without_repeating_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)/"wikidata-00000.sql"
            f.write_text("INSERT OR IGNORE INTO catalogue_titles SELECT 1;\n")
            with patch("wikidata_bulk_execute.d1_execute",
                       side_effect=D1QuotaReached("code 7500")) as d1:
                report = apply_batch_files([{"qid": "Q123"}], Path(tmp), apply=True)
            self.assertEqual(report["status"], "cloudflare_quota_paused")
            self.assertEqual(d1.call_count, 1)
            self.assertEqual(report["verified_present_qids"], 0)


if __name__ == "__main__":
    unittest.main()
