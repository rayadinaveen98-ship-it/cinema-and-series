import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "official_to_sql.py"
spec = importlib.util.spec_from_file_location("official_to_sql", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class OfficialPipelineTests(unittest.TestCase):
    def test_official_qid_release_promotes_to_verified(self):
        statements = module.build_statements(
            {
                "releases": [
                    {
                        "title": "Jailer 2",
                        "wikidata_qid": "Q133255153",
                        "language": "Tamil",
                        "country_code": "IN",
                        "release_date": "2026-10-15",
                        "source_key": "sun_pictures",
                        "source_type": "official_website",
                        "source_title": "Jailer 2 — Sun Pictures",
                        "source_url": "https://www.sunpictures.in/movies/jailer2/",
                    }
                ]
            },
            {"sources": []},
        )
        sql = "\n".join(statements)
        self.assertIn("wd-Q133255153", sql)
        self.assertIn("verification_status='verified'", sql)
        self.assertIn("release_date_source=excluded.release_date_source", sql)
        self.assertIn("is_official", sql)

    def test_title_only_release_reuses_existing_title_before_insert(self):
        statements = module.build_statements(
            {
                "releases": [
                    {
                        "title": "Dragon",
                        "wikidata_qid": None,
                        "language": "Telugu",
                        "country_code": "IN",
                        "release_date": "2027-06-11",
                        "source_key": "mythri_movie_makers",
                        "source_type": "official_youtube",
                        "source_title": "Dragon Glimpse",
                        "source_url": "https://www.youtube.com/watch?v=bedocP4nRAo",
                    }
                ]
            },
            {"sources": []},
        )
        sql = "\n".join(statements)
        self.assertIn("UPDATE movies SET", sql)
        self.assertIn("WHERE NOT EXISTS", sql)
        self.assertIn("official-dragon", sql)

    def test_source_registry_is_idempotent(self):
        statements = module.build_statements(
            {"releases": []},
            {
                "sources": [
                    {
                        "key": "mythri_movie_makers",
                        "name": "Mythri Movie Makers",
                        "source_type": "production_house",
                        "website_url": "https://mythrimoviemakers.com/",
                        "youtube_channel_id": "UCKZSn5C-RzrLjuWJF8wWiDw",
                        "youtube_handle": "@MythriMovieMakers",
                        "active": True,
                    }
                ]
            },
        )
        self.assertEqual(len(statements), 1)
        self.assertIn("ON CONFLICT(source_key) DO UPDATE", statements[0])


if __name__ == "__main__":
    unittest.main()
