import unittest

from scripts import repartition_recommendation_materialization as repartition
from scripts import verify_p1_v3_production as module


class P1V3ProductionVerificationTests(unittest.TestCase):
    def graph(self):
        return module.canonical_production_graph(
            [
                {
                    "id": "wikidata:Q1",
                    "wikidata_qid": "Q1",
                    "media_type": "movie",
                    "display_title": "One",
                    "source_table": "movies",
                    "source_id": "wd-Q1",
                    "source_url": "https://www.wikidata.org/wiki/Q1",
                }
            ],
            [
                {
                    "id": "wikidata:Q2",
                    "wikidata_qid": "Q2",
                    "name": "Drama",
                    "source_url": "https://www.wikidata.org/wiki/Q2",
                }
            ],
            [
                {
                    "id": "wikidata:Q3",
                    "wikidata_qid": "Q3",
                    "name": "Director",
                    "source_url": "https://www.wikidata.org/wiki/Q3",
                }
            ],
            [
                {
                    "title_id": "wikidata:Q1",
                    "genre_id": "wikidata:Q2",
                    "source_property": "P136",
                    "source_url": "https://www.wikidata.org/wiki/Q1",
                }
            ],
            [
                {
                    "title_id": "wikidata:Q1",
                    "person_id": "wikidata:Q3",
                    "role": "director",
                    "source_property": "P57",
                    "source_url": "https://www.wikidata.org/wiki/Q1",
                }
            ],
        )

    def attestation(self, graph):
        return {
            "global_materialization_sha256": repartition.materialization_fingerprint(graph),
            "totals": {
                "candidate_titles": 1,
                "genres": 1,
                "people": 1,
                "emitted_genre_relations": 1,
                "emitted_credit_relations": 1,
            },
        }

    def test_exact_reviewed_graph_verifies(self):
        graph = self.graph()
        result = module.verify_graph(graph, self.attestation(graph))
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["production_mutation"], False)
        self.assertEqual(result["counts"]["candidate_titles"], 1)
        self.assertEqual(result["orphan_genre_relations"], 0)
        self.assertEqual(result["orphan_credit_relations"], 0)
        self.assertEqual(result["invalid_genre_provenance"], 0)
        self.assertEqual(result["invalid_credit_provenance"], 0)

    def test_changed_relationship_fails_graph_hash(self):
        graph = self.graph()
        attestation = self.attestation(graph)
        graph["title_credit_rows"][0]["person_id"] = "wikidata:Q4"
        with self.assertRaisesRegex(ValueError, "graph mismatch"):
            module.verify_graph(graph, attestation)

    def test_count_attestation_mismatch_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        attestation = self.attestation(graph)
        attestation["totals"]["candidate_titles"] = 2
        with self.assertRaisesRegex(ValueError, "normalized counts mismatch"):
            module.verify_graph(graph, attestation)

    def test_invalid_credit_provenance_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_credit_rows"][0]["source_property"] = "P161"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "invalid recommendation provenance"):
            module.verify_graph(graph, attestation)

    def test_invalid_genre_provenance_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_genre_rows"][0]["source_property"] = "P31"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "invalid recommendation provenance"):
            module.verify_graph(graph, attestation)

    def test_orphan_genre_relationship_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_genre_rows"][0]["genre_id"] = "wikidata:Q999"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "orphan relationships"):
            module.verify_graph(graph, attestation)

    def test_orphan_credit_relationship_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_credit_rows"][0]["person_id"] = "wikidata:Q999"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "orphan relationships"):
            module.verify_graph(graph, attestation)

    def test_invalid_media_type_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_rows"][0]["media_type"] = "film"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "invalid recommendation media type"):
            module.verify_graph(graph, attestation)

    def test_invalid_title_qid_fails_even_when_graph_hash_matches(self):
        graph = self.graph()
        graph["title_rows"][0]["wikidata_qid"] = "not-a-qid"
        attestation = self.attestation(graph)
        with self.assertRaisesRegex(ValueError, "invalid recommendation title QID"):
            module.verify_graph(graph, attestation)

    def test_database_only_timestamp_noise_is_not_part_of_reviewed_graph(self):
        graph = self.graph()

        def noisy(rows):
            return [
                {
                    **row,
                    "created_at": "2026-09-28T00:00:00Z",
                    "updated_at": "2026-09-28T01:00:00Z",
                }
                for row in rows
            ]

        recanonicalized = module.canonical_production_graph(
            noisy(graph["title_rows"]),
            noisy(graph["genre_rows"]),
            noisy(graph["people_rows"]),
            noisy(graph["title_genre_rows"]),
            noisy(graph["title_credit_rows"]),
        )
        self.assertEqual(recanonicalized, graph)
        self.assertEqual(
            repartition.materialization_fingerprint(recanonicalized),
            repartition.materialization_fingerprint(graph),
        )


if __name__ == "__main__":
    unittest.main()
