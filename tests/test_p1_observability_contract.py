import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/p1-production-status-snapshot.yml"
BINDER = ROOT / "scripts/cloudflare_bind_existing_d1.py"
SNAPSHOT = ROOT / "scripts/p1_status_snapshot.py"


class P1ObservabilityContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.binder = BINDER.read_text(encoding="utf-8")
        self.snapshot = SNAPSHOT.read_text(encoding="utf-8")

    def test_status_workflow_is_read_only_and_restores_reviewed_v3_artifact(self):
        self.assertIn('ANALYSIS_RUN_ID: "35428784454"', self.workflow)
        self.assertIn('recommendation-metadata-materialization-v3-repartitioned', self.workflow)
        self.assertIn('EXPECTED_PROJECTION_SHA256: "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"', self.workflow)
        self.assertIn("scripts/cloudflare_bind_existing_d1.py", self.workflow)
        self.assertNotIn("cloudflare_bootstrap.py", self.workflow)
        self.assertNotIn("d1 migrations apply", self.workflow)
        self.assertNotIn("gh workflow run", self.workflow)

    def test_status_workflow_contains_no_d1_mutation_statements(self):
        upper = self.workflow.upper()
        for forbidden in (
            "INSERT INTO ",
            "UPDATE ",
            "DELETE FROM ",
            "DROP TABLE ",
            "ALTER TABLE ",
            "CREATE TABLE ",
        ):
            self.assertNotIn(forbidden, upper)

    def test_existing_d1_binder_cannot_create_database(self):
        self.assertIn('run_wrangler("d1", "list", "--json")', self.binder)
        self.assertNotIn('run_wrangler("d1", "create"', self.binder)
        self.assertIn("Expected exactly one existing D1 database", self.binder)

    def test_snapshot_uses_locked_operation_order_and_fail_closed_states(self):
        self.assertIn(
            'OPERATION_ORDER = ["topup", "1", "2", "3", "4", "5", "6", "7", "9", "10", "11", "12", "13", "14", "15"]',
            self.snapshot,
        )
        self.assertIn("unsafe_out_of_order", self.snapshot)
        self.assertIn("unsafe_partial", self.snapshot)
        self.assertIn("unsafe_overfilled", self.snapshot)
        self.assertIn("p1_exit_ready", self.snapshot)

    def test_status_runs_after_daily_controller_and_uploads_compact_artifact(self):
        self.assertIn('cron: "5 1 * * *"', self.workflow)
        self.assertIn("p1-production-status-${{ github.run_id }}", self.workflow)
        self.assertIn("p1-production-status.json", self.workflow)
        self.assertIn("p1-production-status.md", self.workflow)
        self.assertIn("GITHUB_STEP_SUMMARY", self.workflow)


if __name__ == "__main__":
    unittest.main()
