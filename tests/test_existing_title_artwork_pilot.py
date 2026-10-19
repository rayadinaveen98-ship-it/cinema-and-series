"""Artwork pilot: existing exact identities, zero production writes/publication."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.existing_title_artwork_pilot import (
    MAX_TITLES, API, COMMONS, build_pilot,
    commons_by_filename, p18_by_qid, read_wrangle_rows, select_existing_titles,
)


def row(qid, table="catalogue_titles", year=2024, has_poster=0):
    return {"id": table + "-" + qid, "wikidata_qid": qid, "title": "Film " + qid,
            "year": year, "country_code": "IN", "language_name": "Telugu",
            "has_poster": has_poster}


class ExistingArtworkPilotTests(unittest.TestCase):
    def test_d1_wrangle_result_variants_and_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            for payload in ([{"results": [{"id": "a"}]}],
                            {"result": [{"results": [{"id": "a"}]}]},
                            {"results": [{"id": "a"}]}):
                path.write_text(json.dumps(payload))
                self.assertEqual(read_wrangle_rows(path), [{"id": "a"}])
            path.write_text('{"error": "not found"}')
            with self.assertRaises(ValueError):
                read_wrangle_rows(path)

    def test_exact_ids_de_dupe_and_skip_existing_posters(self):
        samples = {
            "movies": [row("Q101", "movies"), row("Q102", "movies", has_poster=1)],
            "catalogue_titles": [row("Q101"), row("Q103"), row("not-a-qid")],
            "series_titles": [row("Q104", "series_titles")],
        }
        selected = select_existing_titles(samples)
        self.assertEqual([(r["source_table"], r["wikidata_qid"]) for r in selected],
                         [("movies", "Q101"), ("catalogue_titles", "Q103"),
                          ("series_titles", "Q104")])
        self.assertEqual(selected[0]["source_id"], "movies-Q101")
        with self.assertRaises(ValueError):
            select_existing_titles(samples, 101)

    def test_source_calls_only_wikidata_and_commons_and_preserve_rights_hold(self):
        calls = []
        def fetch(url, params):
            calls.append((url, params))
            if url == API:
                return {"entities": {
                    "Q101": {"id": "Q101", "claims": {"P18": [{
                        "mainsnak": {"datavalue": {"value": "Film A poster.jpg"}}
                    }]}},
                    "Q103": {"id": "Q103", "claims": {"P18": [
                        {"mainsnak": {"datavalue": {"value": "a.jpg"}}},
                        {"mainsnak": {"datavalue": {"value": "b.jpg"}}},
                    ]}},
                }}
            if url == COMMONS:
                return {"query": {"pages": {"7": {
                    "title": "File:Film A poster.jpg",
                    "imageinfo": [{
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/poster.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Film_A_poster.jpg",
                        "width": 640, "height": 960,
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
                            "Artist": {"value": "<b>Artist</b>"},
                        },
                    }],
                }}}}
            raise AssertionError("Unapproved source URL")
        samples = {"movies": [row("Q101", "movies")],
                   "catalogue_titles": [row("Q103")],
                   "series_titles": [row("Q104", "series_titles")]}
        report = build_pilot(samples, fetch=fetch)
        self.assertEqual(report["selected_count"], 3)
        self.assertEqual(report["d1_writes"], 0)
        self.assertFalse(report["publication_performed"])
        self.assertTrue(report["all_titles_from_existing_d1_snapshot"])
        self.assertEqual(report["status_counts"]["REVIEW_IMAGE_AND_RIGHTS"], 1)
        self.assertEqual(report["status_counts"]["NO_SINGLE_P18_CLAIM"], 2)
        a = report["candidates"][0]
        self.assertEqual(a["image"]["license"], "CC BY-SA 4.0")
        self.assertEqual(a["image"]["artist"], "Artist")
        self.assertEqual(a["match_basis"], "EXACT_WIKIDATA_QID_P18")
        self.assertFalse(a["approved_for_publication"])
        self.assertTrue(all(base in {API, COMMONS} for base, _ in calls))
        self.assertEqual(len([base for base, _ in calls if base == COMMONS]), 1)

    def test_unlicensed_or_missing_file_is_not_approved(self):
        def fetch(url, params):
            if url == API:
                return {"entities": {"Q201": {"id": "Q201", "claims": {"P18": [{
                    "mainsnak": {"datavalue": {"value": "Unknown poster.jpg"}}
                }]}}}}
            return {"query": {"pages": {"1": {"title": "File:Unknown poster.jpg",
                "imageinfo": [{
                    "thumburl": "https://upload.wikimedia.org/file.jpg",
                    "descriptionurl": "https://commons.wikimedia.org/wiki/File:Unknown_poster.jpg",
                    "extmetadata": {},
                }]}}}}
        report = build_pilot({"movies": [row("Q201", "movies")],
                              "catalogue_titles": [], "series_titles": []}, fetch=fetch)
        self.assertEqual(report["status_counts"], {"RIGHTS_REVIEW_NEEDED": 1})
        self.assertFalse(report["candidates"][0]["approved_for_publication"])

    def test_offline_mode_never_calls_any_source(self):
        def forbidden(*args):
            raise AssertionError("Network must not run in offline mode")
        result = build_pilot({"movies": [row("Q11", "movies")],
                              "catalogue_titles": [], "series_titles": []},
                             fetch=forbidden, discover=False)
        self.assertEqual(result["status_counts"], {"NO_SINGLE_P18_CLAIM": 1})
        self.assertEqual(result["d1_writes"], 0)

    def test_workflow_only_reads_no_updates_and_one_time_schedule(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/existing-title-artwork-100-pilot.yml").read_text()
        self.assertIn('2026-10-20', workflow)
        self.assertIn('10 3 20 10', workflow)
        self.assertIn('LIMIT 180;', workflow)
        self.assertIn("publication_performed", workflow)
        self.assertNotIn("migrations apply", workflow)
        self.assertNotIn("INSERT INTO", workflow)
        self.assertNotIn("UPDATE catalogue_titles", workflow)
        self.assertNotIn("DELETE FROM", workflow)
        self.assertNotIn("tmdb.org", workflow.lower())
        self.assertNotIn("themoviedb", workflow.lower())
        self.assertEqual(MAX_TITLES, 100)


if __name__ == "__main__":
    unittest.main()
