import json
import tempfile
import unittest
from pathlib import Path

from scripts.p2_artwork_discovery_review import main


class P2ArtworkDiscoveryReviewTests(unittest.TestCase):
    def test_review_artifact_is_read_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "review.json"
            import sys
            old = sys.argv
            sys.argv = [
                "p2_artwork_discovery_review",
                "--identities", "tests/fixtures/p2_artwork_review_identities.json",
                "--records", "tests/fixtures/p2_artwork_review_records.json",
                "--source-key", "wikimedia_commons",
                "--max-candidates", "1",
                "--output", str(output),
            ]
            try:
                main()
            finally:
                sys.argv = old

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(payload["read_only"])
            self.assertFalse(payload["publication_performed"])
            self.assertFalse(payload["production_writes_performed"])
            self.assertEqual(payload["reviews"][0]["status"], "REVIEW")
            self.assertEqual(payload["reviews"][0]["candidate_count"], 1)
            self.assertEqual(payload["reviews"][1]["status"], "NO_MATCH")


if __name__ == "__main__":
    unittest.main()
