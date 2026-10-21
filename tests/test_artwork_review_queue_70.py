"""Read-only human triage for the archived 70-title artwork pilot."""
import unittest
from scripts.artwork_review_queue_70 import make_queue


def candidate(qid, title, year=2026, table="movies", poster=True, suffix=None):
    kind = suffix or ("TV_series" if table == "series_titles" else "film")
    article = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_") + f"_({year}_{kind})"
    image = {
        "source": "wikipedia_article_pageimage",
        "file_page_url": article,
        "pageimage_filename": title.replace(" ", "_") + "_poster.jpg",
        "image_url": "https://upload.wikimedia.org/wikipedia/en/thumb/example.jpg",
        "width": 600 if poster else 1000,
        "height": 900 if poster else 500,
    }
    return {
        "source_table": table, "source_id": "wd-" + qid, "wikidata_qid": qid,
        "title": title, "year": year, "language": "Telugu", "country": "IN",
        "media_type": "series" if table == "series_titles" else "movie",
        "image": image,
        "poster_candidate": image if poster else None,
        "backdrop_candidate": None if poster else image,
        "approved_for_publication": False,
        "production_written": False,
    }


def snapshot(rows):
    return {
        "schema": "existing-title-artwork-pilot-v1",
        "selected_count": len(rows),
        "candidates": rows,
        "d1_writes": 0, "publication_performed": False,
    }


class ManualArtworkQueueTests(unittest.TestCase):
    def test_identity_flags_come_before_poster_leads(self):
        good = candidate("Q100", "Peddi")
        wrong_year = candidate("Q101", "Dragon", year=2027)
        wrong_year["image"]["file_page_url"] = "https://en.wikipedia.org/wiki/Dragon_(2025_film)"
        wrong_type = candidate("Q102", "Panchanama", suffix="TV_series")
        wrong_type["image"]["file_page_url"] = "https://en.wikipedia.org/wiki/Panchanama_(2026_TV_series)"
        missing = candidate("Q103", "Missing")
        missing["image"] = None
        missing["poster_candidate"] = None
        report = make_queue(snapshot([good, missing, wrong_year, wrong_type]))
        self.assertEqual(report["selected_count"], 4)
        self.assertEqual(report["unresolved_identity_flags"], 2)
        self.assertEqual([row["review_priority"] for row in report["queue"]], [0, 0, 1, 3])
        self.assertEqual(report["poster_leads"], 3)
        self.assertEqual(report["ready_for_publication"], 0)
        self.assertEqual(report["database_reads"], 0)
        self.assertTrue(all(r["approved_for_publication"] is False for r in report["queue"]))

    def test_backdrop_not_mistaken_for_a_poster(self):
        result = make_queue(snapshot([candidate("Q109", "Backdrop only", poster=False)]))
        self.assertEqual(result["queue"][0]["action"], "BACKDROP_ONLY_FIND_POSTER")
        self.assertEqual(result["poster_leads"], 0)
        self.assertEqual(result["backdrop_leads"], 1)

    def test_untrusted_or_previous_publication_fails_closed(self):
        item = candidate("Q120", "Untrusted")
        item["approved_for_publication"] = True
        with self.assertRaises(ValueError):
            make_queue(snapshot([item]))
        item["approved_for_publication"] = False
        item["image"]["source"] = "random_cdn"
        with self.assertRaises(ValueError):
            make_queue(snapshot([item]))

    def test_unlicensed_images_never_become_app_artwork(self):
        row = candidate("Q121", "Pilot")
        result = make_queue(snapshot([row]))
        self.assertEqual(result["queue"][0]["rights_status"], "UNVERIFIED_NOT_FOR_PUBLICATION")
        self.assertFalse(result["publication_performed"])
        self.assertEqual(result["database_writes"], 0)


if __name__ == "__main__":
    unittest.main()
