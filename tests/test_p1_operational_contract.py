import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md"
DAILY = ROOT / ".github/workflows/p1-quota-safe-daily-resume.yml"
WRITER = ROOT / ".github/workflows/recommendation-metadata-production-write-v2.yml"
COORDINATOR = ROOT / ".github/workflows/p1-background-write-coordinator.yml"
MIGRATIONS = ROOT / "migrations"

EXPECTED_ANALYSIS_RUN_ID = "35252106776"
EXPECTED_FINGERPRINT = "4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448"
EXPECTED_CANDIDATES = "14115"
EXPECTED_GENRE_RELATIONS = "13689"
EXPECTED_CREDIT_RELATIONS = "58069"
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

    def test_daily_controller_and_writer_share_the_same_immutable_analysis_lock(self):
        for workflow in (self.daily, self.writer):
            self.assertIn(EXPECTED_ANALYSIS_RUN_ID, workflow)
            self.assertIn(EXPECTED_FINGERPRINT, workflow)

    def test_daily_controller_keeps_one_shard_below_the_hard_write_ceiling(self):
        self.assertIn('MAX_SHARD_ROWS_WRITTEN: "80000"', self.daily)
        self.assertIn('cron: "25 0 * * *"', self.daily)
        self.assertIn("recommendation_materialization_daily_guard", self.daily)
        self.assertIn("Unsafe materialization state detected", self.daily)
        self.assertIn("exceeds quota-safe ceiling", self.daily)

    def test_writer_cannot_bypass_daily_quota_guard(self):
        self.assertIn("quota_guard_run_id", self.writer)
        self.assertIn("write_shard requires a numeric quota_guard_run_id", self.writer)
        self.assertIn("recommendation_materialization_daily_guard", self.writer)
        self.assertIn("UTC-day quota guard ownership mismatch", self.writer)

    def test_final_verification_counts_are_locked(self):
        self.assertIn(f'EXPECTED_CANDIDATES: "{EXPECTED_CANDIDATES}"', self.writer)
        self.assertIn(f'EXPECTED_GENRE_RELATIONS: "{EXPECTED_GENRE_RELATIONS}"', self.writer)
        self.assertIn(f'EXPECTED_CREDIT_RELATIONS: "{EXPECTED_CREDIT_RELATIONS}"', self.writer)
        self.assertIn("P1_COMPLETE_RELATION_COUNTS_VERIFIED", self.writer)
        self.assertIn("S0", self.writer)
        self.assertIn("S1", self.writer)

    def test_daily_controller_auto_verifies_and_retires_only_after_success(self):
        self.assertIn(
            'FINAL_VERIFY_ARTIFACT_NAME: "recommendation-metadata-production-write-v2-verify_final-0"',
            self.daily,
        )
        self.assertIn("Dispatch final P1 verification", self.daily)
        self.assertIn("Retire P1 daily resume after successful final verification", self.daily)
        self.assertIn("steps.final_verify_state.outputs.verified == 'true'", self.daily)
        self.assertIn("p1-quota-safe-daily-resume.yml/disable", self.daily)

    def test_catalogue_mutators_are_paused_before_daily_p1_population(self):
        self.assertIn('cron: "5 0 * * *"', self.coordinator)
        self.assertIn('workflows: ["Recommendation Metadata Production Write V2"]', self.coordinator)
        self.assertIn("actions: write", self.coordinator)
        for workflow in PAUSED_CATALOGUE_WORKFLOWS:
            self.assertIn(workflow, self.coordinator)
        self.assertNotIn("youtube-monitor.yml\n", self.coordinator)
        self.assertNotIn("website-monitor.yml\n", self.coordinator)

    def test_catalogue_mutators_resume_only_after_successful_final_verification(self):
        self.assertIn(
            'FINAL_VERIFY_ARTIFACT_NAME: "recommendation-metadata-production-write-v2-verify_final-0"',
            self.coordinator,
        )
        self.assertIn('run.get("conclusion") == "success"', self.coordinator)
        self.assertIn('run.get("head_branch") == "main"', self.coordinator)
        self.assertIn(
            'run.get("path") == ".github/workflows/recommendation-metadata-production-write-v2.yml"',
            self.coordinator,
        )
        self.assertIn('action = "resume" if verified else "pause"', self.coordinator)
        self.assertIn("p1-background-write-coordinator.yml", self.coordinator)
        self.assertIn("/disable", self.coordinator)


if __name__ == "__main__":
    unittest.main()
