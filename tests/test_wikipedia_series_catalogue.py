import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import fetch_wikipedia_series_catalogue as module


class WikipediaSeriesCatalogueTests(unittest.TestCase):
    def test_bootstrap_seeds_include_india_languages_and_recent_global_debuts(self):
        seeds = module.build_seeds("bootstrap", date(2026, 9, 16))
        categories = {seed.category for seed in seeds}
        self.assertIn("Category:Telugu-language television shows", categories)
        self.assertIn("Category:Hindi-language web series", categories)
        self.assertIn("Category:2026 American television series debuts", categories)
        self.assertIn("Category:2026 Indian television series debuts", categories)

    def test_series_page_filter_rejects_lists_and_season_pages(self):
        self.assertTrue(module._looks_like_series_page("Paatal Lok"))
        self.assertTrue(module._looks_like_series_page("The Office (American TV series)"))
        self.assertFalse(module._looks_like_series_page("List of Telugu-language television series"))
        self.assertFalse(module._looks_like_series_page("List of episodes of Example Show"))
        self.assertFalse(module._looks_like_series_page("Example Show season 2"))
        self.assertFalse(module._looks_like_series_page("Example Show series 3"))

    def test_category_members_captures_qid_in_discovery_request(self):
        seed = module.Seed(
            category="Category:2025 Indian television series debuts",
            country_code="IN",
            language=None,
            series_kind="series",
            group="debut-IN",
            first_air_year=2025,
        )
        payload = {
            "query": {
                "pages": [
                    {
                        "pageid": 123,
                        "title": "Example Show",
                        "pageprops": {"wikibase_item": "Q123"},
                    }
                ]
            }
        }
        with patch.object(module.base, "request_json", return_value=payload) as mocked:
            rows = module.category_members(seed, cap=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].qid, "Q123")
        self.assertEqual(rows[0].page_id, 123)
        self.assertEqual(rows[0].first_air_year, 2025)
        params = mocked.call_args.args[1]
        self.assertEqual(params["generator"], "categorymembers")
        self.assertEqual(params["prop"], "pageprops")
        self.assertEqual(params["ppprop"], "wikibase_item")

    def test_static_category_does_not_invent_first_air_year(self):
        seed = module.Seed(
            category="Category:Telugu-language television shows",
            country_code="IN",
            language="Telugu",
            series_kind="series",
            group="india-Telugu",
        )
        row = module.Discovery(1, "Q1", "Example", "IN", "Telugu", "series", seed.category, seed.first_air_year)
        merged = module.merge_discoveries({1: [row]})[0]
        self.assertIsNone(merged["first_air_year"])
        self.assertEqual(merged["observed_first_air_years"], [])

    def test_merge_dedupes_page_and_prefers_specific_kind(self):
        rows = [
            module.Discovery(42, "Q42", "Example Series", "IN", "Hindi", "series", "Category:Hindi-language television shows", None),
            module.Discovery(42, "Q42", "Example Series", "IN", "Hindi", "web_series", "Category:Indian web series", None),
        ]
        merged = module.merge_discoveries({42: rows})
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "series-wd-Q42")
        self.assertEqual(merged[0]["series_kind"], "web_series")
        self.assertEqual(merged[0]["wikidata_qid"], "Q42")

    def test_sql_targets_series_projection_only(self):
        item = {
            "id": "series-wd-Q9",
            "wikidata_qid": "Q9",
            "wikipedia_page_id": 99,
            "title": "Nine Episodes",
            "series_kind": "miniseries",
            "language": "Hindi",
            "country_code": "IN",
            "first_air_year": 2021,
            "source_category": "Category:Indian television miniseries",
            "source_url": "https://en.wikipedia.org/?curid=99",
            "verification_status": "unconfirmed",
        }
        sql = module.build_sql([item])
        self.assertIn("INSERT INTO series_titles", sql)
        self.assertNotIn("INSERT INTO movies", sql)
        self.assertNotIn("INSERT INTO catalogue_titles", sql)
        self.assertNotIn("2021-01-01", sql)
        self.assertIn("miniseries", sql)


if __name__ == "__main__":
    unittest.main()
