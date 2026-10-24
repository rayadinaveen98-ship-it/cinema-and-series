"""Offline tests: no secrets, GitHub mutations or Cloudflare operations."""
import tempfile
import unittest
from pathlib import Path
from scripts.foundation_workflow_inventory import inspect_workflow, inventory


class WorkflowInventoryTests(unittest.TestCase):
    def test_scheduled_manual_and_chained_triggers_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"cron.yml"
            path.write_text(
                'name: QA\non:\n  schedule:\n'
                '    - cron: "*/15 * * * *"\n'
                '  workflow_run:\n    workflows: ["Collect"]\n'
                '  workflow_dispatch:\npermissions:\n  contents: read\n'
                'jobs:\n  test:\n    steps:\n      - run: echo test\n')
            x=inspect_workflow(path)
            self.assertTrue(x["scheduled"])
            self.assertTrue(x["workflow_chained"])
            self.assertTrue(x["manual"])
            self.assertTrue(x["needs_manual_review"])
            self.assertEqual(x["cron_expressions"],["*/15 * * * *"])

    def test_frozen_cloudflare_reference_is_only_a_static_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"cloudflare.yml"
            path.write_text(
                "on:\n  push:\n    branches: [main]\n"
                "jobs:\n  stage:\n    steps:\n"
                "      - run: python scripts/foundation_remote_account_preflight.py\n"
                "        env:\n"
                "          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}\n"
                "      - run: cat ops/data-foundation-v2-freeze.json\n")
            x=inspect_workflow(path)
            self.assertTrue(x["push_triggered"])
            self.assertTrue(x["cloudflare_token_reference"])
            self.assertTrue(x["explicit_freeze_file_reference"])
            self.assertTrue(x["needs_manual_review"])
            self.assertEqual(x["scope"],"static_workflow_source_only")

    def test_incomplete_inline_triggers_never_pass_as_reviewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"inline.yml"
            path.write_text("on: [schedule, push]\njobs:\n")
            x=inspect_workflow(path)
            self.assertTrue(x["trigger_parser_uncertain"])
            self.assertTrue(x["needs_manual_review"])

    def test_actual_repository_inventories_all_workflow_files(self):
        root=Path(".github/workflows")
        if not root.exists():
            self.skipTest("Only run in a repository checkout")
        x=inventory(root)
        self.assertEqual(x["workflows_inspected"],
                         len(list(root.glob("*.yml")))+len(list(root.glob("*.yaml"))))
        self.assertGreaterEqual(x["workflows_inspected"],100)
        canary=next(i for i in x["entries"] if i["path"]==
            "foundation-remote-worker-binding-canary.yml")
        self.assertTrue(canary["manual"])
        self.assertFalse(canary["scheduled"])
        self.assertFalse(canary["push_triggered"])
        self.assertEqual(x["no_production_d1_data_access"],True)


if __name__=="__main__":
    unittest.main()
