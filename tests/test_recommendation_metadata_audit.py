import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from scripts import recommendation_metadata_audit as audit


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


class RecommendationMetadataAuditTests(unittest.TestCase):
    def test_exact_movie_wins_over_catalogue_overlap(self):
        projection = audit.build_catalogue_projection(
            [{"id": "m1", "wikidata_qid": "Q10", "title": "Exact", "source_url": "https://a"}],
            [
                {"id": "c1", "wikidata_qid": "Q10", "title": "Year", "source_url": "https://b"},
                {"id": "c2", "wikidata_qid": "Q11", "title": "Only Year", "source_url": "https://c"},
            ],
            [],
        )
        rows = {row["wikidata_qid"]: row for row in projection["candidates"]}
        self.assertEqual(rows["Q10"]["source_table"], "movies")
        self.assertEqual(rows["Q11"]["source_table"], "catalogue_titles")
        self.assertEqual(projection["suppressed_catalogue_overlap_count"], 1)

    def test_cross_type_collision_is_excluded_and_reported(self):
        projection = audit.build_catalogue_projection(
            [{"id": "m1", "wikidata_qid": "Q10", "title": "Movie"}],
            [],
            [{"id": "s1", "wikidata_qid": "Q10", "title": "Series"}],
        )
        self.assertEqual(projection["cross_type_collision_qids"], ["Q10"])
        self.assertEqual(projection["candidates"], [])

    def test_invalid_qids_do_not_enter_projection(self):
        projection = audit.build_catalogue_projection(
            [{"id": "m1", "wikidata_qid": None, "title": "No ID"}],
            [{"id": "c1", "wikidata_qid": "not-a-qid", "title": "Bad"}],
            [{"id": "s1", "wikidata_qid": "Q12", "title": "Good"}],
        )
        self.assertEqual([row["wikidata_qid"] for row in projection["candidates"]], ["Q12"])

    def test_sharding_is_stable_by_numeric_qid(self):
        rows = [
            {"wikidata_qid": "Q10"},
            {"wikidata_qid": "Q11"},
            {"wikidata_qid": "Q12"},
            {"wikidata_qid": "Q13"},
        ]
        shard = audit.shard_candidates(rows, shard_index=1, shard_count=2)
        self.assertEqual([row["wikidata_qid"] for row in shard], ["Q11", "Q13"])

    def test_claim_entity_qids_dedupes_and_ignores_deprecated(self):
        entity = {
            "claims": {
                "P136": [
                    {"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q3"}}}},
                    {"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q3"}}}},
                    {"rank": "deprecated", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q4"}}}},
                ]
            }
        }
        values, unusable = audit.claim_entity_qids(entity, "P136")
        self.assertEqual(values, ["Q3"])
        self.assertEqual(unusable, 0)

    def test_claim_entity_qids_counts_unusable(self):
        entity = {
            "claims": {
                "P57": [
                    {"rank": "normal", "mainsnak": {"snaktype": "novalue"}},
                    {"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"value": "not-entity"}}},
                ]
            }
        }
        values, unusable = audit.claim_entity_qids(entity, "P57")
        self.assertEqual(values, [])
        self.assertEqual(unusable, 2)

    def test_movie_ready_requires_genre_and_any_people_signal(self):
        rows = [{"wikidata_qid": "Q100", "media_type": "movie", "display_title": "Ready"}]
        entities = {
            "Q100": entity_with(P136=["Q1"], P57=["Q2"], P161=[]),
        }
        report = audit.audit_candidates(rows, entities)
        self.assertEqual(report["media"]["movie"]["ready"], 1)
        self.assertEqual(report["relation_counts"]["P136"], 1)
        self.assertEqual(report["relation_counts"]["P57"], 1)

    def test_series_creator_is_counted_but_movie_creator_is_not(self):
        rows = [
            {"wikidata_qid": "Q100", "media_type": "series", "display_title": "Series"},
            {"wikidata_qid": "Q101", "media_type": "movie", "display_title": "Movie"},
        ]
        entities = {
            "Q100": entity_with(P136=["Q1"], P170=["Q2"]),
            "Q101": entity_with(P136=["Q1"], P170=["Q3"]),
        }
        report = audit.audit_candidates(rows, entities)
        self.assertEqual(report["media"]["series"]["ready"], 1)
        self.assertEqual(report["media"]["movie"]["ready"], 0)
        self.assertEqual(report["relation_counts"]["P170"], 1)

    def test_missing_entity_is_not_treated_as_missing_metadata(self):
        rows = [{"wikidata_qid": "Q100", "media_type": "movie", "display_title": "Missing"}]
        report = audit.audit_candidates(rows, {})
        self.assertEqual(report["missing_entity_count"], 1)
        self.assertEqual(report["media"]["movie"]["ready"], 0)

    def test_high_fanout_cast_is_visible(self):
        cast = [f"Q{i}" for i in range(1, 52)]
        rows = [{"wikidata_qid": "Q100", "media_type": "series", "display_title": "Many"}]
        report = audit.audit_candidates(rows, {"Q100": entity_with(P136=["Q999"], P161=cast)})
        self.assertEqual(report["high_fanout_cast_title_count"], 1)

    def test_load_d1_rows_supports_wrangler_json_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "snapshot.json"
            path.write_text(json.dumps([{"results": [{"id": "a"}]}, {"results": [{"id": "b"}]}]))
            self.assertEqual([row["id"] for row in audit.load_d1_rows(path)], ["a", "b"])

    @mock.patch.object(audit.base, "request_json")
    @mock.patch.object(audit.time, "sleep")
    def test_http_200_maxlag_is_retried(self, sleep, request_json):
        request_json.side_effect = [
            {"error": {"code": "maxlag", "info": "busy", "lag": 1}},
            {"entities": {}},
        ]
        result = audit.request_wikidata({"action": "wbgetentities"})
        self.assertEqual(result, {"entities": {}})
        self.assertEqual(request_json.call_count, 2)
        sleep.assert_called_once()

    @mock.patch.object(audit.base, "request_json")
    @mock.patch.object(audit.time, "sleep")
    def test_http_429_is_retried(self, sleep, request_json):
        error = urllib.error.HTTPError("https://example", 429, "rate", {}, None)
        request_json.side_effect = [error, {"entities": {}}]
        result = audit.request_wikidata({"action": "wbgetentities"})
        self.assertEqual(result, {"entities": {}})
        self.assertEqual(request_json.call_count, 2)


if __name__ == "__main__":
    unittest.main()
