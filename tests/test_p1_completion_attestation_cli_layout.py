import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_p1_completion_attestation.py"
PROJECTION_SHA = "f26f6218a43c843dd12bbe14e461d9b8264dc26ab06244957bcd5d5042512ff6"
GRAPH_SHA = "9a931b9a7ef081dd8579f67218de14d086515f4cc4bfa20cacb3edb2b8379b78"


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def d1_payload(rows):
    return [{"results": rows, "success": True, "meta": {}}]


class P1CompletionAttestationCliLayoutTests(unittest.TestCase):
    def test_exact_final_artifact_tree_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reviewed = root / "reviewed-v3"
            final = root / "final-verify-evidence"
            out = root / "p1-completion-attestation.json"

            reviewed_attestation = {
                "projection_sha256": PROJECTION_SHA,
                "global_materialization_sha256": GRAPH_SHA,
                "candidate_count": 16380,
                "totals": {
                    "candidate_titles": 16380,
                    "genres": 612,
                    "people": 37964,
                    "emitted_genre_relations": 16489,
                    "emitted_credit_relations": 70551,
                },
            }
            attestation_path = reviewed / "artifact-attestation-v3.json"
            write_json(attestation_path, reviewed_attestation)
            attestation_sha = hashlib.sha256(attestation_path.read_bytes()).hexdigest()

            write_json(
                final / "projection/manifest.json",
                {
                    "sha256": PROJECTION_SHA,
                    "candidate_count": 16380,
                    "movie_qid_count": 6562,
                    "series_qid_count": 9818,
                    "cross_type_collision_count": 0,
                },
            )
            write_json(
                final / "final/graph-verification.json",
                {
                    "state": "verified",
                    "production_mutation": False,
                    "global_materialization_sha256": GRAPH_SHA,
                    "counts": {
                        "candidate_titles": 16380,
                        "genres": 612,
                        "people": 37964,
                        "emitted_genre_relations": 16489,
                        "emitted_credit_relations": 70551,
                    },
                    "orphan_genre_relations": 0,
                    "orphan_credit_relations": 0,
                    "invalid_genre_provenance": 0,
                    "invalid_credit_provenance": 0,
                },
            )
            write_json(
                final / "integrity.json",
                d1_payload(
                    [
                        {
                            "orphan_genres": 0,
                            "orphan_credits": 0,
                            "invalid_genre_provenance": 0,
                            "invalid_credit_provenance": 0,
                        }
                    ]
                ),
            )
            write_json(
                final / "final/catalogue-quality-v1.json",
                {"finding_summary": {"by_severity": {"S0": 0, "S1": 0, "S2": 0}}},
            )
            write_json(final / "source-movies.json", d1_payload([]))
            write_json(final / "source-catalogue.json", d1_payload([]))
            write_json(
                final / "source-series.json",
                d1_payload([{"id": "series-wd-Q3146368", "wikidata_qid": "Q3146368"}]),
            )

            cmd = [
                sys.executable,
                str(SCRIPT),
                "--attestation",
                str(attestation_path),
                "--projection-manifest",
                str(final / "projection/manifest.json"),
                "--graph-verification",
                str(final / "final/graph-verification.json"),
                "--integrity-json",
                str(final / "integrity.json"),
                "--catalogue-quality",
                str(final / "final/catalogue-quality-v1.json"),
                "--source-movies",
                str(final / "source-movies.json"),
                "--source-catalogue",
                str(final / "source-catalogue.json"),
                "--source-series",
                str(final / "source-series.json"),
                "--expected-attestation-sha256",
                attestation_sha,
                "--expected-projection-sha256",
                PROJECTION_SHA,
                "--expected-graph-sha256",
                GRAPH_SHA,
                "--expected-candidates",
                "16380",
                "--expected-movies",
                "6562",
                "--expected-series",
                "9818",
                "--expected-genres",
                "612",
                "--expected-people",
                "37964",
                "--expected-genre-relations",
                "16489",
                "--expected-credit-relations",
                "70551",
                "--out",
                str(out),
            ]
            completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)

            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertIn("P1_COMPLETION_ATTESTATION_VERIFIED=", completed.stdout)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(payload["p1_completion_eligible"])
            self.assertEqual(payload["state"], "verified")
            self.assertFalse(payload["production_mutation"])
            self.assertEqual(payload["production_graph"]["counts"]["recommendation_titles"], 16380)
            self.assertEqual(len(payload["evidence_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
