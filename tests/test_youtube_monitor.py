import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "youtube_monitor.py"
spec = importlib.util.spec_from_file_location("youtube_monitor", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class YouTubeMonitorTests(unittest.TestCase):
    def test_extracts_day_month_year_near_release_context(self):
        text = "Jailer 2 releases worldwide on 15 October 2026."
        self.assertEqual(module.extract_release_dates(text), ["2026-10-15"])

    def test_extracts_month_day_year_near_cinema_context(self):
        text = "In cinemas October 15, 2026. Official announcement."
        self.assertEqual(module.extract_release_dates(text), ["2026-10-15"])

    def test_extracts_numeric_date_with_release_context(self):
        text = "Worldwide release 11/06/2027"
        self.assertEqual(module.extract_release_dates(text), ["2027-06-11"])

    def test_rejects_unrelated_date(self):
        text = "Our channel started on October 15, 2026. Subscribe now."
        self.assertEqual(module.extract_release_dates(text), [])

    def test_multiple_dates_are_not_collapsed_to_single_candidate(self):
        dates = module.extract_release_dates("Releasing 15 October 2026. In cinemas 22 October 2026 overseas.")
        self.assertEqual(dates, ["2026-10-15", "2026-10-22"])

    def test_sql_keeps_candidates_pending_review(self):
        sql = module.build_sql([
            {
                "source_key": "sun_pictures",
                "video_id": "abc123",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "video_title": "Jailer 2 release date",
                "published_at": "2026-09-16T00:00:00Z",
                "candidate_dates": ["2026-10-15"],
                "candidate_release_date": "2026-10-15",
            }
        ])
        self.assertIn("pending_review", sql)
        self.assertNotIn("verification_status", sql)
        self.assertIn("ON CONFLICT(source_key, external_id) DO UPDATE", sql)


if __name__ == "__main__":
    unittest.main()
