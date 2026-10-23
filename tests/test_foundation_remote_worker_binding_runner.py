"""Offline safety tests for the disposable remote Worker D1-binding runner."""
import unittest
from pathlib import Path
from scripts.foundation_remote_worker_binding_runner import (
    safe_config, parse_migrations, PRODUCTION, MIGRATIONS,
    safe_failure_diagnostic, stage_log, seed_schema_only,
    assert_remote_scratch_config, ProbePhaseFailure
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
        self.assertTrue(result["preview_urls"])
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

    def test_manual_canary_trigger_guard_checks_only_yaml_header(self):
        workflow = Path(
            ".github/workflows/foundation-remote-worker-binding-canary.yml"
        ).read_text(encoding="utf-8")
        header = workflow.split("permissions:", 1)[0]
        # The trigger is manual. Text inside the shell validation script
        # must not become a false 'push' trigger.
        self.assertIn("workflow_dispatch:", header)
        self.assertFalse(any(line.strip() == "push:"
                             for line in header.splitlines()))
        self.assertIn("header=wf.split(", workflow)
        self.assertIn("YES_SCRATCH_D1_ONLY", header)
        self.assertIn("Always independently clean up exact temporary scratch D1",
                      workflow)

    def test_preview_readiness_requires_authenticated_real_scratch_health(self):
        from scripts.foundation_remote_worker_binding_runner import (
            HEALTH_ENDPOINT, HEALTH_SCHEMA
        )
        self.assertEqual(HEALTH_ENDPOINT,
                         "http://127.0.0.1:8787/__foundation_staging_probe_health")
        self.assertEqual(HEALTH_SCHEMA,"foundation-v2-worker-binding-health-v1")
        source=Path("scripts/foundation_remote_worker_binding_runner.py").read_text()
        self.assertIn('"x-foundation-ephemeral-token": token', source)
        self.assertIn('data.get("scratch_binding_verified") is True', source)
        self.assertIn('data.get("scratch_write_performed") is False', source)
        self.assertNotIn("if exc.code == 404:\\n                    ready = True", source)

    def test_safe_diagnostic_redacts_exception_messages_and_credentials(self):
        secret = "private-token-and-a-database-uuid-never-log-this"
        result = safe_failure_diagnostic(
            "schema_initialize", True, ValueError(secret))
        import json
        serialized = json.dumps(result)
        self.assertNotIn(secret, serialized)
        self.assertNotIn("uuid", serialized.lower())
        self.assertEqual(result["outcome"], "not_verified")
        self.assertEqual(result["last_stage"], "schema_initialize")
        self.assertTrue(result["exact_scratch_cleanup_confirmed"])
        self.assertFalse(result["remote_worker_binding_passed"])
        self.assertFalse(result["production_corrections_authorized"])

    def test_categorical_diagnostics_disallow_freeform_log_data(self):
        with self.assertRaisesRegex(ValueError, "diagnostic"):
            safe_failure_diagnostic("token=SECRET", False, RuntimeError("x"))
        with self.assertRaisesRegex(ValueError, "diagnostic"):
            stage_log("uuid=PRIVATE")
        from subprocess import TimeoutExpired
        result = safe_failure_diagnostic(
            "preview_start", False, TimeoutExpired("wrangler", 5))
        self.assertEqual(result["failure_category"], "timeout")
        self.assertFalse(result["exact_scratch_cleanup_confirmed"])

    def test_batched_trusted_schema_uses_one_remote_d1_invocation(self):
        import json
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from types import SimpleNamespace
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private-wrangler.qa.jsonc"
            path.write_text(json.dumps(safe_config(QA, STAGE, PROD, TOKEN)))
            self.assertIsNone(assert_remote_scratch_config(QA, path))
            calls = []
            def intercepted(argv, **options):
                self.assertEqual(argv[:4],
                                 ["npx", "wrangler", "d1", "execute"])
                self.assertEqual(argv[4], QA)
                self.assertIn("--remote", argv)
                self.assertIn("--file", argv)
                self.assertNotIn(PRODUCTION, argv)
                script = Path(argv[argv.index("--file")+1])
                source = script.read_text()
                self.assertIn("CREATE TABLE IF NOT EXISTS catalogue_titles", source)
                self.assertIn("CREATE TABLE IF NOT EXISTS series_titles", source)
                self.assertIn("ALTER TABLE series_titles ADD COLUMN", source)
                self.assertNotIn("DROP TABLE", source.upper())
                self.assertNotIn(TOKEN, source)
                self.assertNotIn(PROD, source)
                calls.append(script)
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            with patch("scripts.foundation_remote_worker_binding_runner.subprocess.run",
                       side_effect=intercepted):
                seed_schema_only(QA, path)
            self.assertEqual(len(calls), 1)
            self.assertFalse(calls[0].exists())

    def test_unverified_scratch_uuid_cannot_run_any_remote_sql(self):
        import json
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-wrangler.qa.jsonc"
            bad = safe_config(QA, STAGE, PROD, TOKEN)
            bad["d1_databases"][0]["database_id"] = PROD
            path.write_text(json.dumps(bad))
            with patch("scripts.foundation_remote_worker_binding_runner.subprocess.run") as run:
                with self.assertRaisesRegex(ValueError, "identity"):
                    seed_schema_only(QA, path)
                run.assert_not_called()

    def test_schema_file_removed_after_remote_execution_failure(self):
        import json
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from types import SimpleNamespace
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "private-wrangler.qa.jsonc"
            path.write_text(json.dumps(safe_config(QA, STAGE, PROD, TOKEN)))
            with patch("scripts.foundation_remote_worker_binding_runner.subprocess.run",
                       return_value=SimpleNamespace(returncode=1, stdout="SECRET", stderr="SECRET")):
                with self.assertRaisesRegex(ValueError, "initialization failed"):
                    seed_schema_only(QA, path)
            self.assertEqual(list(Path(tmp).glob("foundation-only-schema-*.sql")), [])

    def test_failed_remote_phase_is_bounded_and_does_not_log_raw_errors(self):
        import json
        failed=ProbePhaseFailure("probe_film")
        self.assertEqual(failed.stage, "probe_film")
        self.assertNotIn(TOKEN, str(failed))
        result=safe_failure_diagnostic(failed.stage,True,failed)
        self.assertEqual(result["last_stage"],"probe_film")
        self.assertNotIn(TOKEN,json.dumps(result))
        with self.assertRaises(ValueError):
            ProbePhaseFailure("probe_SECRET_" + TOKEN)

    def test_trusted_film_and_series_qa_migrations_parse(self):
        self.assertEqual(len(MIGRATIONS),5)
        for file in MIGRATIONS:
            with self.subTest(file=file):
                statements=parse_migrations(Path(file))
                self.assertTrue(statements)
                self.assertFalse(any("DROP TABLE" in sql.upper() for sql in statements))


if __name__=="__main__":
    unittest.main()
