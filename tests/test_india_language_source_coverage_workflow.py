"""Guard continuous, source-only film-language coverage reporting."""
import unittest
from pathlib import Path


WORKFLOW = (Path(__file__).resolve().parents[1] / ".github/workflows"
            / "india-film-language-source-only.yml")


class SourceCoverageWorkflowTests(unittest.TestCase):
    def test_each_collection_audits_its_own_stage_and_checkpoint(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python scripts/accelerate_india_language_source.py", workflow)
        self.assertIn("--max-passes 8", workflow)
        accelerator = (WORKFLOW.parents[2] / "scripts/accelerate_india_language_source.py").read_text(encoding="utf-8")
        self.assertIn('selection="decade-balanced"', accelerator)
        self.assertIn("python scripts/audit_india_film_language_coverage.py", workflow)
        self.assertIn("--stage data/generated/india-language/film-stage.sqlite", workflow)
        self.assertIn("--checkpoint data/generated/india-language/checkpoint.json", workflow)
        self.assertIn("--out data/generated/india-language/coverage-report.json", workflow)
        self.assertIn("report[\"by_decade\"].items()", workflow)
        self.assertIn("report[\"held_for_review\"]", workflow)

        # Preserve a downloadable record without needing production database access.
        self.assertIn("data/generated/india-language/coverage-report.json", workflow)
        self.assertIn("report[\"d1_reads\"] == 0", workflow)
        self.assertIn("report[\"d1_writes\"] == 0", workflow)
        self.assertNotIn("wrangler d1", workflow.casefold())
        self.assertNotIn("CLOUDFLARE_API_TOKEN", workflow)


if __name__ == "__main__":
    unittest.main()
