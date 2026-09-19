import unittest

from scripts import repartition_recommendation_materialization as module


class RepartitionRecommendationMaterializationTests(unittest.TestCase):
    def test_global_rebuild_removes_reviewed_identity_and_adds_delta(self):
        parent = {
            "title_rows": [
                {"id": "wikidata:Q8", "wikidata_qid": "Q8", "media_type": "movie"},
                {"id": "wikidata:Q9", "wikidata_qid": "Q9", "media_type": "series"},
            ],
            "genre_rows": [
                {"id": "wikidata:Q100", "wikidata_qid": "Q100", "name": "Drama"},
            ],
            "people_rows": [
                {"id": "wikidata:Q200", "wikidata_qid": "Q200", "name": "Person"},
            ],
            "title_genre_rows": [
                {"title_id": "wikidata:Q8", "genre_id": "wikidata:Q100", "source_property": "P136", "source_url": "u8"},
                {"title_id": "wikidata:Q9", "genre_id": "wikidata:Q100", "source_property": "P136", "source_url": "u9"},
            ],
            "title_credit_rows": [
                {"title_id": "wikidata:Q9", "person_id": "wikidata:Q200", "role": "cast", "source_property": "P161", "source_url": "u9"},
            ],
        }
        delta = {
            "title_rows": [
                {"id": "wikidata:Q17", "wikidata_qid": "Q17", "media_type": "movie"},
            ],
            "genre_rows": [
                {"id": "wikidata:Q101", "wikidata_qid": "Q101", "name": "Comedy"},
            ],
            "people_rows": [],
            "title_genre_rows": [
                {"title_id": "wikidata:Q17", "genre_id": "wikidata:Q101", "source_property": "P136", "source_url": "u17"},
            ],
            "title_credit_rows": [],
        }
        manifest = {
            "entries": [
                {"wikidata_qid": "Q9"},
                {"wikidata_qid": "Q17"},
            ]
        }
        rebuilt = module.rebuild_global(parent, delta, removed_qids={"Q8"}, current_manifest=manifest)
        self.assertEqual({row["wikidata_qid"] for row in rebuilt["title_rows"]}, {"Q9", "Q17"})
        self.assertFalse(any(row["title_id"] == "wikidata:Q8" for row in rebuilt["title_genre_rows"]))
        self.assertEqual({row["id"] for row in rebuilt["genre_rows"]}, {"wikidata:Q100", "wikidata:Q101"})

    def test_physical_partition_uses_output_modulus_and_entity_closure(self):
        global_rows = {
            "title_rows": [
                {"id": "wikidata:Q16", "wikidata_qid": "Q16"},
                {"id": "wikidata:Q24", "wikidata_qid": "Q24"},
                {"id": "wikidata:Q17", "wikidata_qid": "Q17"},
            ],
            "genre_rows": [
                {"id": "wikidata:Q100"},
                {"id": "wikidata:Q101"},
            ],
            "people_rows": [
                {"id": "wikidata:Q200"},
                {"id": "wikidata:Q201"},
            ],
            "title_genre_rows": [
                {"title_id": "wikidata:Q16", "genre_id": "wikidata:Q100"},
                {"title_id": "wikidata:Q24", "genre_id": "wikidata:Q101"},
                {"title_id": "wikidata:Q17", "genre_id": "wikidata:Q101"},
            ],
            "title_credit_rows": [
                {"title_id": "wikidata:Q16", "person_id": "wikidata:Q200"},
                {"title_id": "wikidata:Q17", "person_id": "wikidata:Q201"},
            ],
        }
        shard0 = module.physical_shard(global_rows, 0, 16)
        shard8 = module.physical_shard(global_rows, 8, 16)
        shard1 = module.physical_shard(global_rows, 1, 16)
        self.assertEqual([row["wikidata_qid"] for row in shard0["title_rows"]], ["Q16"])
        self.assertEqual([row["wikidata_qid"] for row in shard8["title_rows"]], ["Q24"])
        self.assertEqual([row["wikidata_qid"] for row in shard1["title_rows"]], ["Q17"])
        self.assertEqual({row["id"] for row in shard0["genre_rows"]}, {"wikidata:Q100"})
        self.assertEqual({row["id"] for row in shard0["people_rows"]}, {"wikidata:Q200"})
        self.assertEqual({row["id"] for row in shard1["people_rows"]}, {"wikidata:Q201"})

    def test_conflicting_duplicate_entity_rows_fail_closed(self):
        with self.assertRaises(ValueError):
            module.dedupe_rows(
                [
                    {"id": "wikidata:Q1", "name": "One"},
                    {"id": "wikidata:Q1", "name": "Different"},
                ],
                ("id",),
            )


if __name__ == "__main__":
    unittest.main()
