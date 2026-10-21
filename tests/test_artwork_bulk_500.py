"""Bulk 500-title discovery must preserve exact source identity and never publish."""
import tempfile
import unittest
from pathlib import Path

from scripts.artwork_bulk_500 import MAX_TITLES, select_500, discover, as_csv


def row(table, i, language="Telugu"):
    return {
        "id": f"{table}-Q{i}",
        "wikidata_qid": f"Q{i}",
        "title": f"Movie {i}",
        "year": 2026,
        "language_name": language,
        "country_code": "IN",
        "has_poster": 0,
    }


class BulkArtworkTests(unittest.TestCase):
    def test_selects_500_actual_existing_unique_ids_across_three_tables(self):
        samples = {
            "movies": [row("movies", i) for i in range(100, 500)],
            "catalogue_titles": [row("catalogue_titles", i) for i in range(400, 850)],
            "series_titles": [row("series_titles", i) for i in range(800, 1100)],
        }
        items = select_500(samples)
        self.assertEqual(len(items), MAX_TITLES)
        self.assertEqual(len({r["wikidata_qid"] for r in items}), 500)
        self.assertEqual(
            [sum(x["source_table"] == t for x in items)
             for t in ("movies", "catalogue_titles", "series_titles")],
            [275, 150, 75],
        )
        self.assertTrue(all(not item["approved_for_publication"] for item in items))

    def test_fills_unavailable_category_slots_without_duplicating(self):
        samples = {
            "movies": [row("movies", i) for i in range(100, 600)],
            "catalogue_titles": [],
            "series_titles": [row("series_titles", i) for i in range(700, 750)],
        }
        items = select_500(samples)
        self.assertEqual(len(items), 500)
        self.assertEqual(sum(x["source_table"] == "movies" for x in items), 450)
        self.assertEqual(sum(x["source_table"] == "series_titles" for x in items), 50)

    def test_excludes_invalid_qid_bad_year_and_already_illustrated(self):
        good = row("movies", 999)
        unwanted = [
            {**good, "wikidata_qid": "invalid"},
            {**good, "title": "Q999"},
            {**good, "year": None},
            {**good, "has_poster": 1},
            {**good, "id": ""},
            {**good, "language_name": "Unknown"},
        ]
        picked = select_500({"movies": unwanted + [good]}, limit=10)
        self.assertEqual([r["wikidata_qid"] for r in picked], ["Q999"])
        for invalid in (0, 501, -1):
            with self.assertRaises(ValueError):
                select_500({"movies": [good]}, limit=invalid)

    def test_exact_qid_poster_discovery_stays_unlicensed(self):
        qid = "Q880"
        source = {
            "source": "wikipedia_article_pageimage",
            "image_url": "https://upload.wikimedia.org/wikipedia/en/p/p.jpg",
            "file_page_url": "https://en.wikipedia.org/wiki/Movie_880_(2026_film)",
            "pageimage_filename": "Movie_880_poster.jpg",
            "width": 500, "height": 750,
        }
        report = discover(
            {"movies": [row("movies", 880)]}, limit=1,
            get_links=lambda qs: ({qid: ("enwiki", "Movie 880 (2026 film)")}, 0),
            get_images=lambda links: ({qid: source}, 0),
            get_p18=lambda qs: {},
            get_commons=lambda names: {},
        )
        self.assertEqual(report["selected_count"], 1)
        self.assertEqual(report["poster_candidates"], 1)
        self.assertEqual(report["publishable_posters"], 0)
        self.assertEqual(report["displayed_in_app"], 0)
        self.assertEqual(report["d1_writes"], 0)
        self.assertFalse(report["publication_performed"])
        self.assertFalse(report["candidates"][0]["approved_for_publication"])
        with tempfile.TemporaryDirectory() as tmp:
            csv = Path(tmp) / "result.csv"
            as_csv(report, csv)
            contents = csv.read_text(encoding="utf-8")
            self.assertIn("UNVERIFIED_NOT_FOR_PUBLICATION", contents)
            self.assertIn("Movie 880", contents)

    def test_media_and_year_mismatches_are_held_even_for_article_images(self):
        src = {
            "source": "wikipedia_article_pageimage",
            "image_url": "https://upload.wikimedia.org/wikipedia/en/p/p.jpg",
            "file_page_url": "https://en.wikipedia.org/wiki/Movie_881_(2025_TV_series)",
            "pageimage_filename": "Movie_881_poster.jpg",
            "width": 400, "height": 700,
        }
        report = discover(
            {"movies": [row("movies", 881)]}, limit=1,
            get_links=lambda qs: ({"Q881": ("enwiki", "Movie 881 (2025 TV series)")}, 0),
            get_images=lambda links: ({"Q881": src}, 0),
            get_p18=lambda qs: {}, get_commons=lambda names: {},
        )
        self.assertEqual(report["media_type_mismatch_holds"], 1)
        self.assertEqual(report["year_mismatch_holds"], 1)
        self.assertEqual(report["candidates"][0]["status"], "MEDIA_TYPE_MISMATCH_HOLD")

    def test_source_failures_do_not_turn_missing_images_into_success(self):
        report = discover(
            {"series_titles": [row("series_titles", 905)]}, limit=1,
            get_links=lambda qs: ({}, 1),
            get_images=lambda links: ({}, 0),
            get_p18=lambda qs: {}, get_commons=lambda names: {},
        )
        self.assertEqual(report["poster_candidates"], 0)
        self.assertEqual(report["source_errors"]["wikidata_sitelink_batches"], 1)
        self.assertEqual(report["status_counts"]["NO_IMAGE_FOUND"], 1)

    def test_empty_snapshot_fails_instead_of_claiming_500(self):
        with self.assertRaises(ValueError):
            discover({"movies": [], "catalogue_titles": [], "series_titles": []})


if __name__ == "__main__":
    unittest.main()
