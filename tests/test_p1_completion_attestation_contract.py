import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/p1-final-completion-attestation.yml"
SCRIPT = ROOT / "scripts/build_p1_completion_attestation.py"

PROJECTION_SHA = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
GRAPH_SHA = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"
ATTESTATION_SHA = "8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986"


class P1CompletionAttestationContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.script = SCRIPT.read_text(encoding="utf-8")

    def test_follows_only_completed_v3_writer_runs(self):
        self.assertIn('workflows: ["Recommendation Metadata Production Write V3"]', self.workflow)
        self.assertIn("types: [completed]", self.workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", self.workflow)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", self.workflow)

    def test_non_final_writer_runs_are_noop(self):
        self.assertIn("Require exact final-verification artifact on triggering run", self.workflow)
        self.assertIn("recommendation-metadata-production-write-v3-verify_final-final", self.workflow)
        self.assertIn("is_final", self.workflow)
        self.assertIn("non_final_writer", self.workflow)

    def test_completion_attestation_reuses_all_locked_p1_fingerprints(self):
        for value in (PROJECTION_SHA, GRAPH_SHA, ATTESTATION_SHA):
            self.assertIn(value, self.workflow)
        for value in ('"16380"', '"6562"', '"9818"', '"612"', '"37964"', '"16489"', '"70551"'):
            self.assertIn(value, self.workflow)
        self.assertIn("build_p1_completion_attestation.py", self.workflow)
        self.assertIn("p1-completion-attestation.json", self.workflow)

    def test_workflow_is_read_only_with_no_cloudflare_or_d1_write_path(self):
        self.assertIn("actions: read", self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("wrangler", self.workflow.lower())
        self.assertNotIn("cloudflare", self.workflow.lower())
        self.assertNotIn("d1 execute", self.workflow.lower())
        self.assertNotIn("apply_production_write", self.workflow)

    def test_script_fail_closed_contract_mentions_all_final_gates(self):
        self.assertIn("p1_completion_eligible", self.script)
        self.assertIn("production projection mismatch", self.script)
        self.assertIn("final graph verification SHA mismatch", self.script)
        self.assertIn("production recommendation integrity is not clean", self.script)
        self.assertIn("Catalogue Quality V1 is not clean", self.script)
        self.assertIn("reviewed source cleanup", self.script)
        self.assertIn("evidence_sha256", self.script)

    def test_attestation_artifact_is_published_only_for_final_verification(self):
        self.assertIn("Publish P1 completion attestation", self.workflow)
        self.assertIn("if: steps.final_artifact.outputs.is_final == 'true'", self.workflow)
        self.assertIn("p1-final-completion-attestation-${{ env.TRIGGER_RUN_ID }}", self.workflow)
        self.assertIn("retention-days: 90", self.workflow)


if __name__ == "__main__":
    unittest.main()
