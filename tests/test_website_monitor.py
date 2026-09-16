import importlib.util
import unittest
from datetime import date
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "website_monitor.py"
spec = importlib.util.spec_from_file_location("website_monitor", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class WebsiteMonitorTests(unittest.TestCase):
    def test_extracts_future_release_date_near_release_context(self):
        dates, excerpts = module.extract_release_signals(
            "Our next film arrives in cinemas on 15 October 2026 worldwide.",
            today=date(2026, 9, 16),
        )
        self.assertEqual(dates, ["2026-10-15"])
        self.assertTrue(excerpts)

    def test_rejects_old_catalogue_release_date(self):
        dates, _ = module.extract_release_signals(
            "The film released in cinemas on 15 August 2024.",
            today=date(2026, 9, 16),
        )
        self.assertEqual(dates, [])

    def test_rejects_date_without_release_context(self):
        dates, _ = module.extract_release_signals(
            "Company founded on 15 October 2026.",
            today=date(2026, 9, 16),
        )
        self.assertEqual(dates, [])

    def test_candidate_links_stay_on_same_host_and_release_sections(self):
        links = module.candidate_links(
            "https://studio.example/",
            [
                ("/movies", "Movies"),
                ("/news/latest-film", "Latest Film News"),
                ("https://other.example/releases", "Releases"),
                ("/contact", "Contact"),
                ("/logo.png", "Film logo"),
            ],
        )
        self.assertEqual(
            links,
            ["https://studio.example/movies", "https://studio.example/news/latest-film"],
        )

    def test_page_parser_and_observation_remain_pending_review(self):
        parser = module.PageParser()
        parser.feed(
            "<html><head><title>Example Film</title></head><body>"
            "<h1>Example Film</h1><p>In cinemas 4 Sep 2027 worldwide.</p></body></html>"
        )
        observation = module.observation_for_page(
            {"key": "example", "name": "Example Studio"},
            "https://studio.example/example-film",
            parser,
            today=date(2026, 9, 16),
        )
        self.assertIsNotNone(observation)
        assert observation is not None
        self.assertEqual(observation["candidate_release_date"], "2027-09-04")
        self.assertEqual(observation["status"], "pending_review")
        self.assertTrue(observation["external_id"].startswith("web-"))

    def test_sql_upserts_source_before_pending_observation(self):
        source = {
            "key": "example",
            "name": "Example Studio",
            "source_type": "production_house",
            "website_url": "https://studio.example/",
            "youtube_channel_id": None,
            "youtube_handle": None,
            "active": True,
        }
        candidate = {
            "source_key": "example",
            "external_id": "web-123",
            "page_url": "https://studio.example/movie",
            "review_title": "Movie — In cinemas 4 Sep 2027",
            "candidate_dates": ["2027-09-04"],
            "candidate_release_date": "2027-09-04",
        }
        sql = module.build_sql([candidate], [source])
        self.assertLess(sql.index("INSERT INTO source_channels"), sql.index("INSERT INTO source_observations"))
        self.assertIn("pending_review", sql)
        self.assertNotIn("verification_status", sql)


if __name__ == "__main__":
    unittest.main()
