"""Offline contract tests for the read-only Indian movie growth audit."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_indian_movie_growth import audit, category_seeds, markdown_report


def candidate(page, qid, title, year, language, india=False, years=None):
    return {
        "page_id": page, "wikidata_qid": qid, "title": title,
        "year": year, "observed_years": years or [year],
        "language": language, "observed_languages": [language],
        "india_category": india, "source_categories": [],
        "source_url": f"https://en.wikipedia.org/?curid={page}",
    }


class IndiaMovieAuditTests(unittest.TestCase):
    def test_seeds_include_india_and_priority_languages(self):
        seeds = list(category_seeds(2025, 2026))
        self.assertIn(("Category:2026 Indian films", 2026, None, "india_category"), seeds)
        self.assertIn(("Category:2025 Telugu-language films", 2025, "Telugu", "language_category"), seeds)
        self.assertEqual(len(seeds), 2 * 13)

    def test_qid_page_title_year_dedup_and_uncertainty(self):
        exact = [{"id": "m1", "title": "Existing Film", "wikidata_qid": "Q10", "release_date": "2023-04-05"}]
        year = [{"id": "y1", "title": "Old Classic", "wikidata_qid": "Q11",
                 "wikipedia_page_id": 40, "release_year": 1980}]
        candidates = [
            candidate(1, "Q10", "Existing Film", 2023, "Telugu"),
            candidate(40, None, "Old Classic", 1980, "Hindi"),
            candidate(4, "Q12", "Existing Film", 2023, "Telugu"),
            candidate(5, "Q13", "Brand New Film", 2025, "Telugu", True),
            candidate(6, "Q14", "Other Film", 2025, "Punjabi"),
            candidate(7, None, "Conflicting Film", None, "Hindi", False, [2024, 2025]),
            candidate(5, "Q13", "Brand New Film", 2025, "Telugu", True),
        ]
        report = audit(candidates, exact, year, {"source_incomplete": False})
        s = report["summary"]
        self.assertEqual(s["already_in_production"], 2)
        self.assertEqual(s["possible_existing_title_year_match"], 1)
        self.assertEqual(s["new_indian_category_candidates"], 1)
        self.assertEqual(s["new_language_only_candidates"], 1)
        self.assertEqual(s["needs_identity_or_year_review"], 1)
        self.assertEqual(s["duplicate_inside_discovery"], 1)
        self.assertEqual(s["total_net_new_discovery_candidates"], 2)
        self.assertEqual(s["discovered_unique_pages"], 6)
        self.assertIn("not an import", markdown_report(report))

    def test_only_qid_or_page_exactly_confirms_existing_identity(self):
        existing = [{"title": "Test", "wikidata_qid": "Q100",
                     "wikipedia_page_id": 1000, "release_year": 2024}]
        report = audit([
            candidate(2000, "Q100", "Unrelated title", 2024, "Hindi"),
            candidate(1000, "Q200", "Other", 2024, "Hindi"),
            candidate(3000, "Q300", "Test", 2024, "Hindi"),
        ], [], existing)
        self.assertEqual(report["summary"]["already_in_production"], 2)
        self.assertEqual(report["summary"]["possible_existing_title_year_match"], 1)

    def test_two_languages_same_page_not_two_new_films(self):
        report = audit([
            candidate(99, "Q999", "Bilingual Film", 2024, "Telugu", True),
            candidate(99, "Q999", "Bilingual Film", 2024, "Tamil", True),
        ], [], [])
        self.assertEqual(report["summary"]["new_indian_category_candidates"], 1)
        self.assertEqual(report["summary"]["duplicate_inside_discovery"], 1)


if __name__ == "__main__":
    unittest.main()
