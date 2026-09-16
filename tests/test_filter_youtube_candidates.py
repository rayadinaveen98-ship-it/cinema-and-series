import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "filter_youtube_candidates.py"
spec = importlib.util.spec_from_file_location("filter_youtube_candidates", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class YouTubeCandidateFilterTests(unittest.TestCase):
    def test_verified_dates_are_indexed_by_source(self):
        payload = {
            "releases": [
                {
                    "source_key": "red_chillies_entertainment",
                    "release_date": "2026-12-24",
                    "verification_status": "verified",
                },
                {
                    "source_key": "other",
                    "release_date": "2027-01-01",
                    "verification_status": "unconfirmed",
                },
            ]
        }
        self.assertEqual(
            module.known_dates_by_source(payload),
            {"red_chillies_entertainment": {"2026-12-24"}},
        )

    def test_fully_known_candidate_is_removed(self):
        candidates = [
            {
                "source_key": "red_chillies_entertainment",
                "candidate_dates": ["2026-12-24"],
                "candidate_release_date": "2026-12-24",
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"red_chillies_entertainment": {"2026-12-24"}},
        )
        self.assertEqual(filtered, [])
        self.assertEqual(suppressed, 1)

    def test_mixed_candidate_keeps_only_new_date(self):
        candidates = [
            {
                "source_key": "studio",
                "candidate_dates": ["2026-12-24", "2027-01-08"],
                "candidate_release_date": None,
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"studio": {"2026-12-24"}},
        )
        self.assertEqual(suppressed, 1)
        self.assertEqual(filtered[0]["candidate_dates"], ["2027-01-08"])
        self.assertEqual(filtered[0]["candidate_release_date"], "2027-01-08")


if __name__ == "__main__":
    unittest.main()
