import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import fetch_wikipedia_year_catalogue as module


class WikipediaYearCatalogueTests(unittest.TestCase):
    def test_category_year_requires_explicit_leading_year(self):
        self.assertEqual(module.category_year("Category:2024 Telugu-language films"), 2024)
        with self.assertRaises(ValueError):
            module.category_year("Category:Telugu-language films")

    def test_category_members_captures_qid_in_discovery_request(self):
        seed = module.base.Seed(
            category="Category:2024 Telugu-language films",
            country_code="IN",
            language="Telugu",
            group="india-Telugu",
        )
        payload = {
            "query": {
                "pages": [
                    {"pageid": 42, "title": "Example Film", "pageprops": {"wikibase_item": "Q123"}},
                    {"pageid": 43, "title": "No QID Film"},
                ]
            }
        }
        with patch.object(module.base, "request_json", return_value=payload) as request:
            rows = module.category_members(seed, cap=10)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].wikidata_qid, "Q123")
        self.assertIsNone(rows[1].wikidata_qid)
        params = request.call_args.args[1]
        self.assertEqual(params["generator"], "categorymembers")
        self.assertEqual(params["prop"], "pageprops")
        self.assertEqual(params["ppprop"], "wikibase_item")

    def test_captured_qids_avoids_second_lookup_for_known_pages(self):
        by_page = {
            42: [module.Discovery(42, "One", 2024, "IN", "Telugu", "Category:2024 Telugu-language films", "Q42")],
            43: [module.Discovery(43, "Two", 2024, "IN", "Telugu", "Category:2024 Telugu-language films")],
        }
        self.assertEqual(module.captured_qids(by_page), {42: "Q42"})

    def test_merge_discoveries_keeps_year_precision_and_stable_identity(self):
        first = module.Discovery(
            page_id=42,
            title="Example Film",
            release_year=2021,
            country_code="IN",
            language="Telugu",
            category="Category:2021 Telugu-language films",
        )
        second = module.Discovery(
            page_id=42,
            title="Example Film",
            release_year=2021,
            country_code="IN",
            language="Telugu",
            category="Category:2021 Indian films",
        )
        movies = module.merge_discoveries({42: [first, second]}, {42: "Q123"})

        self.assertEqual(len(movies), 1)
        movie = movies[0]
        self.assertEqual(movie["id"], "wd-Q123")
        self.assertEqual(movie["wikidata_qid"], "Q123")
        self.assertEqual(movie["wikipedia_page_id"], 42)
        self.assertEqual(movie["release_year"], 2021)
        self.assertEqual(movie["date_precision"], "year")
        self.assertEqual(movie["verification_status"], "unconfirmed")
        self.assertEqual(movie["country_code"], "IN")

    def test_conflicting_year_categories_do_not_invent_day_precision(self):
        rows = [
            module.Discovery(7, "Festival Film", 2020, "FR", None, "Category:2020 French films"),
            module.Discovery(7, "Festival Film", 2021, "FR", None, "Category:2021 French films"),
        ]
        movie = module.merge_discoveries({7: rows}, {})[0]
        self.assertEqual(movie["observed_release_years"], [2020, 2021])
        self.assertEqual(movie["release_year"], 2020)
        self.assertEqual(movie["date_precision"], "year")
        self.assertNotIn("release_date", movie)

    def test_qid_resolution_keeps_later_batch_after_failure(self):
        page_ids = list(range(1, 52))
        second_payload = {
            "query": {
                "pages": [
                    {"pageid": 51, "pageprops": {"wikibase_item": "Q51"}},
                ]
            }
        }
        with patch.object(module.base, "request_json", side_effect=[RuntimeError("temporary"), second_payload]):
            with patch.object(module.time, "sleep", return_value=None):
                resolved, reports = module.resolve_qids(page_ids)

        self.assertEqual(resolved, {51: "Q51"})
        self.assertEqual(reports[0]["status"], "deferred")
        self.assertEqual(reports[1]["status"], "ok")

    def test_sql_targets_only_year_precision_projection(self):
        movie = {
            "id": "wd-Q9",
            "wikidata_qid": "Q9",
            "wikipedia_page_id": 99,
            "title": "Nine",
            "release_year": 1999,
            "date_precision": "year",
            "language": "Hindi",
            "country_code": "IN",
            "source_category": "Category:1999 Hindi-language films",
            "source_url": "https://en.wikipedia.org/?curid=99",
            "verification_status": "unconfirmed",
        }
        sql = module.build_sql([movie])
        self.assertIn("INSERT INTO catalogue_titles", sql)
        self.assertNotIn("INSERT INTO movies", sql)
        self.assertNotIn("1999-01-01", sql)
        self.assertIn("1999", sql)
        self.assertIn("Q9", sql)


if __name__ == "__main__":
    unittest.main()
