import copy
import unittest

from scripts.build_p1_completion_attestation import build_completion_attestation


ATTESTATION_SHA = "8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986"
PROJECTION_SHA = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
GRAPH_SHA = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"


class P1CompletionAttestationTests(unittest.TestCase):
    def setUp(self):
        self.reviewed_attestation = {
            "projection_sha256": PROJECTION_SHA,
            "global_materialization_sha256": GRAPH_SHA,
            "candidate_count": 16380,
            "totals": {
                "candidate_titles": 16380,
                "genres": 612,
                "people": 37964,
                "emitted_genre_relations": 16489,
                "emitted_credit_relations": 70551,
            },
        }
        self.projection = {
            "sha256": PROJECTION_SHA,
            "candidate_count": 16380,
            "movie_qid_count": 6562,
            "series_qid_count": 9818,
            "cross_type_collision_count": 0,
        }
        self.graph = {
            "state": "verified",
            "production_mutation": False,
            "global_materialization_sha256": GRAPH_SHA,
            "counts": {
                "candidate_titles": 16380,
                "genres": 612,
                "people": 37964,
                "emitted_genre_relations": 16489,
                "emitted_credit_relations": 70551,
            },
            "orphan_genre_relations": 0,
            "orphan_credit_relations": 0,
            "invalid_genre_provenance": 0,
            "invalid_credit_provenance": 0,
        }
        self.integrity = {
            "orphan_genres": 0,
            "orphan_credits": 0,
            "invalid_genre_provenance": 0,
            "invalid_credit_provenance": 0,
        }
        self.quality = {"finding_summary": {"by_severity": {"S0": 0, "S1": 0, "S2": 4}}}
        self.series = [{"id": "series-wd-Q3146368", "wikidata_qid": "Q3146368"}]

    def build(self, **overrides):
        values = {
            "reviewed_attestation": self.reviewed_attestation,
            "reviewed_attestation_sha256": ATTESTATION_SHA,
            "projection_manifest": self.projection,
            "graph_verification": self.graph,
            "integrity": self.integrity,
            "catalogue_quality": self.quality,
            "source_movies": [],
            "source_catalogue": [],
            "source_series": self.series,
            "expected_attestation_sha256": ATTESTATION_SHA,
            "expected_projection_sha256": PROJECTION_SHA,
            "expected_graph_sha256": GRAPH_SHA,
            "expected_candidates": 16380,
            "expected_movies": 6562,
            "expected_series": 9818,
            "expected_genres": 612,
            "expected_people": 37964,
            "expected_genre_relations": 16489,
            "expected_credit_relations": 70551,
        }
        values.update(overrides)
        return build_completion_attestation(**values)

    def test_verified_evidence_builds_completion_attestation(self):
        result = self.build()
        self.assertEqual(result["state"], "verified")
        self.assertTrue(result["p1_completion_eligible"])
        self.assertFalse(result["production_mutation"])
        self.assertEqual(result["production_projection"]["candidate_count"], 16380)
        self.assertEqual(result["production_graph"]["counts"]["title_credits"], 70551)
        self.assertEqual(result["catalogue_quality"], {"S0": 0, "S1": 0})
        self.assertEqual(len(result["evidence_sha256"]), 64)

    def test_attestation_hash_is_deterministic(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first["evidence_sha256"], second["evidence_sha256"])

    def test_projection_drift_fails_closed(self):
        projection = copy.deepcopy(self.projection)
        projection["sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "production projection mismatch"):
            self.build(projection_manifest=projection)

    def test_graph_sha_mismatch_fails_closed(self):
        graph = copy.deepcopy(self.graph)
        graph["global_materialization_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "final graph verification SHA mismatch"):
            self.build(graph_verification=graph)

    def test_graph_count_mismatch_fails_closed(self):
        graph = copy.deepcopy(self.graph)
        graph["counts"]["people"] -= 1
        with self.assertRaisesRegex(ValueError, "final graph counts mismatch"):
            self.build(graph_verification=graph)

    def test_nonzero_integrity_fails_closed(self):
        integrity = copy.deepcopy(self.integrity)
        integrity["orphan_credits"] = 1
        with self.assertRaisesRegex(ValueError, "production recommendation integrity is not clean"):
            self.build(integrity=integrity)

    def test_nonzero_s0_or_s1_fails_closed(self):
        quality = copy.deepcopy(self.quality)
        quality["finding_summary"]["by_severity"]["S1"] = 1
        with self.assertRaisesRegex(ValueError, "Catalogue Quality V1 is not clean"):
            self.build(catalogue_quality=quality)

    def test_source_cleanup_drift_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "reviewed source cleanup is incomplete"):
            self.build(source_movies=[{"id": "wd-Q3049630", "wikidata_qid": "Q3049630"}])

    def test_canonical_series_cleanup_identity_is_required(self):
        with self.assertRaisesRegex(ValueError, "canonical Series state mismatch"):
            self.build(source_series=[])


if __name__ == "__main__":
    unittest.main()
