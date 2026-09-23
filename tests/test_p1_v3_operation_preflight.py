import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.p1_v3_operation_preflight import PreflightError, preflight_operation


class P1V3OperationPreflightTests(unittest.TestCase):
    def _fixture(self, root: Path, *, estimated_rows_written: int = 49_159) -> dict[str, str]:
        executable_dir = root / "executable"
        executable_dir.mkdir(parents=True)

        executable = executable_dir / "physical-shard-3.sql"
        executable.write_text("-- reviewed shard 3 executable\nSELECT 1;\n", encoding="utf-8")
        executable_sha = hashlib.sha256(executable.read_bytes()).hexdigest()

        statement_counts = {
            "INSERT INTO genres": 192,
            "INSERT INTO people": 4_877,
            "INSERT INTO recommendation_titles": 1_056,
            "INSERT OR IGNORE INTO title_credits": 5_384,
            "INSERT OR IGNORE INTO title_genres": 1_041,
        }
        cost = {
            "schema_version": "p1-d1-reviewed-import-v2",
            "data_statement_count": sum(statement_counts.values()),
            "estimated_rows_written": estimated_rows_written,
            "executable_sha256": executable_sha,
            "expected_projection_sha256": "projection-test",
            "free_daily_rows_written_limit": 100_000,
            "free_daily_rows_written_headroom": 100_000 - estimated_rows_written,
            "statement_counts": statement_counts,
        }
        (executable_dir / "physical-shard-3-cost.json").write_text(
            json.dumps(cost, sort_keys=True) + "\n", encoding="utf-8"
        )

        attestation = {
            "schema_version": "recommendation-metadata-v3-artifact-attestation",
            "projection_sha256": "projection-test",
            "global_materialization_sha256": "graph-test",
            "already_present_parent_partitions": [0, 8],
            "remaining_full_physical_shards": [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15],
            "physical_shards": [
                {
                    "shard": 3,
                    "candidate_titles": 1_056,
                    "genre_relations": 1_041,
                    "credit_relations": 5_384,
                    "estimated_rows_written": estimated_rows_written,
                    "executable_sql_sha256": executable_sha,
                    "materialization_sha256": "materialization-test",
                }
            ],
        }
        attestation_path = root / "artifact-attestation-v3.json"
        attestation_path.write_text(
            json.dumps(attestation, sort_keys=True) + "\n", encoding="utf-8"
        )
        return {
            "attestation_sha": hashlib.sha256(attestation_path.read_bytes()).hexdigest(),
            "executable_sha": executable_sha,
        }

    def test_physical_shard_preflight_returns_exact_reviewed_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = self._fixture(root)
            result = preflight_operation(
                root,
                "3",
                expected_attestation_sha256=fixture["attestation_sha"],
                expected_projection_sha256="projection-test",
                expected_graph_sha256="graph-test",
            )

        self.assertEqual(result["state"], "preflight_ok")
        self.assertFalse(result["production_mutation"])
        self.assertEqual(result["operation"], "3")
        self.assertEqual(result["physical_shard"], 3)
        self.assertEqual(result["estimated_rows_written"], 49_159)
        self.assertEqual(result["conservative_headroom"], 30_841)
        self.assertEqual(result["free_daily_headroom"], 50_841)
        self.assertEqual(result["data_statement_count"], 12_550)
        self.assertEqual(result["statement_counts"]["recommendation_titles"], 1_056)
        self.assertEqual(result["statement_counts"]["genre_upserts"], 192)
        self.assertEqual(result["statement_counts"]["people_upserts"], 4_877)
        self.assertEqual(result["statement_counts"]["title_genres"], 1_041)
        self.assertEqual(result["statement_counts"]["title_credits"], 5_384)
        self.assertEqual(result["executable_sha256"], fixture["executable_sha"])
        self.assertEqual(result["authorized_parent_partitions_not_rewritten"], [0, 8])

    def test_preflight_fails_if_executable_bytes_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = self._fixture(root)
            (root / "executable" / "physical-shard-3.sql").write_text(
                "-- drifted executable\nSELECT 2;\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PreflightError, "selected executable SHA-256 mismatch"):
                preflight_operation(
                    root,
                    "3",
                    expected_attestation_sha256=fixture["attestation_sha"],
                    expected_projection_sha256="projection-test",
                    expected_graph_sha256="graph-test",
                )

    def test_preflight_fails_closed_above_conservative_ceiling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = self._fixture(root, estimated_rows_written=80_001)
            with self.assertRaisesRegex(PreflightError, "exceeds conservative P1 write ceiling"):
                preflight_operation(
                    root,
                    "3",
                    expected_attestation_sha256=fixture["attestation_sha"],
                    expected_projection_sha256="projection-test",
                    expected_graph_sha256="graph-test",
                )

    def test_preflight_fails_if_statement_counts_do_not_match_attestation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = self._fixture(root)
            cost_path = root / "executable" / "physical-shard-3-cost.json"
            cost = json.loads(cost_path.read_text(encoding="utf-8"))
            cost["statement_counts"]["INSERT INTO recommendation_titles"] = 1_055
            cost["data_statement_count"] -= 1
            cost_path.write_text(json.dumps(cost, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(PreflightError, "attested candidate title count mismatch"):
                preflight_operation(
                    root,
                    "3",
                    expected_attestation_sha256=fixture["attestation_sha"],
                    expected_projection_sha256="projection-test",
                    expected_graph_sha256="graph-test",
                )

    def test_unreviewed_partition_is_not_an_allowed_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(PreflightError, "unsupported V3 operation"):
                preflight_operation(root, "8")


if __name__ == "__main__":
    unittest.main()
