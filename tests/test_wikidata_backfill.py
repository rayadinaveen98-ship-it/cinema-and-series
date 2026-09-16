import unittest
from datetime import date

from scripts import fetch_wikidata_backfill
from scripts.fetch_wikidata_backfill import Country, Shard, balanced_selection, normalize, query_text, selected_shards
from scripts.wikidata_to_sql import build_statements


class WikidataBackfillTests(unittest.TestCase):
    @staticmethod
    def binding(
        qid: str,
        release_date: str,
        title: str,
        country_qid: str = "Q668",
        country_label: str = "India",
        language: str = "Telugu",
    ) -> dict:
        return {
            "item": {"value": f"http://www.wikidata.org/entity/{qid}"},
            "itemLabel": {"value": title},
            "date": {"value": f"{release_date}T00:00:00Z"},
            "languageLabel": {"value": language},
            "country": {"value": f"http://www.wikidata.org/entity/{country_qid}"},
            "countryLabel": {"value": country_label},
        }

    def test_normalize_uses_earliest_date_and_country(self):
        shard = Shard("india-test", 1990, 2000, (Country("Q668", "IN", "India"),))
        payload = {
            "results": {
                "bindings": [
                    self.binding("Q1", "1998-06-10", "Example", language="Hindi"),
                    self.binding("Q1", "1998-05-01", "Example", language="Telugu"),
                ]
            }
        }
        movies = normalize([(shard, payload)])
        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["release_date"], "1998-05-01")
        self.assertEqual(movies[0]["candidate_dates"], ["1998-05-01", "1998-06-10"])
        self.assertEqual(movies[0]["country_code"], "IN")
        self.assertEqual(movies[0]["languages"], ["Hindi", "Telugu"])
        self.assertEqual(movies[0]["merge_strategy"], "earliest")

    def test_query_is_sharded_and_pageable(self):
        shard = Shard("korea-test", 2020, 2024, (Country("Q884", "KR", "South Korea"),), page=2)
        query = query_text(shard)
        self.assertIn("VALUES ?country { wd:Q884 }", query)
        self.assertIn("YEAR(?date) >= 2020", query)
        self.assertIn("YEAR(?date) <= 2024", query)
        self.assertIn(f"LIMIT {fetch_wikidata_backfill.QUERY_LIMIT}", query)
        self.assertIn(f"OFFSET {fetch_wikidata_backfill.QUERY_LIMIT * 2}", query)

    def test_rotation_advances_page_after_full_shard_cycle(self):
        at_anchor = selected_shards("rotate", date(2026, 9, 16))
        after_six_days = selected_shards("rotate", date(2026, 9, 22))
        self.assertEqual(at_anchor[0].key, fetch_wikidata_backfill.ROTATION_SHARDS[0].key)
        self.assertEqual(at_anchor[0].page, 0)
        self.assertEqual(after_six_days[0].key, fetch_wikidata_backfill.ROTATION_SHARDS[0].key)
        self.assertEqual(after_six_days[0].page, 1)

    def test_balanced_selection_prevents_one_shard_from_consuming_run(self):
        india = Shard("india", 2000, 2001, (Country("Q668", "IN", "India"),))
        korea = Shard("korea", 2000, 2001, (Country("Q884", "KR", "South Korea"),))
        india_payload = {
            "results": {
                "bindings": [
                    self.binding("Q1", "2000-01-01", "India One"),
                    self.binding("Q2", "2000-01-02", "India Two"),
                    self.binding("Q3", "2000-01-03", "India Three"),
                ]
            }
        }
        korea_payload = {
            "results": {
                "bindings": [
                    self.binding("Q4", "2000-02-01", "Korea One", "Q884", "South Korea", "Korean"),
                    self.binding("Q5", "2000-02-02", "Korea Two", "Q884", "South Korea", "Korean"),
                ]
            }
        }
        movies = balanced_selection([(india, india_payload), (korea, korea_payload)], 4)
        self.assertEqual([movie["wikidata_qid"] for movie in movies], ["Q1", "Q4", "Q2", "Q5"])

    def test_backfill_sql_keeps_stronger_dates_and_country(self):
        statements = build_statements(
            {
                "merge_strategy": "earliest",
                "movies": [
                    {
                        "wikidata_qid": "Q77",
                        "title": "Global Example",
                        "release_date": "1999-04-02",
                        "languages": ["Korean"],
                        "country_code": "KR",
                        "source_url": "https://www.wikidata.org/wiki/Q77",
                    }
                ],
            }
        )
        movie_sql = statements[0]
        self.assertIn("'KR'", movie_sql)
        self.assertIn("movies.verification_status IN ('verified','supported')", movie_sql)
        self.assertIn("excluded.release_date < movies.release_date", movie_sql)
        self.assertIn("WHERE movies.title <> excluded.title", movie_sql)

    def test_default_sql_contract_still_defaults_to_india_replace(self):
        statements = build_statements(
            {
                "movies": [
                    {
                        "wikidata_qid": "Q88",
                        "title": "India Example",
                        "release_date": "2026-10-10",
                        "languages": ["Tamil"],
                    }
                ]
            }
        )
        movie_sql = statements[0]
        self.assertIn("'IN'", movie_sql)
        self.assertIn("excluded.release_date <> movies.release_date", movie_sql)


if __name__ == "__main__":
    unittest.main()
