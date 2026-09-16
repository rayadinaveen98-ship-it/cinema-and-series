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
    def test_verified_titles_are_indexed_by_source_and_date(self):
        payload = {
            "releases": [
                {
                    "title": "KING",
                    "source_key": "red_chillies_entertainment",
                    "release_date": "2026-12-24",
                    "verification_status": "verified",
                },
                {
                    "title": "Other",
                    "source_key": "other",
                    "release_date": "2027-01-01",
                    "verification_status": "unconfirmed",
                },
            ]
        }
        self.assertEqual(
            module.verified_titles_by_source_date(payload),
            {"red_chillies_entertainment": {"2026-12-24": {"KING"}}},
        )

    def test_fully_known_same_movie_candidate_is_removed(self):
        candidates = [
            {
                "source_key": "red_chillies_entertainment",
                "video_title": "KING | Shah Rukh Khan | Release Date Announcement",
                "candidate_dates": ["2026-12-24"],
                "candidate_release_date": "2026-12-24",
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"red_chillies_entertainment": {"2026-12-24": {"KING"}}},
        )
        self.assertEqual(filtered, [])
        self.assertEqual(suppressed, 1)

    def test_same_source_and_date_different_movie_is_not_removed(self):
        candidate = {
            "source_key": "red_chillies_entertainment",
            "video_title": "Another Film | In Cinemas 24 December 2026",
            "candidate_dates": ["2026-12-24"],
            "candidate_release_date": "2026-12-24",
        }
        filtered, suppressed = module.filter_candidates(
            [candidate],
            {"red_chillies_entertainment": {"2026-12-24": {"KING"}}},
        )
        self.assertEqual(filtered, [candidate])
        self.assertEqual(suppressed, 0)

    def test_distinctive_cross_source_same_title_and_date_is_removed(self):
        candidate = {
            "source_key": "t_series",
            "video_title": "RANABAALI - Hindi Teaser | In Theatres October 16th",
            "candidate_dates": ["2026-10-16"],
            "candidate_release_date": "2026-10-16",
        }
        filtered, suppressed = module.filter_candidates(
            [candidate],
            {"mythri_movie_makers": {"2026-10-16": {"RANABAALI"}}},
        )
        self.assertEqual(filtered, [])
        self.assertEqual(suppressed, 1)

    def test_short_generic_cross_source_title_is_kept_for_review(self):
        candidate = {
            "source_key": "t_series",
            "video_title": "KING | Official Announcement | 24 December 2026",
            "candidate_dates": ["2026-12-24"],
            "candidate_release_date": "2026-12-24",
        }
        filtered, suppressed = module.filter_candidates(
            [candidate],
            {"red_chillies_entertainment": {"2026-12-24": {"KING"}}},
        )
        self.assertEqual(filtered, [candidate])
        self.assertEqual(suppressed, 0)

    def test_cross_source_same_title_but_different_date_is_kept(self):
        candidate = {
            "source_key": "t_series",
            "video_title": "RANABAALI | New Date Announcement",
            "candidate_dates": ["2026-10-23"],
            "candidate_release_date": "2026-10-23",
        }
        filtered, suppressed = module.filter_candidates(
            [candidate],
            {"mythri_movie_makers": {"2026-10-16": {"RANABAALI"}}},
        )
        self.assertEqual(filtered, [candidate])
        self.assertEqual(suppressed, 0)

    def test_mixed_candidate_keeps_only_new_date_for_same_movie(self):
        candidates = [
            {
                "source_key": "studio",
                "video_title": "Dragon | Release Update",
                "candidate_dates": ["2026-12-24", "2027-01-08"],
                "candidate_release_date": None,
                "date_contexts": [
                    {"date": "2026-12-24", "excerpt": "Dragon releases 24 December 2026."},
                    {"date": "2027-01-08", "excerpt": "Dragon new date 8 January 2027 in cinemas."},
                ],
            }
        ]
        filtered, suppressed = module.filter_candidates(
            candidates,
            {"studio": {"2026-12-24": {"Dragon"}}},
        )
        self.assertEqual(suppressed, 1)
        self.assertEqual(filtered[0]["candidate_dates"], ["2027-01-08"])
        self.assertEqual(filtered[0]["candidate_release_date"], "2027-01-08")
        self.assertEqual(
            filtered[0]["date_contexts"],
            [{"date": "2027-01-08", "excerpt": "Dragon new date 8 January 2027 in cinemas."}],
        )

    def test_missing_movie_identity_is_kept_for_review(self):
        candidate = {
            "source_key": "studio",
            "video_title": "Big Release Date Announcement",
            "candidate_dates": ["2026-12-24"],
            "candidate_release_date": "2026-12-24",
            "date_contexts": [
                {"date": "2026-12-24", "excerpt": "Big release in cinemas 24 December 2026."}
            ],
        }
        filtered, suppressed = module.filter_candidates(
            [candidate],
            {"studio": {"2026-12-24": {"Dragon"}}},
        )
        self.assertEqual(filtered, [candidate])
        self.assertEqual(suppressed, 0)


if __name__ == "__main__":
    unittest.main()
