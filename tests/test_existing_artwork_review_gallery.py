"""Artwork gallery remains source-only, readable, and safe with untrusted metadata."""
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.render_existing_artwork_review import (
    csv_rows, image_shape, render_html, safe_csv_cell, safe_rights_url, safe_url,
)

ROOT = Path(__file__).resolve().parents[1]


def pilot(title="RRR", license_url="https://creativecommons.org/licenses/by/4.0/"):
    return {
        "schema": "existing-title-artwork-pilot-v1",
        "read_only": True, "d1_writes": 0, "publication_performed": False,
        "selected_count": 1,
        "candidates": [{
            "source_table": "catalogue_titles", "source_id": "catalogue-Q123",
            "wikidata_qid": "Q123", "title": title, "year": 2022,
            "language": "Telugu", "country": "IN", "status": "REVIEW_IMAGE_AND_RIGHTS",
            "file_name": "Film poster.jpg", "approved_for_publication": False,
            "production_written": False,
            "image": {
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/example.png",
                "file_page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                "width": 800, "height": 1200, "license": "CC BY 4.0",
                "license_url": license_url, "artist": "Example artist",
            },
        }],
    }


class ExistingArtworkReviewGalleryTests(unittest.TestCase):
    def test_contact_sheet_is_safe_read_only_and_not_auto_approved(self):
        page = render_html(pilot())
        self.assertIn("Existing-title artwork review", page)
        self.assertIn("Q123", page)
        self.assertIn("portrait", page)
        self.assertIn("REVIEW IMAGE AND RIGHTS", page)
        self.assertIn("not approved for publication", page)
        self.assertIn("Content-Security-Policy", page)
        self.assertIn("loading=\"lazy\"", page)
        self.assertIn("CC BY 4.0", page)
        self.assertNotIn("<script", page)
        self.assertEqual(csv_rows(pilot())[0]["review_decision"], "PENDING")

    def test_scripts_and_cross_origin_images_are_escaped_or_blocked(self):
        payload = pilot(title='"><img src=x onerror=alert(1)>',
                        license_url='javascript:alert(1)')
        payload["candidates"][0]["image"]["image_url"] = "https://example.com/stolen.png"
        payload["candidates"][0]["image"]["file_page_url"] = "https://example.com/fake"
        payload["candidates"][0]["image"]["artist"] = '<svg onload="alert(1)">'
        page = render_html(payload)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", page)
        self.assertNotIn('<img src=x onerror', page)
        self.assertNotIn("<svg", page)
        self.assertNotIn('href="javascript:', page)
        self.assertNotIn("https://example.com/stolen.png", page)
        self.assertNotIn('href="https://example.com/fake', page)
        self.assertIn("No usable thumbnail", page)

    def test_shaped_images_are_not_mislabeled_as_posters(self):
        self.assertEqual(image_shape({"width": 600, "height": 1000}), "portrait")
        self.assertEqual(image_shape({"width": 1600, "height": 900}), "landscape")
        self.assertEqual(image_shape({"width": 1000, "height": 1100}), "square-ish")
        self.assertEqual(image_shape({"width": 0, "height": 1000}), "unknown")
        self.assertEqual(image_shape({}), "unknown")
        self.assertEqual(image_shape({"width": "nan", "height": 1000}), "unknown")
        self.assertIn("NOT verified theatrical posters", render_html(pilot()))

    def test_rejects_unsafe_pilot_and_identity_drift(self):
        for prop, value in (("read_only", False), ("publication_performed", True),
                            ("d1_writes", 1), ("selected_count", 0)):
            p = pilot()
            p[prop] = value
            with self.assertRaises(ValueError):
                render_html(p)
        for prop in ("approved_for_publication", "production_written"):
            p = pilot()
            p["candidates"][0][prop] = True
            with self.assertRaises(ValueError):
                csv_rows(p)
        p = pilot()
        p["candidates"].append(p["candidates"][0].copy())
        p["selected_count"] = 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            render_html(p)

    def test_third_party_rights_links_https_only_and_csv_formula_safe(self):
        self.assertEqual(safe_url("https://upload.wikimedia.org/a.jpg", {"upload.wikimedia.org"}),
                         "https://upload.wikimedia.org/a.jpg")
        self.assertEqual(safe_url("https://upload.wikimedia.org.evil.com/a.jpg",
                                  {"upload.wikimedia.org"}), "")
        self.assertEqual(safe_url("http://upload.wikimedia.org/a.jpg", {"upload.wikimedia.org"}), "")
        self.assertEqual(safe_rights_url("javascript:alert(1)"), "")
        self.assertEqual(safe_rights_url("https://creativecommons.org/licenses/by/4.0/"),
                         "https://creativecommons.org/licenses/by/4.0/")
        self.assertEqual(safe_csv_cell("=1+1"), "'=1+1")
        self.assertEqual(safe_csv_cell("   @danger"), "'   @danger")
        self.assertEqual(safe_csv_cell("safe film title"), "safe film title")
        p = pilot("=HYPERLINK(\"https://evil.test\")")
        self.assertTrue(csv_rows(p)[0]["title"].startswith("'="))

    def test_cli_exports_both_gallery_and_review_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            input_path, html_path, csv_path = (d / n for n in ("pilot.json", "gallery.html", "review.csv"))
            input_path.write_text(json.dumps(pilot()), encoding="utf-8")
            run = subprocess.run([
                sys.executable, str(ROOT / "scripts/render_existing_artwork_review.py"),
                "--input", str(input_path), "--html", str(html_path), "--csv", str(csv_path),
            ], check=True, capture_output=True, text=True)
            self.assertIn("ARTWORK_REVIEW_GALLERY=", run.stdout)
            self.assertIn("Existing-title artwork review", html_path.read_text(encoding="utf-8"))
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_id"], "catalogue-Q123")
            self.assertEqual(rows[0]["review_decision"], "PENDING")


if __name__ == "__main__":
    unittest.main()
