import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/p1-final-completion-attestation.yml"
WRITER = ROOT / ".github/workflows/recommendation-metadata-production-write-v3.yml"
SCRIPT = ROOT / "scripts/build_p1_completion_attestation.py"

PROJECTION_SHA = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
GRAPH_SHA = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"
ATTESTATION_SHA = "8eb39db7964c03e968b26aeccaa33f4b0f85c422fe4c08471ee7ec95510e2986"


class P1CompletionAttestationContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.writer = WRITER.read_text(encoding="utf-8")
        self.script = SCRIPT.read_text(encoding="utf-8")

    def test_requires_explicit_successful_main_v3_trigger_run(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertIn("trigger_run_id:", self.workflow)
        self.assertIn("Validate successful main V3 triggering run", self.workflow)
        self.assertIn("Recommendation Metadata Production Write V3", self.workflow)
        self.assertIn("run.get('conclusion')", self.workflow)
        self.assertIn("run.get('head_branch')", self.workflow)
        self.assertIn("run.get('path')", self.workflow)

    def test_non_final_writer_runs_are_noop(self):
        self.assertIn("Require exact final-verification artifact on triggering run", self.workflow)
        self.assertIn("recommendation-metadata-production-write-v3-verify_final-final", self.workflow)
        self.assertIn("is_final", self.workflow)
        self.assertIn("non_final_writer", self.workflow)

    def test_controller_dispatches_attestation_before_retirement(self):
        self.assertIn("p1-final-completion-attestation.yml", self.writer)
        self.assertIn("trigger_run_id", self.writer)
        self.assertIn("P1 completion attestation is pending", self.writer)
        self.assertIn("final_attestation_state.outputs.verified == 'true'", self.writer)

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

    def test_final_writer_artifact_layout_matches_completion_consumer(self):
        self.assertIn("path: data/generated/v3-production/**", self.writer)
        for produced in (
            "data/generated/v3-production/projection/manifest.json",
            "data/generated/v3-production/final/graph-verification.json",
            "data/generated/v3-production/integrity.json",
            "data/generated/v3-production/final/catalogue-quality-v1.json",
            "data/generated/v3-production/source-movies.json",
            "data/generated/v3-production/source-catalogue.json",
            "data/generated/v3-production/source-series.json",
        ):
            self.assertIn(produced, self.writer)
        for consumed in (
            "data/generated/final-verify-evidence/projection/manifest.json",
            "data/generated/final-verify-evidence/final/graph-verification.json",
            "data/generated/final-verify-evidence/integrity.json",
            "data/generated/final-verify-evidence/final/catalogue-quality-v1.json",
            "data/generated/final-verify-evidence/source-movies.json",
            "data/generated/final-verify-evidence/source-catalogue.json",
            "data/generated/final-verify-evidence/source-series.json",
        ):
            self.assertIn(consumed, self.workflow)


if __name__ == "__main__":
    unittest.main()
