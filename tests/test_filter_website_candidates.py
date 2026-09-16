import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "filter_website_candidates.py"
spec = importlib.util.spec_from_file_location("filter_website_candidates", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class WebsiteCandidateFilterTests(unittest.TestCase):
    def test_known_verified_dates_are_indexed_by_source(self):
        known = module.known_dates_by_source(
            {
                "releases": [
                    {
                        "source_key": "dharma_productions",
                        "release_date": "2026-10-09",
                        "verification_status": "verified",
                    },
                    {
                        "source_key": "dharma_productions",
                        "release_date": "2027-02-12",
                        "verification_status": "verified",
                    },
                    {
                        "source_key": "example",
                        "release_date": "2027-03-01",
                        "verification_status": "unconfirmed",
                    },
                ]
            }
        )
        self.assertEqual(known["dharma_productions"], {"2026-10-09", "2027-02-12"})
        self.assertNotIn("example", known)

    def test_fully_known_candidate_is_removed(self):
        candidates = [
            {
                "source_key": "dharma_productions",
                "candidate_dates": ["2026-10-09", "2027-02-12"],
                "candidate_release_date": None,
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"dharma_productions": {"2026-10-09", "2027-02-12"}},
        )
        self.assertEqual(filtered, [])
        self.assertEqual(suppressed, 2)

    def test_mixed_candidate_keeps_only_new_date(self):
        candidates = [
            {
                "source_key": "example",
                "candidate_dates": ["2026-10-09", "2027-05-14"],
                "candidate_release_date": None,
                "status": "pending_review",
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"example": {"2026-10-09"}},
        )
        self.assertEqual(suppressed, 1)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["candidate_dates"], ["2027-05-14"])
        self.assertEqual(filtered[0]["candidate_release_date"], "2027-05-14")
        self.assertEqual(filtered[0]["status"], "pending_review")

    def test_new_candidate_is_unchanged(self):
        candidate = {
            "source_key": "example",
            "candidate_dates": ["2027-05-14"],
            "candidate_release_date": "2027-05-14",
        }
        filtered, suppressed = module.filter_candidates([candidate], {"example": {"2026-10-09"}})
        self.assertEqual(suppressed, 0)
        self.assertEqual(filtered, [candidate])


if __name__ == "__main__":
    unittest.main()
