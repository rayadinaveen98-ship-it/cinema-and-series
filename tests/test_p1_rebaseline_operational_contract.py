import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REBASELINE = ROOT / ".github/workflows/p1-rebaseline-materialization-v2.yml"
REPARTITION = ROOT / ".github/workflows/p1-repartition-materialization-v3.yml"
STATUS = ROOT / "docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md"
GRAPH_VERIFY = ROOT / "scripts/verify_p1_v3_production.py"

CURRENT_SHA = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
PARENT_SHA = "4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class P1RebaselineOperationalContractTests(unittest.TestCase):
    def setUp(self):
        self.rebaseline = read(REBASELINE)
        self.repartition = read(REPARTITION)
        self.status = read(STATUS)
        self.graph_verify = read(GRAPH_VERIFY)

    def test_delta_run_is_read_only_and_locked_to_exact_lineage(self):
        self.assertIn('PARENT_RUN_ID: "35252106776"', self.rebaseline)
        self.assertIn('CURRENT_PROJECTION_RUN_ID: "35421313646"', self.rebaseline)
        self.assertIn(PARENT_SHA, self.rebaseline)
        self.assertIn(CURRENT_SHA, self.rebaseline)
        self.assertIn('EXPECTED_UNCHANGED: "14114"', self.rebaseline)
        self.assertIn('EXPECTED_ADDED: "2266"', self.rebaseline)
        self.assertIn('EXPECTED_REMOVED: "1"', self.rebaseline)
        self.assertIn("Q3049630", self.rebaseline)
        self.assertNotIn("wrangler d1 execute", self.rebaseline)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", self.rebaseline)

    def test_v3_repartition_is_manual_read_only_assembly(self):
        self.assertIn("workflow_dispatch:", self.repartition)
        self.assertNotIn("schedule:", self.repartition)
        self.assertNotIn("wrangler d1 execute", self.repartition)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", self.repartition)
        self.assertIn(CURRENT_SHA, self.repartition)
        self.assertIn('EXPECTED_CANDIDATES: "16380"', self.repartition)
        self.assertIn('PHYSICAL_SHARD_COUNT: "16"', self.repartition)
        self.assertIn('MAX_ROWS_WRITTEN_PER_DAY: "80000"', self.repartition)

    def test_v3_requires_complete_clean_delta_before_repartition(self):
        self.assertIn("missing delta shard", self.repartition)
        self.assertIn("delta candidate partition mismatch", self.repartition)
        self.assertIn("delta has missing title entities", self.repartition)
        self.assertIn("delta has skipped relations from missing labels", self.repartition)
        self.assertIn("recommendation_delta_materialization", read(ROOT / "scripts/repartition_recommendation_materialization.py"))

    def test_v3_write_cost_plan_preserves_existing_parent_shard_zero(self):
        self.assertIn("existing-shard-0-topup", self.repartition)
        self.assertIn("already_present_parent_partitions':[0,8]", self.repartition)
        self.assertIn("remaining_full_physical_shards':[1,2,3,4,5,6,7,9,10,11,12,13,14,15]", self.repartition)
        self.assertIn("exceeds conservative write ceiling", self.repartition)
        self.assertIn("recommendation-metadata-materialization-v3-repartitioned", self.repartition)

    def test_v3_attests_exact_graph_and_every_executable_artifact(self):
        self.assertIn("Build final V3 artifact attestation", self.repartition)
        self.assertIn("build_p1_v3_artifact_manifest.py", self.repartition)
        self.assertIn("artifact-attestation-v3.json", self.repartition)
        self.assertIn("artifact-attestation-v3.sha256", self.repartition)
        repartition_script = read(ROOT / "scripts/repartition_recommendation_materialization.py")
        self.assertIn("materialization_sha256", repartition_script)
        self.assertIn("Global materialization SHA-256", repartition_script)
        self.assertIn("Shard materialization SHA-256", repartition_script)

    def test_final_production_verifier_requires_exact_reviewed_graph(self):
        self.assertIn("production materialization graph mismatch", self.graph_verify)
        self.assertIn("materialization_fingerprint", self.graph_verify)
        self.assertIn("invalid recommendation provenance", self.graph_verify)
        self.assertIn("orphan relationships", self.graph_verify)
        self.assertIn("P1_V3_PRODUCTION_GRAPH_VERIFIED", self.graph_verify)

    def test_status_explicitly_marks_parent_writer_obsolete(self):
        self.assertIn("SHARD 1 COMPLETE", self.status)
        self.assertIn("physical shard 2", self.status)
        self.assertIn("35689533994:1", self.status)
        self.assertIn(CURRENT_SHA, self.status)
        self.assertIn("14,114", self.status)
        self.assertIn("2,266", self.status)
        self.assertIn("obsolete 14,115-title / 8-shard", self.status)
        self.assertIn("P1 exits only after", self.status)


if __name__ == "__main__":
    unittest.main()
