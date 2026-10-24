"""Credential-free billing cross-check tests. No actual billing or D1 access."""
import io
import json
import unittest
from urllib.error import HTTPError, URLError

from scripts.foundation_d1_billing_usage_diagnostic import (
    SCHEMA, safe_result, inspect_billing_data, fetch_billing_data,
)

ACCOUNT = "a"*32
TOKEN = "private-token-never-log"
DAY = "2026-10-24"


def bill(service="D1 Rows Written", family="D1", day="2026-10-22",
         account=ACCOUNT):
    from datetime import datetime, timedelta, timezone
    start = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return {
        "BillingAccountId": account,
        "ServiceName": service,
        "ServiceFamilyName": family,
        "ChargePeriodStart": start.isoformat(),
        "ChargePeriodEnd": (start+timedelta(days=1)).isoformat(),
        "PricingQuantity": 4,
        "ConsumedUnit": "rows",
        "ContractedCost": 12345.67,
        "BillingAccountName": "SECRET_BILLING_ACCOUNT",
    }


def response(*rows):
    return {"success": True, "errors": [], "result": list(rows)}


class FakeHTTP:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, maximum):
        return self.payload[:maximum]


class BillingCrosscheckTests(unittest.TestCase):
    def test_empty_billing_records_are_not_zero_usage_or_quota_headroom(self):
        r=inspect_billing_data(response(),DAY,ACCOUNT)
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["status"],"billing_rows_absent")
        self.assertEqual(r["d1_billing_row_count"],0)
        self.assertFalse(r["full_daily_d1_write_allowance_known"])
        self.assertFalse(r["free_tier_quota_exhausted_proven"])
        self.assertFalse(r["current_quota_headroom_verified"])
        self.assertFalse(r["scratch_staging_authorized"])
        self.assertFalse(r["production_corrections_authorized"])

    def test_d1_historical_rows_counted_without_amounts_or_secrets(self):
        rows=response(bill(),bill("Workers Standard","Workers","2026-10-23"))
        result=inspect_billing_data(rows,DAY,ACCOUNT)
        self.assertEqual(result["status"],"historical_d1_billing_rows_visible")
        self.assertEqual(result["billing_row_count"],2)
        self.assertEqual(result["d1_billing_row_count"],1)
        self.assertEqual(result["most_recent_d1_charge_period_start_utc"],
                         "2026-10-22")
        s=json.dumps(result)
        self.assertNotIn(ACCOUNT,s)
        self.assertNotIn("SECRET_BILLING_ACCOUNT",s)
        self.assertNotIn("12345",s)
        self.assertFalse(result["current_quota_headroom_verified"])

    def test_non_d1_records_alone_are_not_d1_zero_usage(self):
        result=inspect_billing_data(
            response(bill("Workers Standard","Workers")),DAY,ACCOUNT)
        self.assertEqual(result["status"],"d1_rows_absent_in_billing")
        self.assertIsNone(result["most_recent_d1_charge_period_start_utc"])
        self.assertFalse(result["free_tier_quota_exhausted_proven"])

    def test_identifies_only_fixed_readonly_billing_endpoint(self):
        seen=[]
        def open_once(request,timeout):
            seen.append(request)
            self.assertEqual(timeout,30)
            self.assertEqual(request.get_method(),"GET")
            self.assertEqual(request.get_header("Authorization"),"Bearer "+TOKEN)
            self.assertIn("/accounts/"+ACCOUNT+"/billable-usage?",request.full_url)
            self.assertIn("from=2026-10-17",request.full_url)
            self.assertIn("to=2026-10-24",request.full_url)
            self.assertNotIn("/d1/",request.full_url)
            return FakeHTTP(response(bill()))
        result=fetch_billing_data(ACCOUNT,TOKEN,DAY,open_once)
        self.assertEqual(len(seen),1)
        self.assertEqual(result["status"],"historical_d1_billing_rows_visible")
        self.assertNotIn(TOKEN,json.dumps(result))

    def test_missing_billing_read_secret_never_calls_http(self):
        called=[]
        result=fetch_billing_data(ACCOUNT,"",DAY,lambda *a,**k: called.append(1))
        self.assertEqual(result["status"],"billing_token_not_configured")
        self.assertEqual(called,[])

    def test_billing_permission_error_never_logs_private_response(self):
        for code,status in [(401,"billing_permission_unavailable"),
                            (403,"billing_permission_unavailable"),
                            (429,"billing_api_unavailable"),
                            (500,"billing_api_unavailable")]:
            def deny(request,timeout):
                raise HTTPError(request.full_url,code,"SECRET",{},
                                io.BytesIO(b"SECRET_MESSAGE "+TOKEN.encode()))
            r=fetch_billing_data(ACCOUNT,TOKEN,DAY,deny)
            self.assertEqual(r["status"],status)
            self.assertNotIn(TOKEN,json.dumps(r))
            self.assertNotIn("SECRET",json.dumps(r))

    def test_malformed_wrong_account_duplicate_and_future_billing_rejected(self):
        cases=[
            {"success":False,"result":[]},
            {"success":True,"result":None},
            {"success":True,"errors":[{"message":"PRIVATE"}],"result":[]},
            response(bill(account="b"*32)),
            response(bill(day="2026-10-25")),
            response(bill(day="2026-10-01")),
            response({"ServiceName":"D1"}),
            response(*[bill()]*3001),
        ]
        for p in cases:
            with self.subTest(reason=str(p)[:70]):
                with self.assertRaises(ValueError):
                    inspect_billing_data(p,DAY,ACCOUNT)

    def test_network_exception_cannot_establish_quota_headroom(self):
        def offline(req, timeout):
            raise URLError("SECRET_HTTP")
        r=fetch_billing_data(ACCOUNT,TOKEN,DAY,offline)
        self.assertEqual(r["status"],"billing_response_unverified")
        self.assertFalse(r["scratch_staging_authorized"])

    def test_workflow_is_manual_only_and_never_reuses_d1_token(self):
        from pathlib import Path
        path=Path(".github/workflows/foundation-d1-billing-usage-diagnostic.yml")
        s=path.read_text()
        header=s.split("\npermissions:",1)[0]
        self.assertIn("workflow_dispatch:",header)
        self.assertNotIn("\n  push:",header)
        self.assertNotIn("\n  schedule:",header)
        self.assertIn("YES_BILLING_READ_ONLY",header)
        self.assertIn("secrets.CLOUDFLARE_BILLING_READ_TOKEN",s)
        self.assertNotIn("secrets.CLOUDFLARE_API_TOKEN",s)
        self.assertNotIn("wrangler d1 execute",s)
        self.assertNotIn("wrangler d1 create",s)


if __name__=="__main__":
    unittest.main()
