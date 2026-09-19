import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/p1-reviewed-source-identity-cleanup.yml"


class P1ReviewedSourceCleanupContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_cleanup_is_manual_and_explicit_only(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("schedule:", self.workflow)
        self.assertIn("apply_cleanup", self.workflow)
        self.assertIn("inputs.apply_cleanup == true", self.workflow)
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)

    def test_cleanup_is_bound_to_reviewed_projection(self):
        self.assertIn(
            'EXPECTED_PROJECTION_SHA256: "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"',
            self.workflow,
        )
        self.assertIn('EXPECTED_CANDIDATES: "16380"', self.workflow)
        self.assertIn("P1_SOURCE_CLEANUP_PROJECTION_INVARIANT", self.workflow)

    def test_exact_three_noncanonical_rows_are_targeted(self):
        for value in ("wd-Q3049630", "series-wd-Q3049630", "wd-Q3146368"):
            self.assertIn(value, self.workflow)
        self.assertIn("series-wd-Q3146368", self.workflow)
        self.assertIn("canonical Series retention mismatch", self.workflow)
        self.assertEqual(self.workflow.count("DELETE FROM "), 3)

    def test_cleanup_requires_exact_controller_owned_quota_guard(self):
        self.assertIn("quota_guard_token", self.workflow)
        self.assertIn("^[0-9]+:cleanup$", self.workflow)
        self.assertIn("recommendation_materialization_daily_guard", self.workflow)
        self.assertIn("cleanup UTC-day quota guard ownership mismatch", self.workflow)
        self.assertIn("P1_SOURCE_CLEANUP_QUOTA_GUARD_VERIFIED", self.workflow)

    def test_pre_and_post_state_are_fail_closed(self):
        self.assertIn("P1_SOURCE_CLEANUP_PRESTATE_EXACT", self.workflow)
        self.assertIn("P1_SOURCE_CLEANUP_POSTSTATE_EXACT", self.workflow)
        self.assertIn("unexpected Movie cleanup pre-state", self.workflow)
        self.assertIn("unexpected catalogue cleanup pre-state", self.workflow)
        self.assertIn("unexpected Series cleanup pre-state", self.workflow)


if __name__ == "__main__":
    unittest.main()
