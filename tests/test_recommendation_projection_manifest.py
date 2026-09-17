import unittest

from scripts import recommendation_projection_manifest as manifest


class RecommendationProjectionManifestTests(unittest.TestCase):
    def test_exact_movie_precedence_is_reflected_in_manifest(self):
        exact = [{"id": "m1", "wikidata_qid": "Q10", "title": "Exact"}]
        catalogue = [{"id": "c1", "wikidata_qid": "Q10", "title": "Year", "source_url": "https://example.com/c1"}]
        result = manifest.build_manifest(exact, catalogue, [])
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["suppressed_catalogue_overlap_count"], 1)
        self.assertEqual(result["entries"][0]["source_table"], "movies")

    def test_fingerprint_is_stable_for_input_order(self):
        first = [
            {"id": "m2", "wikidata_qid": "Q20", "title": "Twenty"},
            {"id": "m1", "wikidata_qid": "Q10", "title": "Ten"},
        ]
        second = list(reversed(first))
        left = manifest.build_manifest(first, [], [])
        right = manifest.build_manifest(second, [], [])
        self.assertEqual(left["sha256"], right["sha256"])
        self.assertEqual(left["entries"], right["entries"])

    def test_title_change_changes_fingerprint(self):
        before = manifest.build_manifest(
            [{"id": "m1", "wikidata_qid": "Q10", "title": "Old Title"}], [], []
        )
        after = manifest.build_manifest(
            [{"id": "m1", "wikidata_qid": "Q10", "title": "Corrected Title"}], [], []
        )
        self.assertNotEqual(before["sha256"], after["sha256"])

    def test_source_projection_change_changes_fingerprint(self):
        catalogue = [{"id": "c1", "wikidata_qid": "Q10", "title": "Ten", "source_url": "https://example.com/c1"}]
        before = manifest.build_manifest([], catalogue, [])
        after = manifest.build_manifest([{"id": "m1", "wikidata_qid": "Q10", "title": "Ten"}], catalogue, [])
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.assertEqual(before["entries"][0]["source_table"], "catalogue_titles")
        self.assertEqual(after["entries"][0]["source_table"], "movies")

    def test_cross_type_collision_is_hard_failure(self):
        with self.assertRaises(ValueError):
            manifest.build_manifest(
                [{"id": "m1", "wikidata_qid": "Q10", "title": "Movie"}],
                [],
                [{"id": "s1", "wikidata_qid": "Q10", "title": "Series", "source_url": "https://example.com/s1"}],
            )


if __name__ == "__main__":
    unittest.main()
