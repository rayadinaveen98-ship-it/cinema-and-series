import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_p1_v3_artifact_manifest as module


PROJECTION_SHA = "1" * 64
GLOBAL_SHA = "2" * 64


class P1V3ArtifactManifestTests(unittest.TestCase):
    def make_fixture(self, root: Path):
        (root / "executable").mkdir(parents=True)
        summary = {
            "state": "complete",
            "production_mutation": False,
            "materialization_sha256": GLOBAL_SHA,
            "projection_manifest": {"sha256": PROJECTION_SHA},
            "physical_shard_count": 2,
            "lineage": {"unchanged_count": 2, "added_count": 1, "removed_count": 0, "removed_qids": []},
            "totals": {
                "candidate_titles": 3,
                "genres": 2,
                "people": 2,
                "emitted_genre_relations": 2,
                "emitted_credit_relations": 2,
            },
            "shards": [
                {"shard": 0, "materialization_sha256": "a" * 64},
                {"shard": 1, "materialization_sha256": "b" * 64},
            ],
        }
        projection = {"sha256": PROJECTION_SHA, "candidate_count": 3}
        cost_plan = {
            "projection_sha256": PROJECTION_SHA,
            "physical_shard_rows_written": {"0": 100, "1": 120},
            "existing_shard_0_topup_rows_written": 25,
            "already_present_parent_partitions": [0],
            "remaining_full_physical_shards": [1],
            "hard_ceiling": 80000,
        }
        (root / "recommendation-metadata-materialization-v3-summary.json").write_text(json.dumps(summary))
        (root / "recommendation-projection-manifest.json").write_text(json.dumps(projection))
        (root / "write-cost-plan-v3.json").write_text(json.dumps(cost_plan))

        for shard, titles, graph_sha, genre_rel, credit_rel, cost in (
            (0, 1, "a" * 64, 1, 1, 100),
            (1, 2, "b" * 64, 1, 1, 120),
        ):
            report = {
                "materialization_sha256": graph_sha,
                "global_materialization_sha256": GLOBAL_SHA,
                "shard_index": shard,
                "shard_count": 2,
                "projection_manifest": {"sha256": PROJECTION_SHA},
                "stats": {
                    "candidate_titles": titles,
                    "emitted_genre_relations": genre_rel,
                    "emitted_credit_relations": credit_rel,
                },
            }
            (root / f"recommendation-materialization-physical-shard-{shard}.json").write_text(json.dumps(report))
            sql = (
                f"-- Projection manifest SHA-256: {PROJECTION_SHA}\n"
                f"-- Global materialization SHA-256: {GLOBAL_SHA}\n"
                f"-- Shard materialization SHA-256: {graph_sha}\n"
                "INSERT INTO recommendation_titles VALUES ('x');\n"
            )
            (root / f"recommendation-materialization-physical-shard-{shard}.sql").write_text(sql)
            (root / "executable" / f"physical-shard-{shard}.sql").write_text("INSERT INTO recommendation_titles VALUES ('x');\n")
            (root / "executable" / f"physical-shard-{shard}-cost.json").write_text(
                json.dumps({"estimated_rows_written": cost})
            )

        (root / "executable" / "existing-shard-0-topup.sql").write_text("INSERT INTO recommendation_titles VALUES ('topup');\n")
        (root / "executable" / "existing-shard-0-topup-cost.json").write_text(
            json.dumps({"estimated_rows_written": 25})
        )

    def test_build_manifest_attests_every_reviewed_and_executable_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            result = module.build_manifest(
                root,
                expected_projection_sha256=PROJECTION_SHA,
                expected_candidates=3,
                shard_count=2,
            )
            self.assertEqual(result["global_materialization_sha256"], GLOBAL_SHA)
            self.assertEqual(result["candidate_count"], 3)
            self.assertEqual(len(result["physical_shards"]), 2)
            self.assertEqual(result["physical_shards"][0]["estimated_rows_written"], 100)
            self.assertEqual(result["existing_shard_0_topup"]["estimated_rows_written"], 25)
            for shard in result["physical_shards"]:
                self.assertRegex(shard["reviewed_sql_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(shard["executable_sql_sha256"], r"^[0-9a-f]{64}$")

    def test_missing_graph_binding_in_reviewed_sql_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            path = root / "recommendation-materialization-physical-shard-1.sql"
            path.write_text(path.read_text().replace(f"-- Global materialization SHA-256: {GLOBAL_SHA}\n", ""))
            with self.assertRaisesRegex(ValueError, "lacks global graph binding"):
                module.build_manifest(
                    root,
                    expected_projection_sha256=PROJECTION_SHA,
                    expected_candidates=3,
                    shard_count=2,
                )

    def test_write_cost_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_fixture(root)
            (root / "executable" / "physical-shard-0-cost.json").write_text(
                json.dumps({"estimated_rows_written": 99})
            )
            with self.assertRaisesRegex(ValueError, "cost plan mismatch"):
                module.build_manifest(
                    root,
                    expected_projection_sha256=PROJECTION_SHA,
                    expected_candidates=3,
                    shard_count=2,
                )


if __name__ == "__main__":
    unittest.main()
