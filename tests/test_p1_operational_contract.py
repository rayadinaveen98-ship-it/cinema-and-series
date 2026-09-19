import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md"
DAILY = ROOT / ".github/workflows/p1-quota-safe-daily-resume.yml"
WRITER = ROOT / ".github/workflows/recommendation-metadata-production-write-v3.yml"
COORDINATOR = ROOT / ".github/workflows/p1-background-write-coordinator.yml"
CLEANUP = ROOT / ".github/workflows/p1-reviewed-source-identity-cleanup.yml"
YOUTUBE_MONITOR = ROOT / ".github/workflows/youtube-monitor.yml"
WEBSITE_MONITOR = ROOT / ".github/workflows/website-monitor.yml"
MIGRATIONS = ROOT / "migrations"

EXPECTED_ANALYSIS_RUN_ID = "35428784454"
EXPECTED_FINGERPRINT = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
EXPECTED_GRAPH = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"
EXPECTED_ATTESTATION = "8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986"
EXPECTED_CANDIDATES = "16380"
EXPECTED_GENRE_RELATIONS = "16489"
EXPECTED_CREDIT_RELATIONS = "70551"
PAUSED_CATALOGUE_WORKFLOWS = (
    "catalogue-growth-15k.yml",
    "series-catalogue.yml",
    "wikidata-backfill.yml",
    "wikidata-refresh.yml",
    "wikipedia-year-catalogue.yml",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class P1OperationalContractTests(unittest.TestCase):
    def setUp(self):
        self.status = read(STATUS)
        self.daily = read(DAILY)
        self.writer = read(WRITER)
        self.coordinator = read(COORDINATOR)
        self.cleanup = read(CLEANUP)
        self.youtube_monitor = read(YOUTUBE_MONITOR)
        self.website_monitor = read(WEBSITE_MONITOR)

    def test_p1_population_is_explicitly_in_progress(self):
        self.assertIn("PRODUCTION POPULATION IN PROGRESS", self.status)
        self.assertIn("P1 exits only after", self.status)

    def test_migration_numbering_is_frozen_through_0022_while_p1_is_active(self):
        numbered = []
        for path in MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.sql"):
            match = re.match(r"^(\d{4})_", path.name)
            if match:
                numbered.append((int(match.group(1)), path.name))
        self.assertTrue(numbered, "no numbered migrations found")
        highest = max(numbered)
        self.assertEqual(
            highest[0],
            22,
            f"P1 migration freeze violated by {highest[1]}; do not add 0023+ on main until P1 closes",
        )
        self.assertTrue((MIGRATIONS / "0021_recommendation_metadata_foundation.sql").exists())
        self.assertTrue((MIGRATIONS / "0022_recommendation_materialization_daily_guard.sql").exists())

    def test_daily_controller_writer_and_cleanup_share_v3_projection_lock(self):
        for workflow in (self.daily, self.writer, self.cleanup):
            self.assertIn(EXPECTED_FINGERPRINT, workflow)
        for workflow in (self.daily, self.writer):
            self.assertIn(EXPECTED_ANALYSIS_RUN_ID, workflow)
            self.assertIn(EXPECTED_GRAPH, workflow)
            self.assertIn(EXPECTED_ATTESTATION, workflow)

    def test_daily_controller_sequences_cleanup_before_recommendation_writes(self):
        self.assertIn("Determine reviewed source-cleanup state", self.daily)
        self.assertIn("Reserve UTC day for reviewed source cleanup", self.daily)
        self.assertIn("Dispatch reviewed source cleanup", self.daily)
        self.assertIn("steps.cleanup_state.outputs.state == 'complete'", self.daily)
        self.assertIn("topup 1 2 3 4 5 6 7 9 10 11 12 13 14 15", self.daily)

    def test_daily_controller_keeps_one_operation_below_hard_write_ceiling(self):
        self.assertIn('MAX_SHARD_ROWS_WRITTEN: "80000"', self.daily)
        self.assertIn('cron: "25 0 * * *"', self.daily)
        self.assertIn("recommendation_materialization_daily_guard", self.daily)
        self.assertIn("Unsafe materialization state detected", self.daily)
        self.assertIn("exceeds quota-safe ceiling", self.daily)

    def test_writer_cannot_bypass_operation_bound_daily_quota_guard(self):
        self.assertIn("quota_guard_token", self.writer)
        self.assertIn("quota_guard_token operation mismatch", self.writer)
        self.assertIn("recommendation_materialization_daily_guard", self.writer)
        self.assertIn("UTC-day V3 quota guard ownership mismatch", self.writer)
        self.assertIn("${GITHUB_RUN_ID}:${NEXT_OPERATION}", self.daily)

    def test_writer_uses_exact_attested_executable_and_graph(self):
        self.assertIn(f'EXPECTED_CANDIDATES: "{EXPECTED_CANDIDATES}"', self.writer)
        self.assertIn(f'EXPECTED_GENRE_RELATIONS: "{EXPECTED_GENRE_RELATIONS}"', self.writer)
        self.assertIn(f'EXPECTED_CREDIT_RELATIONS: "{EXPECTED_CREDIT_RELATIONS}"', self.writer)
        self.assertIn("selected executable SHA mismatch", self.writer)
        self.assertIn("verify_p1_v3_production.py", self.writer)
        self.assertIn("P1_V3_CATALOGUE_QUALITY_VERIFIED", self.writer)
        self.assertIn("S0", self.writer)
        self.assertIn("S1", self.writer)

    def test_daily_controller_auto_verifies_and_retires_only_after_success(self):
        self.assertIn(
            'FINAL_VERIFY_ARTIFACT_NAME: "recommendation-metadata-production-write-v3-verify_final-final"',
            self.daily,
        )
        self.assertIn("Dispatch final V3 verification", self.daily)
        self.assertIn("Retire V3 daily resume after successful final verification", self.daily)
        self.assertIn("steps.final_verify_state.outputs.verified == 'true'", self.daily)
        self.assertIn("p1-quota-safe-daily-resume.yml/disable", self.daily)

    def test_catalogue_mutators_are_paused_before_p1_population(self):
        self.assertIn('cron: "5 0 * * *"', self.coordinator)
        self.assertIn('workflows: ["Recommendation Metadata Production Write V3"]', self.coordinator)
        self.assertIn("actions: write", self.coordinator)
        for workflow in PAUSED_CATALOGUE_WORKFLOWS:
            self.assertIn(workflow, self.coordinator)
        self.assertNotIn("youtube-monitor.yml\n", self.coordinator)
        self.assertNotIn("website-monitor.yml\n", self.coordinator)

    def test_catalogue_pause_is_idempotent_when_workflows_are_already_disabled(self):
        self.assertIn("CURRENT_STATE=", self.coordinator)
        self.assertIn('if [[ "$CURRENT_STATE" != "$EXPECTED_STATE" ]]', self.coordinator)
        self.assertIn("already ${EXPECTED_STATE}; no state mutation needed", self.coordinator)
        self.assertIn("Workflow state verification failed", self.coordinator)

    def test_catalogue_mutators_resume_only_after_successful_v3_final_verification(self):
        self.assertIn(
            'FINAL_VERIFY_ARTIFACT_NAME: "recommendation-metadata-production-write-v3-verify_final-final"',
            self.coordinator,
        )
        self.assertIn("run.get('conclusion')=='success'", self.coordinator)
        self.assertIn("run.get('head_branch')=='main'", self.coordinator)
        self.assertIn(".github/workflows/recommendation-metadata-production-write-v3.yml", self.coordinator)
        self.assertIn("action='resume' if verified else 'pause'", self.coordinator)
        self.assertIn("p1-background-write-coordinator.yml", self.coordinator)
        self.assertIn("/disable", self.coordinator)

    def test_observation_monitors_preserve_artifacts_but_skip_d1_writes_on_p1_quota_day(self):
        for workflow in (self.youtube_monitor, self.website_monitor):
            self.assertIn("Respect P1 UTC-day D1 write reservation", workflow)
            self.assertIn("recommendation_materialization_daily_guard", workflow)
            self.assertIn("steps.p1_quota.outputs.reserved != 'true'", workflow)
            self.assertIn("Apply D1 migrations", workflow)
        self.assertIn("official-youtube-release-candidates", self.youtube_monitor)
        self.assertIn("official-website-release-candidates", self.website_monitor)
        self.assertIn("P1_D1_WRITE_QUOTA_RESERVED", self.youtube_monitor)
        self.assertIn("P1_D1_WRITE_QUOTA_RESERVED", self.website_monitor)


if __name__ == "__main__":
    unittest.main()
