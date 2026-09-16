import unittest
import urllib.error
from email.message import Message
from unittest.mock import patch

from scripts import fetch_wikidata
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

    def test_unresolved_qid_label_is_not_imported(self):
        statements = build_statements(
            {
                "movies": [
                    {
                        "wikidata_qid": "Q999",
                        "title": "Q999",
                        "release_date": "2026-09-18",
                        "languages": ["Unknown"],
                        "source_url": "https://www.wikidata.org/wiki/Q999",
                    }
                ]
            }
        )
        self.assertEqual(statements, [])

    def test_long_rate_limit_is_deferred_without_sleeping(self):
        headers = Message()
        headers["Retry-After"] = "1000"
        error = urllib.error.HTTPError(
            url=fetch_wikidata.ENDPOINTS[0],
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=None,
        )
        with patch.object(fetch_wikidata, "fetch", side_effect=error), patch.object(fetch_wikidata.time, "sleep") as sleep:
            with self.assertRaises(fetch_wikidata.WikidataDeferred):
                fetch_wikidata.fetch_with_resilience()
        sleep.assert_not_called()

    def test_bounded_rate_limit_cooldown_can_retry(self):
        headers = Message()
        headers["Retry-After"] = "65"
        error = urllib.error.HTTPError(
            url=fetch_wikidata.ENDPOINTS[0],
            code=429,
            msg="Too Many Requests",
            hdrs=headers,
            fp=None,
        )
        payload = {"results": {"bindings": []}}
        with patch.object(fetch_wikidata, "fetch", side_effect=[error, payload]) as fetch, patch.object(fetch_wikidata.time, "sleep") as sleep:
            result = fetch_wikidata.fetch_with_resilience()
        self.assertEqual(result, payload)
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(65)


if __name__ == "__main__":
    unittest.main()
