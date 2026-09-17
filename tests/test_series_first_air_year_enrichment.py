import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import enrich_series_first_air_year as module


def time_claim(year, *, rank="normal", precision=9, sign="+"):
    return {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {
                "value": {
                    "time": f"{sign}{year:04d}-00-00T00:00:00Z",
                    "precision": precision,
                    "before": 0,
                    "after": 0,
                    "timezone": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                }
            },
        },
    }


class SeriesFirstAirYearEnrichmentTests(unittest.TestCase):
    def test_partition_only_missing_year_rows_and_separates_missing_identity(self):
        rows = [
            {"id": "s1", "wikidata_qid": "Q1", "first_air_year": None},
            {"id": "s2", "wikidata_qid": "Q2", "first_air_year": 2020},
            {"id": "s3", "wikidata_qid": None, "first_air_year": None},
            {"id": "s4", "wikidata_qid": "bad", "first_air_year": ""},
        ]
        candidates, missing_identity, snapshot_count = module.partition_candidates(rows, 10)
        self.assertEqual(snapshot_count, 3)
        self.assertEqual([row["id"] for row in candidates], ["s1"])
        self.assertEqual([row["id"] for row in missing_identity], ["s3", "s4"])

    def test_year_precision_or_better_is_usable(self):
        value = time_claim(2018, precision=9)["mainsnak"]["datavalue"]["value"]
        self.assertEqual(module.extract_year_from_time_value(value), 2018)
        value["precision"] = 11
        self.assertEqual(module.extract_year_from_time_value(value), 2018)

    def test_below_year_precision_is_unusable(self):
        value = time_claim(2018, precision=8)["mainsnak"]["datavalue"]["value"]
        self.assertIsNone(module.extract_year_from_time_value(value))

    def test_out_of_schema_or_bce_year_is_unusable(self):
        old = time_claim(1899)["mainsnak"]["datavalue"]["value"]
        future = time_claim(2201)["mainsnak"]["datavalue"]["value"]
        bce = time_claim(2020, sign="-")["mainsnak"]["datavalue"]["value"]
        self.assertIsNone(module.extract_year_from_time_value(old))
        self.assertIsNone(module.extract_year_from_time_value(future))
        self.assertIsNone(module.extract_year_from_time_value(bce))

    def test_single_p580_year_resolves(self):
        entity = {"claims": {"P580": [time_claim(2017)]}}
        self.assertEqual(module.claim_first_air_year(entity), ("resolved", 2017))

    def test_duplicate_dates_in_same_year_resolve_to_year(self):
        entity = {"claims": {"P580": [time_claim(2017, precision=11), time_claim(2017, precision=9)]}}
        self.assertEqual(module.claim_first_air_year(entity), ("resolved", 2017))

    def test_multiple_normal_years_remain_ambiguous(self):
        entity = {"claims": {"P580": [time_claim(2017), time_claim(2018)]}}
        self.assertEqual(module.claim_first_air_year(entity), ("ambiguous", None))

    def test_unique_preferred_year_wins_over_normal_claim(self):
        entity = {
            "claims": {
                "P580": [
                    time_claim(2017, rank="normal"),
                    time_claim(2018, rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_first_air_year(entity), ("resolved", 2018))

    def test_unusable_preferred_claim_never_falls_back_silently(self):
        entity = {
            "claims": {
                "P580": [
                    time_claim(2017, rank="normal"),
                    time_claim(2018, rank="preferred", precision=8),
                ]
            }
        }
        self.assertEqual(module.claim_first_air_year(entity), ("unusable", None))

    def test_deprecated_claim_is_ignored(self):
        entity = {"claims": {"P580": [time_claim(2017, rank="deprecated")]}}
        self.assertEqual(module.claim_first_air_year(entity), ("missing", None))

    def test_build_enrichment_partitions_snapshot_exactly(self):
        candidates = [
            {"id": "s1", "wikidata_qid": "Q1", "title": "One", "first_air_year": None},
            {"id": "s2", "wikidata_qid": "Q2", "title": "Two", "first_air_year": None},
            {"id": "s3", "wikidata_qid": "Q3", "title": "Three", "first_air_year": None},
            {"id": "s4", "wikidata_qid": "Q4", "title": "Four", "first_air_year": None},
        ]
        missing_identity = [{"id": "s5", "wikidata_qid": None, "title": "Five", "first_air_year": None}]
        entities = {
            "Q1": {"claims": {"P580": [time_claim(2010)]}},
            "Q2": {"claims": {"P580": [time_claim(2011), time_claim(2012)]}},
            "Q3": {"claims": {}},
            "Q4": {"claims": {"P580": [time_claim(2013, precision=8)]}},
        }
        report = module.build_enrichment(candidates, missing_identity, 5, entities)
        self.assertEqual(report["snapshot_count"], 5)
        self.assertEqual(report["update_count"], 1)
        self.assertEqual(report["ambiguous_count"], 1)
        self.assertEqual(report["missing_claim_count"], 1)
        self.assertEqual(report["unusable_time_count"], 1)
        self.assertEqual(report["missing_identity_count"], 1)
        self.assertEqual(
            report["update_count"]
            + report["ambiguous_count"]
            + report["missing_claim_count"]
            + report["unusable_time_count"]
            + report["missing_identity_count"],
            report["snapshot_count"],
        )
        self.assertEqual(report["updates"][0]["first_air_year_source"], "wikidata:P580")

    def test_sql_never_overwrites_existing_year(self):
        report = {
            "updates": [
                {
                    "id": "series-wd-Q10",
                    "wikidata_qid": "Q10",
                    "first_air_year": 2019,
                    "first_air_year_source": "wikidata:P580",
                    "first_air_year_source_url": "https://www.wikidata.org/wiki/Q10",
                }
            ]
        }
        sql = module.build_sql(report)
        self.assertIn("UPDATE series_titles", sql)
        self.assertIn("first_air_year=2019", sql)
        self.assertIn("wikidata_qid='Q10'", sql)
        self.assertIn("first_air_year IS NULL", sql)
        self.assertIn("first_air_year_source='wikidata:P580'", sql)
        self.assertNotIn("language_name", sql)

    def test_wikidata_request_retries_429_and_uses_get(self):
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

    def test_http_200_maxlag_payload_is_retried(self):
        with mock.patch.object(
            module.base,
            "request_json",
            side_effect=[
                {"error": {"code": "maxlag", "lag": 7, "info": "replication lag"}},
                {"entities": {}},
            ],
        ) as request_json, mock.patch.object(module.time, "sleep") as sleep:
            payload = module.request_wikidata({"action": "wbgetentities", "ids": "Q1"})

        self.assertEqual(payload, {"entities": {}})
        self.assertEqual(request_json.call_count, 2)
        sleep.assert_called_once_with(8)

    def test_non_transient_api_error_never_becomes_missing_metadata(self):
        with mock.patch.object(
            module.base,
            "request_json",
            return_value={"error": {"code": "badvalue", "info": "Invalid ids"}},
        ), mock.patch.object(module.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "Wikidata API error badvalue"):
                module.request_wikidata({"action": "wbgetentities", "ids": "Q1"})
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
