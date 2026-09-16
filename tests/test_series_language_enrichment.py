import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import enrich_series_languages as module


def language_claim(qid, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": {"entity-type": "item", "id": qid}},
        },
    }


class SeriesLanguageEnrichmentTests(unittest.TestCase):
    def test_candidates_require_unknown_language_and_valid_qid(self):
        rows = [
            {"id": "s1", "wikidata_qid": "Q1", "language_name": "Unknown"},
            {"id": "s2", "wikidata_qid": "Q2", "language_name": "Telugu"},
            {"id": "s3", "wikidata_qid": None, "language_name": "Unknown"},
            {"id": "s4", "wikidata_qid": "bad", "language_name": "Unknown"},
        ]
        selected = module.select_candidates(rows, 10)
        self.assertEqual([row["id"] for row in selected], ["s1"])

    def test_qid_shards_are_stable_and_disjoint(self):
        rows = [
            {"id": f"s{qid}", "wikidata_qid": f"Q{qid}", "language_name": "Unknown"}
            for qid in range(1, 9)
        ]
        shard0 = module.select_candidates(rows, 10, shard_index=0, shard_count=2)
        shard1 = module.select_candidates(rows, 10, shard_index=1, shard_count=2)
        self.assertEqual([row["wikidata_qid"] for row in shard0], ["Q2", "Q4", "Q6", "Q8"])
        self.assertEqual([row["wikidata_qid"] for row in shard1], ["Q1", "Q3", "Q5", "Q7"])
        self.assertFalse({row["id"] for row in shard0} & {row["id"] for row in shard1})

    def test_invalid_shard_index_is_rejected(self):
        with self.assertRaises(ValueError):
            module.select_candidates([], 10, shard_index=8, shard_count=8)

    def test_single_p364_claim_resolves(self):
        entity = {"claims": {"P364": [language_claim("Q1860")]}}
        self.assertEqual(module.claim_language_qids(entity), ("resolved", "Q1860"))

    def test_multiple_normal_languages_remain_ambiguous(self):
        entity = {"claims": {"P364": [language_claim("Q1860"), language_claim("Q809")]}}
        self.assertEqual(module.claim_language_qids(entity), ("ambiguous", None))

    def test_unique_preferred_language_wins_over_normal_claim(self):
        entity = {
            "claims": {
                "P364": [
                    language_claim("Q1860", rank="normal"),
                    language_claim("Q809", rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_language_qids(entity), ("resolved", "Q809"))

    def test_deprecated_claim_is_ignored(self):
        entity = {"claims": {"P364": [language_claim("Q1860", rank="deprecated")]}}
        self.assertEqual(module.claim_language_qids(entity), ("missing", None))

    def test_build_enrichment_requires_resolved_label(self):
        candidates = [
            {"id": "series-wd-Q10", "wikidata_qid": "Q10", "title": "Example", "language_name": "Unknown"}
        ]
        entities = {"Q10": {"claims": {"P364": [language_claim("Q809")]}}}
        report = module.build_enrichment(candidates, entities, {"Q809": "Polish"})
        self.assertEqual(report["update_count"], 1)
        self.assertEqual(report["updates"][0]["language"], "Polish")
        self.assertEqual(report["updates"][0]["language_source"], "wikidata:P364")

    def test_sql_never_overwrites_resolved_language(self):
        report = {
            "updates": [
                {
                    "id": "series-wd-Q10",
                    "wikidata_qid": "Q10",
                    "language": "Telugu",
                    "language_source": "wikidata:P364",
                    "language_source_url": "https://www.wikidata.org/wiki/Q10",
                }
            ]
        }
        sql = module.build_sql(report)
        self.assertIn("UPDATE series_titles", sql)
        self.assertIn("wikidata_qid='Q10'", sql)
        self.assertIn("LOWER(language_name)='unknown'", sql)
        self.assertIn("language_source='wikidata:P364'", sql)
        self.assertNotIn("country_code", sql)

    def test_wikidata_request_retries_429_with_retry_after_and_get(self):
        rate_limit = urllib.error.HTTPError(
            "https://www.wikidata.org/w/api.php",
            429,
            "Too Many Requests",
            {"Retry-After": "7"},
            None,
        )
        with mock.patch.object(
            module.base,
            "request_json",
            side_effect=[rate_limit, {"entities": {}}],
        ) as request_json, mock.patch.object(module.time, "sleep") as sleep:
            payload = module.request_wikidata({"action": "wbgetentities", "ids": "Q1"})

        self.assertEqual(payload, {"entities": {}})
        self.assertEqual(request_json.call_count, 2)
        called_params = request_json.call_args_list[0].args[1]
        self.assertEqual(called_params["maxlag"], "5")
        self.assertFalse(request_json.call_args_list[0].kwargs["post"])
        sleep.assert_called_once_with(7)

    def test_wikidata_request_retries_http_200_maxlag_payload(self):
        with mock.patch.object(
            module.base,
            "request_json",
            side_effect=[
                {"error": {"code": "maxlag", "lag": 7, "info": "Waiting for database replication lag"}},
                {"entities": {}},
            ],
        ) as request_json, mock.patch.object(module.time, "sleep") as sleep:
            payload = module.request_wikidata({"action": "wbgetentities", "ids": "Q1"})

        self.assertEqual(payload, {"entities": {}})
        self.assertEqual(request_json.call_count, 2)
        sleep.assert_called_once_with(8)

    def test_non_transient_wikidata_api_error_never_becomes_missing_metadata(self):
        with mock.patch.object(
            module.base,
            "request_json",
            return_value={"error": {"code": "badvalue", "info": "Invalid ids parameter"}},
        ), mock.patch.object(module.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "Wikidata API error badvalue"):
                module.request_wikidata({"action": "wbgetentities", "ids": "Q1"})
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
