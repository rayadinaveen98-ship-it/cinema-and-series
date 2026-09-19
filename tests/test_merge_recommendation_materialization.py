import unittest

from scripts import merge_recommendation_materialization as merge


class MergeRecommendationMaterializationTests(unittest.TestCase):
    def test_merge_removes_reviewed_title_and_adds_delta_title(self):
        parent = {
            "title_rows": [
                {"id": "wikidata:Q8", "wikidata_qid": "Q8"},
                {"id": "wikidata:Q3049630", "wikidata_qid": "Q3049630"},
            ],
            "genre_rows": [
                {"id": "wikidata:Q100", "wikidata_qid": "Q100", "name": "Genre", "source_url": "u"},
                {"id": "wikidata:Q200", "wikidata_qid": "Q200", "name": "Removed Genre", "source_url": "u"},
            ],
            "people_rows": [],
            "title_genre_rows": [
                {"title_id": "wikidata:Q8", "genre_id": "wikidata:Q100", "source_property": "P136", "source_url": "u"},
                {"title_id": "wikidata:Q3049630", "genre_id": "wikidata:Q200", "source_property": "P136", "source_url": "u"},
            ],
            "title_credit_rows": [],
            "stats": {"missing_title_entities": 0},
        }
        delta = {
            "title_rows": [{"id": "wikidata:Q16", "wikidata_qid": "Q16"}],
            "genre_rows": [{"id": "wikidata:Q300", "wikidata_qid": "Q300", "name": "New Genre", "source_url": "u"}],
            "people_rows": [],
            "title_genre_rows": [
                {"title_id": "wikidata:Q16", "genre_id": "wikidata:Q300", "source_property": "P136", "source_url": "u"}
            ],
            "title_credit_rows": [],
            "stats": {"missing_title_entities": 0, "unusable_claims": 0, "skipped_relations_missing_label": 0},
        }
        current_manifest = {
            "schema_version": "recommendation-projection-manifest-v2",
            "candidate_count": 2,
            "movie_qid_count": 2,
            "series_qid_count": 0,
            "sha256": "current",
        }
        parent_manifest = {"sha256": "parent"}
        expected = [{"wikidata_qid": "Q8"}, {"wikidata_qid": "Q16"}]
        result = merge.merge_shard(
            parent,
            delta,
            removed_qids={"Q3049630"},
            expected_entries=expected,
            current_manifest=current_manifest,
            parent_manifest=parent_manifest,
            shard_index=0,
            shard_count=8,
        )
        self.assertEqual({row["wikidata_qid"] for row in result["title_rows"]}, {"Q8", "Q16"})
        self.assertEqual({row["id"] for row in result["genre_rows"]}, {"wikidata:Q100", "wikidata:Q300"})
        self.assertEqual(result["stats"]["emitted_genre_relations"], 2)
        self.assertEqual(result["lineage"]["inherited_parent_titles"], 1)
        self.assertEqual(result["lineage"]["delta_titles"], 1)

    def test_partition_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "partition mismatch"):
            merge.merge_shard(
                {"title_rows": [], "genre_rows": [], "people_rows": [], "title_genre_rows": [], "title_credit_rows": [], "stats": {}},
                {"title_rows": [], "genre_rows": [], "people_rows": [], "title_genre_rows": [], "title_credit_rows": [], "stats": {}},
                removed_qids=set(),
                expected_entries=[{"wikidata_qid": "Q8"}],
                current_manifest={"schema_version": "v", "candidate_count": 1, "movie_qid_count": 1, "series_qid_count": 0, "sha256": "c"},
                parent_manifest={"sha256": "p"},
                shard_index=0,
                shard_count=8,
            )


if __name__ == "__main__":
    unittest.main()
