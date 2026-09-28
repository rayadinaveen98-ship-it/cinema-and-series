import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import p2_artwork_coverage_audit as audit


ROOT = Path(__file__).resolve().parents[1]


class P2ArtworkAuditSnapshotBuilderCliTests(unittest.TestCase):
    def test_documented_cli_path_builds_valid_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            titles_path = root / "titles.json"
            candidates_path = root / "candidates.json"
            output_path = root / "snapshot.json"

            titles_path.write_text(
                json.dumps(
                    {
                        "titles": [
                            {
                                "media_type": "movie",
                                "source_table": "movies",
                                "source_id": "m1",
                                "language": "Telugu",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidates_path.write_text(
                json.dumps(
                    {
                        "candidates": [
                            {
                                "media_type": "movie",
                                "source_table": "movies",
                                "source_id": "m1",
                                "source_key": "official_page",
                                "source_asset_id": "og-1",
                                "presentation_role": "poster",
                                "publication_state": "DISCOVERED",
                                "rights_basis": "NO_RIGHTS_BASIS",
                                "hosting_mode": "REFERENCE_ONLY",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_p2_artwork_audit_snapshot.py",
                    "--titles",
                    str(titles_path),
                    "--candidates",
                    str(candidates_path),
                    "--territory",
                    "IN",
                    "--evaluated-at",
                    "2026-09-28T00:00:00Z",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            snapshot = json.loads(output_path.read_text(encoding="utf-8"))
            report = audit.build_report(snapshot)
            self.assertEqual(report["input"], {"titles": 1, "candidates": 1})
            self.assertEqual(report["candidates"]["publishable_image_candidates"], 0)
            self.assertIn("sha256=", result.stdout)
            self.assertEqual(len(report["input_attestation"]["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
