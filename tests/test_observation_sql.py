import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "observation_sql.py"
spec = importlib.util.spec_from_file_location("observation_sql", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class ObservationSqlTests(unittest.TestCase):
    def test_youtube_sql_persists_compact_date_contexts(self):
        candidate = {
            "source_key": "t_series",
            "video_id": "abc123",
            "video_url": "https://www.youtube.com/watch?v=abc123",
            "video_title": "Example Film teaser",
            "published_at": "2026-09-16T06:30:20Z",
            "candidate_dates": ["2026-10-23"],
            "candidate_release_date": "2026-10-23",
            "date_contexts": [
                {"date": "2026-10-23", "excerpt": "Example Film — in cinemas 23 October 2026."}
            ],
        }
        sql = module.build_observation_sql([candidate], [], "youtube")
        self.assertIn("evidence_contexts_json", sql)
        self.assertIn("in cinemas 23 October 2026", sql)
        self.assertIn("pending_review", sql)

    def test_website_sql_persists_context_excerpts(self):
        candidate = {
            "source_key": "studio",
            "external_id": "web-123",
            "page_url": "https://studio.example/film",
            "review_title": "Example Film release update",
            "candidate_dates": ["2027-01-08"],
            "candidate_release_date": "2027-01-08",
            "context_excerpts": ["Example Film releases worldwide on 8 January 2027."],
        }
        sql = module.build_observation_sql([candidate], [], "website")
        self.assertIn("evidence_contexts_json", sql)
        self.assertIn("releases worldwide on 8 January 2027", sql)
        self.assertIn("NULL,'2027-01-08'", sql)

    def test_empty_queue_produces_no_sql(self):
        self.assertEqual(module.build_observation_sql([], [], "youtube"), "")

    def test_unsupported_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            module.build_observation_sql([{}], [], "social")


if __name__ == "__main__":
    unittest.main()
