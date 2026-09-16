import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "filter_youtube_candidates.py"
spec = importlib.util.spec_from_file_location("filter_youtube_candidates_nayyi", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class NayyiNavelliDedupeTests(unittest.TestCase):
    def test_verified_amazon_nayyi_navelli_repeats_are_suppressed(self):
        known = {
            "amazon_mgm_studios_india": {
                "2026-10-16": {"Nayyi Navelli"},
            }
        }
        candidates = [
            {
                "source_key": "amazon_mgm_studios_india",
                "video_title": "Nayyi Navelli: Official Teaser | Yami, Addinath | 16th Oct",
                "candidate_dates": ["2026-10-16"],
                "candidate_release_date": "2026-10-16",
            },
            {
                "source_key": "amazon_mgm_studios_india",
                "video_title": "Nayyi Navelli | In Cinemas - 16th October | Yami Gautam",
                "candidate_dates": ["2026-10-16"],
                "candidate_release_date": "2026-10-16",
            },
        ]

        filtered, suppressed = module.filter_candidates(candidates, known)

        self.assertEqual(filtered, [])
        self.assertEqual(suppressed, 2)


if __name__ == "__main__":
    unittest.main()
