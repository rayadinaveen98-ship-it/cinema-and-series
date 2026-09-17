import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import enrich_series_native_titles as module


def native_claim(text, language="te", rank="normal", snaktype="value"):
    mainsnak = {"snaktype": snaktype}
    if snaktype == "value":
        mainsnak["datavalue"] = {
            "value": {"text": text, "language": language},
            "type": "monolingualtext",
        }
    return {"rank": rank, "mainsnak": mainsnak}


class SeriesNativeTitleEnrichmentTests(unittest.TestCase):
    def test_candidates_require_missing_title_and_valid_qid(self):
        rows = [
            {"id": "s1", "wikidata_qid": "Q1", "native_title": None},
            {"id": "s2", "wikidata_qid": "Q2", "native_title": "Already"},
            {"id": "s3", "wikidata_qid": None, "native_title": None},
            {"id": "s4", "wikidata_qid": "bad", "native_title": ""},
        ]
        selected = module.select_candidates(rows, 10)
        self.assertEqual([row["id"] for row in selected], ["s1"])

    def test_qid_shards_are_stable_and_disjoint(self):
        rows = [
            {"id": f"s{qid}", "wikidata_qid": f"Q{qid}", "native_title": None}
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

    def test_single_p1705_claim_resolves_with_language_code(self):
        entity = {"claims": {"P1705": [native_claim("ఆర్ఆర్ఆర్", "te")]}}
        self.assertEqual(module.claim_native_title(entity), ("resolved", ("ఆర్ఆర్ఆర్", "te")))

    def test_duplicate_identical_claims_still_resolve(self):
        entity = {"claims": {"P1705": [native_claim("Example", "en"), native_claim("Example", "en")]}}
        self.assertEqual(module.claim_native_title(entity), ("resolved", ("Example", "en")))

    def test_multiple_distinct_native_labels_remain_ambiguous(self):
        entity = {"claims": {"P1705": [native_claim("One", "en"), native_claim("Uno", "es")]}}
        self.assertEqual(module.claim_native_title(entity), ("ambiguous", None))

    def test_unique_preferred_native_label_wins(self):
        entity = {
            "claims": {
                "P1705": [
                    native_claim("Normal", "en"),
                    native_claim("Preferred", "ko", rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_native_title(entity), ("resolved", ("Preferred", "ko")))

    def test_multiple_preferred_native_labels_are_ambiguous(self):
        entity = {
            "claims": {
                "P1705": [
                    native_claim("One", "en", rank="preferred"),
                    native_claim("Two", "fr", rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_native_title(entity), ("ambiguous", None))

    def test_unusable_preferred_claim_never_falls_back_to_normal(self):
        entity = {
            "claims": {
                "P1705": [
                    native_claim("Normal", "en"),
                    native_claim("", "te", rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_native_title(entity), ("unusable", None))

    def test_deprecated_claim_is_ignored(self):
        entity = {"claims": {"P1705": [native_claim("Old", "en", rank="deprecated")]}}
        self.assertEqual(module.claim_native_title(entity), ("missing", None))

    def test_missing_language_code_is_unusable(self):
        entity = {"claims": {"P1705": [native_claim("Title", "")]}}
        self.assertEqual(module.claim_native_title(entity), ("unusable", None))

    def test_build_enrichment_records_language_and_provenance(self):
        candidates = [{"id": "series-wd-Q10", "wikidata_qid": "Q10", "title": "Example", "native_title": None}]
        entities = {"Q10": {"claims": {"P1705": [native_claim("예시", "ko")]}}}
        report = module.build_enrichment(candidates, entities)
        self.assertEqual(report["update_count"], 1)
        self.assertEqual(report["updates"][0]["native_title"], "예시")
        self.assertEqual(report["updates"][0]["native_title_language_code"], "ko")
        self.assertEqual(report["updates"][0]["native_title_source"], "wikidata:P1705")

    def test_sql_never_overwrites_existing_native_title(self):
        report = {
            "updates": [
                {
                    "id": "series-wd-Q10",
                    "wikidata_qid": "Q10",
                    "native_title": "మూల శీర్షిక",
                    "native_title_language_code": "te",
                    "native_title_source": "wikidata:P1705",
                    "native_title_source_url": "https://www.wikidata.org/wiki/Q10",
                }
            ]
        }
        sql = module.build_sql(report)
        self.assertIn("UPDATE series_titles", sql)
        self.assertIn("wikidata_qid='Q10'", sql)
        self.assertIn("TRIM(native_title)=''", sql)
        self.assertIn("native_title_source='wikidata:P1705'", sql)
        self.assertIn("native_title_language_code='te'", sql)
        self.assertNotIn("language_name=", sql)

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
