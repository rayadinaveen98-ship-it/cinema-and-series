"""No-credential D1 analytics freshness tests; never connect to production."""
import unittest
from scripts.foundation_remote_account_preflight import assess
from scripts.foundation_d1_analytics_freshness import (
    inspect_recent_analytics, QUERY, fetch_recent,
)

TODAY = "2026-10-24"
DBID = "00000000-0000-4000-8000-000000000001"


def account_dbs():
    return [{"name": "cinema-and-series", "uuid": DBID}]


def metrics(day, read=20, write=5, rq=2, wq=1, dbid=DBID):
    return {"dimensions": {"date": day, "databaseId": dbid},
            "sum": {"rowsRead": read, "rowsWritten": write,
                    "readQueries": rq, "writeQueries": wq}}


def payload(*groups):
    return {"data": {"viewer": {"accounts": [
        {"d1AnalyticsAdaptiveGroups": list(groups)}]}}}


def snapshot(*groups):
    return assess(account_dbs(), payload(*groups), TODAY)


class D1FreshnessTests(unittest.TestCase):
    def test_historical_usage_visible_but_today_empty_is_not_verified_quota(self):
        preflight = snapshot()
        report = inspect_recent_analytics(
            payload(metrics("2026-10-23", read=110, write=44),
                    metrics("2026-10-22", read=140, write=13)),
            TODAY, preflight)
        self.assertEqual(report["status"], "today_missing_historical_visible")
        self.assertFalse(report["current_day_groups_present"])
        self.assertTrue(report["prior_day_groups_present"])
        self.assertEqual(report["daily_group_totals"]["2026-10-23"]["rows_written"], 44)
        self.assertFalse(report["independent_realtime_quota_verified"])
        self.assertFalse(report["canary_or_production_write_authorized"])
        self.assertFalse(report["production_d1_sql_executed"])
        self.assertEqual(report["production_d1_writes"], 0)
        self.assertNotIn(DBID, str(report))

    def test_three_empty_days_still_do_not_prove_zero_usage(self):
        result = inspect_recent_analytics(payload(), TODAY, snapshot())
        self.assertEqual(result["status"], "all_three_days_missing")
        self.assertFalse(result["prior_day_groups_present"])
        self.assertFalse(result["current_day_groups_present"])
        self.assertFalse(result["independent_realtime_quota_verified"])

    def test_current_day_consistent_same_source_still_not_independent(self):
        preflight = snapshot(metrics(TODAY, 22, 7))
        recent = payload(metrics(TODAY, 22, 7), metrics("2026-10-23", 45, 20))
        result = inspect_recent_analytics(recent, TODAY, preflight)
        self.assertEqual(result["status"], "today_present_same_source_counts_agree")
        self.assertFalse(result["independent_realtime_quota_verified"])
        self.assertEqual(result["daily_group_totals"][TODAY]["write_queries"], 1)

    def test_inconsistent_today_snapshots_fail_evidence(self):
        for preflight, recent in [
            (snapshot(), payload(metrics(TODAY))),
            (snapshot(metrics(TODAY)), payload()),
            (snapshot(metrics(TODAY, 20, 5)), payload(metrics(TODAY, 20, 6))),
        ]:
            with self.subTest(preflight=preflight["usage_data_empty"]):
                x = inspect_recent_analytics(recent, TODAY, preflight)
                self.assertEqual(x["status"], "same_day_snapshots_inconsistent")
                self.assertFalse(x["canary_or_production_write_authorized"])

    def test_multiple_daily_database_groups_aggregate_without_ids(self):
        otherid = "00000000-0000-4000-8000-000000000002"
        snapshot_today = snapshot(metrics(TODAY, 15, 3),
                                  metrics(TODAY, 20, 4, dbid=otherid))
        observed = payload(metrics(TODAY, 15, 3),
                           metrics(TODAY, 20, 4, dbid=otherid))
        report = inspect_recent_analytics(observed, TODAY, snapshot_today)
        self.assertEqual(report["status"], "today_present_same_source_counts_agree")
        self.assertEqual(report["daily_group_totals"][TODAY]["rows_written"], 7)
        self.assertNotIn(DBID, str(report))
        self.assertNotIn(otherid, str(report))

    def test_reject_wrong_day_duplicate_uuid_and_invalid_metrics(self):
        cases = [
            payload(metrics("2026-10-21")),
            payload(metrics(TODAY), metrics(TODAY)),
            payload(metrics(TODAY, write=-1)),
            payload(metrics(TODAY, read=True)),
            payload(metrics(TODAY, rq=None)),
            payload(metrics(TODAY, dbid="not-a-d1-id")),
            {"errors": [{"message": "SECRET"}]},
            {"data": {"viewer": {"accounts": []}}},
            {"data": {"viewer": {"accounts": [
                {"d1AnalyticsAdaptiveGroups": [metrics(TODAY)] * 10000}]}}},
        ]
        for case in cases:
            with self.subTest(case=str(case)[:45]):
                with self.assertRaises(ValueError):
                    inspect_recent_analytics(case, TODAY, snapshot())

    def test_wrong_or_untrusted_preflight_rejected(self):
        data = snapshot()
        data["production_d1_writes"] = 1
        with self.assertRaises(ValueError):
            inspect_recent_analytics(payload(), TODAY, data)
        data = snapshot()
        data["utc_day"] = "2026-10-23"
        with self.assertRaises(ValueError):
            inspect_recent_analytics(payload(), TODAY, data)

    def test_http_query_uses_only_graphql_with_account_window(self):
        self.assertIn("d1AnalyticsAdaptiveGroups", QUERY)
        self.assertIn("date_geq: $start", QUERY)
        self.assertIn("date_leq: $end", QUERY)
        import inspect
        code = inspect.getsource(fetch_recent)
        self.assertIn("https://api.cloudflare.com/client/v4/graphql", code)
        self.assertNotIn("wrangler", code)
        self.assertNotIn("d1 execute", code)


if __name__ == "__main__":
    unittest.main()
