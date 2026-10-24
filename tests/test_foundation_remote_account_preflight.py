"""Offline negative tests for remote Cloudflare D1 preflight (zero Cloudflare calls)."""
import unittest
from scripts.foundation_remote_account_preflight import (
    assess, inspect_graphql, inspect_list, MIN_CANARY_WRITE_HEADROOM
)

DAY = "2026-10-23"
def db(name, last):
    return {"name": name, "uuid": f"00000000-0000-4000-8000-{last:012d}"}

def analytics(rows_read=200, rows_written=500, day=DAY):
    return {
        "data": {
            "viewer": {
                "accounts": [{
                    "d1AnalyticsAdaptiveGroups": [{
                        "dimensions": {
                            "date": day,
                            "databaseId": "00000000-0000-4000-8000-000000000001",
                        },
                        "sum": {
                            "rowsRead": rows_read,
                            "rowsWritten": rows_written,
                        },
                    }]
                }]
            }
        }
    }


class PreflightTests(unittest.TestCase):
    def test_valid_read_only_capacity_and_usage(self):
        result = assess([db("cinema-and-series", 1),
                         db("another-database", 2)], analytics(), DAY)
        self.assertEqual(result["database_count"], 2)
        self.assertTrue(result["canary_capacity_indicated_not_authorized"])
        self.assertFalse(result["full_staging_authorized"])
        self.assertFalse(result["production_corrections_authorized"])
        self.assertFalse(result["remote_staging_database_created"])
        self.assertEqual(result["production_d1_writes"], 0)

    def test_unknown_or_duplicate_production_identity_fails(self):
        for bad in ([db("different", 1)],
                    [db("cinema-and-series", 1), db("cinema-and-series", 2)],
                    [db("cinema-and-series", 1), db("other", 1)]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    inspect_list(bad)

    def test_old_orphan_qa_database_forces_manual_cleanup(self):
        with self.assertRaisesRegex(ValueError, "staging D1"):
            inspect_list([db("cinema-and-series", 1),
                          db("foundation-v2-qa-39900000-1", 2)])

    def test_not_enough_database_slots_blocks_creating_another(self):
        names = [db("cinema-and-series", 1)]
        names += [db(f"another-{n}", n + 1) for n in range(8)]
        with self.assertRaisesRegex(ValueError, "slots"):
            inspect_list(names)

    def test_missing_account_analytics_and_errors_fail_closed(self):
        for bad in ({}, {"errors": [{"message": "denied"}]}, {
            "data": {"viewer": {"accounts": []}}
        }):
            with self.subTest(payload=bad):
                with self.assertRaises(ValueError):
                    inspect_graphql(bad, DAY)

    def test_an_empty_usage_day_does_not_infer_positive_remaining_budget(self):
        v = {"data": {"viewer": {"accounts": [
            {"d1AnalyticsAdaptiveGroups": []}
        ]}}}
        result = inspect_graphql(v, DAY)
        self.assertTrue(result["usage_data_empty"])
        self.assertFalse(result["reported_usage_headroom_sufficient"])
        self.assertEqual(result["quota_status"], "usage_unverified")
        self.assertEqual(result["quota_status_reason"], "no_current_utc_day_usage_groups")
        self.assertIsNone(result["free_rows_written_remaining_estimate"])
        self.assertIsNone(result["free_rows_read_remaining_estimate"])
        self.assertIsNone(result["account_rows_written_reported"])
        self.assertIsNone(result["reported_daily_write_limit_reached"])
        self.assertFalse(assess([db("cinema-and-series",1)], v, DAY)
                         ["canary_capacity_indicated_not_authorized"])

    def test_quota_nearly_exhausted_rejects_canary_readiness(self):
        value = inspect_graphql(analytics(rows_written=100000 -
                                                  MIN_CANARY_WRITE_HEADROOM + 1), DAY)
        self.assertFalse(value["reported_usage_headroom_sufficient"])

    def test_quota_status_reports_low_headroom_without_claiming_exhaustion(self):
        near=inspect_graphql(analytics(rows_written=70000),DAY)
        self.assertEqual(near["quota_status"],"reported_headroom_insufficient")
        self.assertEqual(near["free_rows_written_remaining_estimate"],30000)
        self.assertFalse(near["reported_daily_write_limit_reached"])
        exhausted=inspect_graphql(analytics(rows_written=100000),DAY)
        self.assertEqual(exhausted["quota_status"],"reported_headroom_insufficient")
        self.assertEqual(exhausted["free_rows_written_remaining_estimate"],0)
        self.assertTrue(exhausted["reported_daily_write_limit_reached"])
        self.assertFalse(exhausted["reported_usage_headroom_sufficient"])

    def test_sufficient_analytics_is_not_live_quota_authorization(self):
        r=assess([db("cinema-and-series",1)],analytics(),DAY)
        self.assertEqual(r["quota_status"],"reported_headroom_sufficient")
        self.assertEqual(r["free_rows_written_remaining_estimate"],99500)
        self.assertEqual(r["usage_evidence_scope"],
                         "account_d1_graphql_daily_groups_not_realtime")
        self.assertFalse(r["full_staging_authorized"])
        self.assertFalse(r["production_corrections_authorized"])

    def test_multiple_database_usage_groups_are_aggregated(self):
        sample=analytics(rows_read=123,rows_written=401)
        sample["data"]["viewer"]["accounts"][0]["d1AnalyticsAdaptiveGroups"].append(
            {"dimensions":{"date":DAY,"databaseId":
                "00000000-0000-4000-8000-000000000002"},
             "sum":{"rowsRead":44,"rowsWritten":98}})
        r=inspect_graphql(sample,DAY)
        self.assertEqual(r["account_rows_read_reported"],167)
        self.assertEqual(r["account_rows_written_reported"],499)
        self.assertEqual(r["free_rows_written_remaining_estimate"],99501)

    def test_empty_new_utc_day_is_not_reported_as_exhausted(self):
        sample={"data":{"viewer":{"accounts":[{"d1AnalyticsAdaptiveGroups":[]}]}}}
        r=inspect_graphql(sample,"2026-10-24")
        self.assertEqual(r["quota_status"],"usage_unverified")
        self.assertIsNone(r["reported_daily_write_limit_reached"])
        self.assertIsNone(r["free_rows_written_remaining_estimate"])

    def test_wrong_utc_day_or_truncated_groups_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "UTC day"):
            inspect_graphql(analytics(day="2026-10-22"), DAY)
        with self.assertRaisesRegex(ValueError, "truncated"):
            v = analytics()
            v["data"]["viewer"]["accounts"][0]["d1AnalyticsAdaptiveGroups"] = [
                v["data"]["viewer"]["accounts"][0]["d1AnalyticsAdaptiveGroups"][0]
            ] * 10000
            inspect_graphql(v, DAY)

    def test_negative_and_non_integer_usage_rejected(self):
        for value in (-1, 1.5, None, True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "rows metric"):
                    inspect_graphql(analytics(rows_written=value), DAY)


if __name__ == "__main__":
    unittest.main()
