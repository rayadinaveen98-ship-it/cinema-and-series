import unittest

from scripts import enrich_recommendation_metadata as enrich


class RecommendationMetadataEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.movie = {
            "id": "wikidata:Q100",
            "wikidata_qid": "Q100",
            "media_type": "movie",
            "display_title": "Movie's Night",
            "source_table": "movies",
            "source_id": "movie-100",
            "source_url": "https://www.wikidata.org/wiki/Q100",
        }
        self.series = {
            "id": "wikidata:Q200",
            "wikidata_qid": "Q200",
            "media_type": "series",
            "display_title": "Series 200",
            "source_table": "series_titles",
            "source_id": "series-200",
            "source_url": "https://www.wikidata.org/wiki/Q200",
        }

    @staticmethod
    def claim(qid):
        return {
            "rank": "normal",
            "mainsnak": {
                "snaktype": "value",
                "datavalue": {"value": {"id": qid}},
            },
        }

    def test_collects_explicit_movie_relations(self):
        entities = {
            "Q100": {
                "claims": {
                    "P136": [self.claim("Q1")],
                    "P57": [self.claim("Q2")],
                    "P170": [self.claim("Q999")],
                    "P161": [self.claim("Q3")],
                }
            }
        }
        relations, genres, people, stats = enrich.collect_relations([self.movie], entities)
        self.assertEqual(genres, {"Q1"})
        self.assertEqual(people, {"Q2", "Q3"})
        self.assertEqual(stats["creator_relations"], 0)
        self.assertEqual({item["role"] for item in relations if item["kind"] == "credit"}, {"director", "cast"})

    def test_series_creator_is_materialized(self):
        entities = {
            "Q200": {"claims": {"P170": [self.claim("Q20")]}}
        }
        relations, _, people, stats = enrich.collect_relations([self.series], entities)
        self.assertEqual(people, {"Q20"})
        self.assertEqual(stats["creator_relations"], 1)
        self.assertEqual(relations[0]["role"], "creator")

    def test_missing_labels_skip_dependent_relationship_only(self):
        entities = {
            "Q100": {
                "claims": {
                    "P136": [self.claim("Q1")],
                    "P57": [self.claim("Q2")],
                    "P161": [self.claim("Q3")],
                }
            }
        }
        result = enrich.materialize([self.movie], entities, {"Q1": "Drama", "Q2": "Director Name"})
        self.assertEqual(len(result["title_rows"]), 1)
        self.assertEqual(len(result["genre_rows"]), 1)
        self.assertEqual(len(result["people_rows"]), 1)
        self.assertEqual(len(result["title_genre_rows"]), 1)
        self.assertEqual(len(result["title_credit_rows"]), 1)
        self.assertEqual(result["stats"]["skipped_relations_missing_label"], 1)

    def test_same_person_can_have_multiple_explicit_roles(self):
        entities = {
            "Q200": {
                "claims": {
                    "P57": [self.claim("Q20")],
                    "P170": [self.claim("Q20")],
                    "P161": [self.claim("Q20")],
                }
            }
        }
        result = enrich.materialize([self.series], entities, {"Q20": "Multi Role"})
        roles = sorted(row["role"] for row in result["title_credit_rows"])
        self.assertEqual(roles, ["cast", "creator", "director"])
        self.assertEqual(len(result["people_rows"]), 1)

    def test_sql_quote_escapes_apostrophes(self):
        self.assertEqual(enrich.sql_quote("Movie's Night"), "'Movie''s Night'")

    def test_render_sql_is_transactional_and_idempotent(self):
        entities = {
            "Q100": {
                "claims": {
                    "P136": [self.claim("Q1")],
                    "P57": [self.claim("Q2")],
                }
            }
        }
        result = enrich.materialize([self.movie], entities, {"Q1": "Drama", "Q2": "Director's Name"})
        sql = enrich.render_sql(result)
        self.assertIn("BEGIN;", sql)
        self.assertTrue(sql.rstrip().endswith("COMMIT;"))
        self.assertIn("ON CONFLICT(wikidata_qid) DO UPDATE", sql)
        self.assertIn("INSERT OR IGNORE INTO title_genres", sql)
        self.assertIn("INSERT OR IGNORE INTO title_credits", sql)
        self.assertIn("Director''s Name", sql)

    def test_missing_title_entity_emits_title_but_no_relations(self):
        result = enrich.materialize([self.movie], {}, {})
        self.assertEqual(len(result["title_rows"]), 1)
        self.assertEqual(result["stats"]["missing_title_entities"], 1)
        self.assertEqual(result["title_genre_rows"], [])
        self.assertEqual(result["title_credit_rows"], [])

    def test_entity_url_is_stable(self):
        self.assertEqual(enrich.entity_url("Q123"), "https://www.wikidata.org/wiki/Q123")


if __name__ == "__main__":
    unittest.main()
