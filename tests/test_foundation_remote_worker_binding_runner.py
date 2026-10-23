"""Offline safety tests for the disposable remote Worker D1-binding runner."""
import unittest
from pathlib import Path
from scripts.foundation_remote_worker_binding_runner import (
    safe_config, parse_migrations, PRODUCTION, MIGRATIONS
)

QA="foundation-v2-qa-39946487548-1"
STAGE="00000000-0000-4000-8000-000000000099"
PROD="00000000-0000-4000-8000-000000000001"
TOKEN="synthetic-offline-temporary-secret-token-with-40-chars"


class RemoteWorkerRunnerTest(unittest.TestCase):
    def test_safe_preview_binds_only_explicit_other_uuid(self):
        result=safe_config(QA,STAGE,PROD,TOKEN)
        self.assertEqual(result["d1_databases"][0]["database_id"],STAGE)
        self.assertEqual(result["d1_databases"][0]["database_name"],QA)
        self.assertEqual(result["main"],
                         str(Path("scripts/foundation_staging_worker_probe.mjs").resolve()))
        self.assertFalse(result["workers_dev"])
        self.assertEqual(result["vars"]["FOUNDATION_STAGE_UUID"],STAGE)
        self.assertEqual(result["vars"]["FOUNDATION_PRODUCTION_UUID"],PROD)
        self.assertEqual(result["compatibility_flags"],["nodejs_compat"])
        self.assertNotIn(PRODUCTION,result["d1_databases"][0]["database_name"])

    def test_production_name_and_uuid_are_rejected(self):
        for name,stage,prod in ((PRODUCTION,STAGE,PROD),
                                (QA,PROD,PROD),
                                ("not-a-staging-db",STAGE,PROD),
                                (QA,"invalid",PROD)):
            with self.subTest(name=name,stage=stage):
                with self.assertRaises(ValueError):
                    safe_config(name,stage,prod,TOKEN)

    def test_missing_ephemeral_secret_rejected(self):
        with self.assertRaisesRegex(ValueError,"token"):
            safe_config(QA,STAGE,PROD,"not-long-enough")

    def test_trusted_film_and_series_qa_migrations_parse(self):
        self.assertEqual(len(MIGRATIONS),5)
        for file in MIGRATIONS:
            with self.subTest(file=file):
                statements=parse_migrations(Path(file))
                self.assertTrue(statements)
                self.assertFalse(any("DROP TABLE" in sql.upper() for sql in statements))


if __name__=="__main__":
    unittest.main()
