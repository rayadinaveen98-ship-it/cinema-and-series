import unittest

from scripts.fetch_wikidata import normalize
from scripts.wikidata_to_sql import build_statements


class WikidataNormalizationTests(unittest.TestCase):
    @staticmethod
    def binding(qid: str, release_date: str, title: str, language: str = "Telugu", place: str | None = None) -> dict:
        row = {
            "item": {"value": f"http://www.wikidata.org/entity/{qid}"},
            "itemLabel": {"value": title},
            "date": {"value": f"{release_date}T00:00:00Z"},
            "languageLabel": {"value": language},
        }
        if place:
            row["place"] = {"value": f"http://www.wikidata.org/entity/{place}"}
        return row

    def test_india_qualified_date_wins(self):
        payload = {
            "results": {
                "bindings": [
                    self.binding("Q1", "2026-01-01", "Example"),
                    self.binding("Q1", "2026-02-01", "Example", place="Q668"),
                ]
            }
        }
        movies = normalize(payload)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["wikidata_qid"], "Q1")
        self.assertEqual(movies[0]["release_date"], "2026-02-01")
        self.assertEqual(movies[0]["candidate_dates"], ["2026-01-01", "2026-02-01"])
        self.assertEqual(movies[0]["selection_reason"], "india_qualified_latest")

    def test_latest_candidate_is_fallback_without_territory_qualifier(self):
        payload = {
            "results": {
                "bindings": [
                    self.binding("Q2", "2026-03-01", "Another Film", "Tamil"),
                    self.binding("Q2", "2026-04-10", "Another Film", "Tamil"),
                ]
            }
        }
        movies = normalize(payload)
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["release_date"], "2026-04-10")
        self.assertEqual(movies[0]["verification_status"], "unconfirmed")
        self.assertEqual(movies[0]["selection_reason"], "latest_open_data_candidate")

    def test_languages_are_deduplicated(self):
        payload = {
            "results": {
                "bindings": [
                    self.binding("Q3", "2026-06-12", "Multilingual", "Telugu"),
                    self.binding("Q3", "2026-06-12", "Multilingual", "Tamil"),
                    self.binding("Q3", "2026-06-12", "Multilingual", "Telugu"),
                ]
            }
        }
        movies = normalize(payload)
        self.assertEqual(movies[0]["languages"], ["Tamil", "Telugu"])

    def test_generated_sql_is_remote_d1_compatible(self):
        statements = build_statements(
            {
                "movies": [
                    {
                        "wikidata_qid": "Q10",
                        "title": "D1 Example",
                        "release_date": "2026-09-18",
                        "languages": ["Telugu"],
                        "source_url": "https://www.wikidata.org/wiki/Q10",
                    }
                ]
            }
        )
        sql = "\n".join(statements).upper()
        self.assertEqual(len(statements), 2)
        self.assertNotIn("BEGIN TRANSACTION", sql)
        self.assertNotIn("COMMIT;", sql)
        self.assertIn("ON CONFLICT", sql)


if __name__ == "__main__":
    unittest.main()
