"""Offline contract tests for the read-only Indian movie growth audit."""
import sys
import unittest
import urllib.error
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_indian_movie_growth import audit, category_seeds, markdown_report, discover, rate_limited, resolve_page_qids, category_pages


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

    def test_fast_india_only_year_scan_avoids_twelve_language_requests(self):
        seeds = list(category_seeds(2008, 2009, india_only=True))
        self.assertEqual(seeds, [
            ("Category:2009 Indian films", 2009, None, "india_category"),
            ("Category:2008 Indian films", 2008, None, "india_category"),
        ])
        with (patch("audit_indian_movie_growth.category_pages",
                    return_value=[{"page_id": 222, "title": "New Film",
                                   "wikidata_qid": "Q222"}]) as pages,
              patch("audit_indian_movie_growth.time.sleep")):
            records, meta = discover(2008, 2009, 8000, max_categories=16,
                                     india_only=True)
        self.assertEqual(pages.call_count, 2)
        self.assertEqual(len(records), 1)
        self.assertTrue(meta["india_only"])
        self.assertEqual(meta["next_category_offset"], 2)
        self.assertFalse(meta["source_incomplete"])
        self.assertTrue(records[0]["india_category"])

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

    def test_category_generator_resolves_qid_without_second_api_call(self):
        payload = {
            "query": {"pages": [
                {"pageid": 42, "title": "Test Film",
                 "pageprops": {"wikibase_item": "Q12345"}},
                {"pageid": 43, "title": "Another Film"},
            ]}
        }
        with patch("audit_indian_movie_growth.wiki.request_json", return_value=payload) as req:
            pages = category_pages("Category:2026 Indian films")
        self.assertEqual(pages[0]["wikidata_qid"], "Q12345")
        self.assertIsNone(pages[1]["wikidata_qid"])
        kwargs = req.call_args.args[1]
        self.assertEqual(kwargs["generator"], "categorymembers")
        self.assertEqual(kwargs["prop"], "pageprops")
        self.assertEqual(kwargs["ppprop"], "wikibase_item")

    def test_discover_uses_generator_qids_without_extra_pageprops_calls(self):
        def pages(category):
            return [{"page_id": 11, "title": "Film", "wikidata_qid": "Q11"}]
        with patch("audit_indian_movie_growth.category_pages", side_effect=pages), \
             patch("audit_indian_movie_growth.resolve_page_qids") as extra, \
             patch("audit_indian_movie_growth.time.sleep"):
            movies, meta = discover(2026, 2026, 100, max_categories=1)
        self.assertEqual(movies[0]["wikidata_qid"], "Q11")
        self.assertEqual(meta["qid_resolution_failed_batches"], 0)
        extra.assert_not_called()

    def test_crawl_stops_at_first_rate_limit(self):
        errors = []
        def fetch(category):
            if "2026 Indian films" in category:
                return [{"page_id": 100, "title": "First Film"}]
            raise urllib.error.HTTPError("https://en.wikipedia.org", 429, "Too Many Requests", {}, None)

        with patch("audit_indian_movie_growth.category_pages", side_effect=fetch) as pages, \
             patch("audit_indian_movie_growth.resolve_page_qids", return_value=({}, 0, False)), \
             patch("audit_indian_movie_growth.time.sleep"):
            records, source = discover(2026, 2026, 8000, max_categories=13, category_offset=0)
        self.assertEqual(len(records), 1)
        self.assertEqual(pages.call_count, 2)
        self.assertEqual(source["categories_attempted"], 2)
        self.assertEqual(source["categories_failed"], 1)
        self.assertEqual(source["halt_reason"], "wikipedia_rate_limit")
        self.assertEqual(source["next_category_offset"], 1)

    def test_category_offset_and_small_batch(self):
        with patch("audit_indian_movie_growth.category_pages",
                   return_value=[{"page_id": 222, "title": "Film"}]) as pages, \
             patch("audit_indian_movie_growth.resolve_page_qids", return_value=({}, 0, False)), \
             patch("audit_indian_movie_growth.time.sleep"):
            records, source = discover(2025, 2026, 8000, max_categories=2, category_offset=13)
        self.assertEqual(len(records), 1)
        self.assertEqual(source["category_offset"], 13)
        self.assertEqual(source["next_category_offset"], 15)
        self.assertEqual(source["halt_reason"], "category_batch_complete")
        self.assertEqual(pages.call_count, 2)

    def test_429_is_distinct_from_other_errors(self):
        self.assertTrue(rate_limited(urllib.error.HTTPError("https://test", 429, "rate", {}, None)))
        self.assertFalse(rate_limited(urllib.error.HTTPError("https://test", 503, "busy", {}, None)))

    def test_pageprops_stops_after_first_rate_limit(self):
        with patch("audit_indian_movie_growth.wiki.request_json",
                   side_effect=urllib.error.HTTPError("https://test", 429, "rate", {}, None)) as req, \
             patch("audit_indian_movie_growth.time.sleep"):
            resolved, failed, blocked = resolve_page_qids(list(range(1, 201)))
        self.assertEqual((resolved, failed, blocked), ({}, 1, True))
        self.assertEqual(req.call_count, 1)

    def test_two_languages_same_page_not_two_new_films(self):
        report = audit([
            candidate(99, "Q999", "Bilingual Film", 2024, "Telugu", True),
            candidate(99, "Q999", "Bilingual Film", 2024, "Tamil", True),
        ], [], [])
        self.assertEqual(report["summary"]["new_indian_category_candidates"], 1)
        self.assertEqual(report["summary"]["duplicate_inside_discovery"], 1)


if __name__ == "__main__":
    unittest.main()
