import unittest
from datetime import date
from unittest.mock import patch

from scripts import fetch_mediawiki_backfill
from scripts.fetch_mediawiki_backfill import Seed, build_seeds, claim_time_dates, discover_titles, normalize_entities


class MediaWikiBackfillTests(unittest.TestCase):
    def test_bootstrap_prioritizes_indian_language_and_global_country_categories(self):
        seeds = build_seeds("bootstrap", date(2026, 9, 16))
        categories = {seed.category for seed in seeds}
        self.assertIn("Category:2024 Telugu-language films", categories)
        self.assertIn("Category:2024 Malayalam-language films", categories)
        self.assertIn("Category:2024 South Korean films", categories)
        self.assertIn("Category:2024 American films", categories)
        self.assertTrue(all(seed.category.startswith("Category:") for seed in seeds))

    def test_rotation_changes_historical_year_slice(self):
        day_one = {seed.category.split(" ", 1)[0] for seed in build_seeds("rotate", date(2026, 9, 16))}
        day_two = {seed.category.split(" ", 1)[0] for seed in build_seeds("rotate", date(2026, 9, 17))}
        self.assertNotEqual(day_one, day_two)

    def test_claim_dates_require_day_precision(self):
        entity = {
            "claims": {
                "P577": [
                    {"mainsnak": {"datavalue": {"value": {"time": "+2024-05-03T00:00:00Z", "precision": 11}}}},
                    {"mainsnak": {"datavalue": {"value": {"time": "+2024-00-00T00:00:00Z", "precision": 9}}}},
                ]
            }
        }
        self.assertEqual(claim_time_dates(entity), ["2024-05-03"])

    def test_discovery_balances_groups_before_cap(self):
        seeds = [
            Seed("Category:One", "IN", "Telugu", "india-Telugu"),
            Seed("Category:Two", "KR", None, "country-KR"),
        ]
        with patch.object(fetch_mediawiki_backfill, "category_members", side_effect=[["A", "B", "C"], ["K1", "K2"]]), patch.object(fetch_mediawiki_backfill.time, "sleep"):
            titles, metadata, reports = discover_titles(seeds, 4)
        self.assertEqual(titles, ["K1", "A", "K2", "B"])
        self.assertEqual(metadata["A"][0].language, "Telugu")
        self.assertEqual(len(reports), 2)

    def test_normalize_entities_uses_seeded_language_country_and_earliest_date(self):
        entity = {
            "id": "Q123",
            "labels": {"en": {"value": "Example Film"}},
            "sitelinks": {"enwiki": {"title": "Example Film"}},
            "claims": {
                "P577": [
                    {"mainsnak": {"datavalue": {"value": {"time": "+2024-06-02T00:00:00Z", "precision": 11}}}},
                    {"mainsnak": {"datavalue": {"value": {"time": "+2024-05-01T00:00:00Z", "precision": 11}}}},
                ],
                "P364": [],
            },
        }
        metadata = {"Example Film": [Seed("Category:2024 Telugu-language films", "IN", "Telugu", "india-Telugu")]}
        with patch.object(fetch_mediawiki_backfill, "fetch_labels", return_value={}):
            movies = normalize_entities([entity], metadata)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["wikidata_qid"], "Q123")
        self.assertEqual(movies[0]["release_date"], "2024-05-01")
        self.assertEqual(movies[0]["language" if "language" in movies[0] else "languages"], ["Telugu"])
        self.assertEqual(movies[0]["country_code"], "IN")
        self.assertEqual(movies[0]["merge_strategy"], "earliest")


if __name__ == "__main__":
    unittest.main()
