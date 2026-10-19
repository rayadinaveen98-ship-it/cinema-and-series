"""Ensure routine Wikipedia film acquisition cannot consume production D1 quota."""
import re
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[1]
            / ".github/workflows/wikipedia-year-catalogue.yml")


class WikipediaYearSourceOnlyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_schedule_and_push_remain_source_only(self):
        self.assertIn('cron: "41 5 * * *"', self.workflow)
        self.assertIn("branches: [main]", self.workflow)
        self.assertIn('if [[ "$GITHUB_EVENT_NAME" != "workflow_dispatch"', self.workflow)
        self.assertIn('"${{ inputs.apply_to_production }}" != "true"', self.workflow)
        self.assertIn('echo "ready=false"', self.workflow)
        self.assertIn("Source-only acquisition: D1 access disabled", self.workflow)

    def test_manual_import_requires_explicit_false_by_default_boolean(self):
        self.assertRegex(self.workflow,
                         r"apply_to_production:\s*\n\s*description:.*\n"
                         r"\s*required: true\s*\n\s*default: false\s*\n"
                         r"\s*type: boolean")
        self.assertIn('GITHUB_EVENT_NAME', self.workflow)
        self.assertIn('echo "ready=true"', self.workflow)
        self.assertIn('group: india-catalogue-autopilot', self.workflow)
        self.assertIn('cancel-in-progress: false', self.workflow)

    def test_every_d1_step_checks_manual_approval_output(self):
        workflow = self.workflow
        cloudflare_gate = workflow.index("      - name: Gate production database access")
        tail = workflow[cloudflare_gate:]
        commands = list(re.finditer(
            r"^\s*(?:run:.*|.*)\b(?:wrangler d1|cloudflare_bootstrap\.py)\b",
            tail, re.MULTILINE))
        self.assertGreaterEqual(len(commands), 6)
        for step in tail.split("\n      - name: ")[1:]:
            if "wrangler d1" not in step and "cloudflare_bootstrap.py" not in step:
                continue
            self.assertIn("if: steps.cloudflare.outputs.ready == 'true'", step,
                          "D1 call lacks per-step production opt-in gate")
        self.assertIn("name: wikipedia-year-catalogue", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)


if __name__ == "__main__":
    unittest.main()
