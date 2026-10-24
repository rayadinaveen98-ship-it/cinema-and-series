"""Offline tests for single fixed read-only D1 query: no Cloudflare requests."""
import io
import json
import unittest
from urllib.error import HTTPError
from scripts.foundation_d1_runtime_readonly_probe import (
    SQL, SCHEMA, current_probe_status,
)

DBID = "00000000-0000-4000-8000-000000000001"
PROD_DB = [{"name": "cinema-and-series", "uuid": DBID}]
ACCOUNT = "a" * 32
TOKEN = "private-never-log-this"


class FakeResponse:
    def __init__(self, raw):
        self._raw = raw
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return self._raw[:size]


def reply(read=1, write=0, changes=0, changed=False, rows=None):
    data = {"success": True, "errors": [], "result": [{
        "success": True,
        "meta": {"rows_read": read, "rows_written": write,
                 "changes": changes, "changed_db": changed},
        "results": [{"probe_ok": 1}] if rows is None else rows
    }]}
    return json.dumps(data).encode()


class SingleReadProbeTests(unittest.TestCase):
    def test_fixed_select_one_against_exact_production_uuid(self):
        self.assertEqual(SQL, "SELECT 1 AS probe_ok")
        requests = []
        def open_one(req, timeout):
            requests.append(req)
            self.assertEqual(timeout, 20)
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(json.loads(req.data), {"sql": "SELECT 1 AS probe_ok"})
            self.assertTrue(req.full_url.endswith("/d1/database/" + DBID + "/query"))
            self.assertEqual(req.get_header("Authorization"), "Bearer " + TOKEN)
            return FakeResponse(reply())
        status = current_probe_status(PROD_DB, ACCOUNT, TOKEN, open_one)
        self.assertEqual(len(requests), 1)
        self.assertEqual(status["schema"], SCHEMA)
        self.assertEqual(status["runtime_status"], "read_succeeded_no_write")
        self.assertTrue(status["independent_current_query_health_evidence"])
        self.assertFalse(status["independent_realtime_quota_headroom_verified"])
        self.assertIsNone(status["account_remaining_reads"])
        self.assertIsNone(status["account_remaining_writes"])
        self.assertFalse(status["scratch_creation_authorized"])
        self.assertFalse(status["production_corrections_authorized"])
        self.assertFalse(status["data_mutation_requested"])
        self.assertNotIn(DBID, json.dumps(status))
        self.assertNotIn(TOKEN, json.dumps(status))
        self.assertNotIn(ACCOUNT, json.dumps(status))

    def test_documented_daily_limit_errors_are_categorized_without_leaking(self):
        for message, expected in [
            ("Your account has exceeded D1's free tier daily row read limit.",
             "cloudflare_reported_daily_read_limit"),
            ("Your account has exceeded D1's free tier daily row write limit.",
             "cloudflare_reported_daily_write_limit"),
            ("SECRET_please_retry", "query_unverified"),
        ]:
            def open_limit(req, timeout):
                raise HTTPError(req.full_url, 400, "PRIVATE", {},
                                io.BytesIO((message+TOKEN).encode()))
            result = current_probe_status(PROD_DB, ACCOUNT, TOKEN, open_limit)
            self.assertEqual(result["runtime_status"], expected)
            self.assertFalse(result["query_succeeded"])
            self.assertFalse(result["scratch_creation_authorized"])
            self.assertNotIn(TOKEN, json.dumps(result))
            self.assertNotIn("PRIVATE", json.dumps(result))

    def test_reject_wrong_database_duplicate_and_scratch_orphan_before_http(self):
        for dbs in (
            [{"name": "not-production", "uuid": DBID}],
            PROD_DB + [{"name": "foundation-v2-qa-400000-1",
                        "uuid": "00000000-0000-4000-8000-000000000002"}],
            PROD_DB + PROD_DB,
        ):
            calls = []
            def open_never(req, timeout):
                calls.append(req)
                raise AssertionError("No HTTP query should be made")
            with self.assertRaises(ValueError):
                current_probe_status(dbs, ACCOUNT, TOKEN, open_never)
            self.assertEqual(calls, [])

    def test_reject_bad_account_identity_and_empty_token_before_http(self):
        for a, token in (("not-account", TOKEN), (ACCOUNT, ""), ("", TOKEN)):
            with self.assertRaises(ValueError):
                current_probe_status(PROD_DB, a, token,
                                     lambda req, timeout: None)

    def test_refuses_write_or_mutation_metadata_even_if_result_is_one(self):
        samples = [
            reply(write=1),
            reply(changes=1),
            reply(changed=True),
            reply(write=True),
            reply(read=10000),
            reply(rows=[{"probe_ok": 2}]),
            reply(rows=[{"probe_ok": 1}, {"probe_ok": 1}]),
            b"{invalid",
        ]
        for sample in samples:
            with self.subTest(sample=sample[:30]):
                status = current_probe_status(
                    PROD_DB, ACCOUNT, TOKEN,
                    lambda req, timeout: FakeResponse(sample))
                self.assertEqual(status["runtime_status"], "query_unverified")
                self.assertFalse(status["independent_current_query_health_evidence"])
                self.assertFalse(status["production_corrections_authorized"])

    def test_manual_only_workflow_requires_explicit_fixed_read_ack(self):
        from pathlib import Path
        s = Path(".github/workflows/foundation-d1-runtime-readonly-probe.yml").read_text()
        top = s.split("\npermissions:", 1)[0]
        self.assertIn("workflow_dispatch:", top)
        self.assertNotIn("\n  schedule:", top)
        self.assertNotIn("\n  push:", top)
        self.assertIn("YES_ONE_READ_ONLY_D1_QUERY", top)
        self.assertIn("foundation_d1_runtime_readonly_probe.py", s)
        self.assertNotIn("wrangler d1 execute", s)
        self.assertNotIn("wrangler d1 create", s)


if __name__ == "__main__":
    unittest.main()
