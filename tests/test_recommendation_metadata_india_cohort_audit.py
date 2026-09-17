import unittest

from scripts import recommendation_metadata_india_cohort_audit as cohort


def entity_with(**properties):
    claims = {}
    for prop, qids in properties.items():
        claims[prop] = [
            {
                "rank": "normal",
                "mainsnak": {
                    "snaktype": "value",
                    "datavalue": {"value": {"id": qid}},
                },
            }
            for qid in qids
        ]
    return {"claims": claims}


class RecommendationMetadataIndiaCohortAuditTests(unittest.TestCase):
    def test_normalize_language_accepts_case_insensitive_india_languages(self):
        self.assertEqual(cohort.normalize_language("telugu"), "Telugu")
        self.assertEqual(cohort.normalize_language(" MALAYALAM "), "Malayalam")
        self.assertEqual(cohort.normalize_language("English"), "Other/Unknown")

    def test_exact_movie_language_wins_over_catalogue_overlap(self):
        mapping = cohort.language_map(
            [{"wikidata_qid": "Q10", "language_name": "Telugu"}],
            [{"wikidata_qid": "Q10", "language_name": "Hindi"}],
            [],
        )
        self.assertEqual(mapping[("movie", "Q10")], "Telugu")

    def test_ready_requires_genre_and_people(self):
        candidates = [
            {"wikidata_qid": "Q10", "media_type": "movie"},
            {"wikidata_qid": "Q11", "media_type": "series"},
        ]
        entities = {
            "Q10": entity_with(P136=["Q1"], P57=["Q2"]),
            "Q11": entity_with(P136=["Q1"]),
        }
        languages = {("movie", "Q10"): "Telugu", ("series", "Q11"): "Telugu"}
        report = cohort.audit_cohorts(candidates, entities, languages)
        self.assertEqual(report["Telugu"]["titles"], 2)
        self.assertEqual(report["Telugu"]["ready"], 1)
        self.assertEqual(report["Telugu"]["movie_ready"], 1)
        self.assertEqual(report["Telugu"]["series_ready"], 0)
        self.assertEqual(report["Telugu"]["ready_percent"], 50.0)

    def test_series_creator_counts_as_people(self):
        candidates = [{"wikidata_qid": "Q20", "media_type": "series"}]
        entities = {"Q20": entity_with(P136=["Q1"], P170=["Q2"])}
        languages = {("series", "Q20"): "Tamil"}
        report = cohort.audit_cohorts(candidates, entities, languages)
        self.assertEqual(report["Tamil"]["ready"], 1)


if __name__ == "__main__":
    unittest.main()
