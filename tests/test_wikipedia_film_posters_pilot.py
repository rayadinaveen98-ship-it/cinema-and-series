"""Film-page image discovery regression, never a title-guessing publisher."""
import unittest
from scripts.wikipedia_film_posters_pilot import (
    WIKIDATA, article_sitelinks, film_page_images, merge_images,
)


def snapshot():
    return {
        "schema": "existing-title-artwork-pilot-v1", "d1_writes": 0,
        "publication_performed": False, "selected_count": 2,
        "candidates": [
            {"wikidata_qid": "Q1234", "source_table": "movies", "source_id": "m-Q1234",
             "title": "Telugu Film", "status": "NO_SINGLE_P18_CLAIM",
             "image": None, "approved_for_publication": False, "production_written": False},
            {"wikidata_qid": "Q888", "source_table": "movies", "source_id": "m-Q888",
             "title": "Missing Film", "status": "NO_SINGLE_P18_CLAIM",
             "image": None, "approved_for_publication": False, "production_written": False}
        ]
    }


class WikipediaFilmPosterPilotTests(unittest.TestCase):
    def test_exact_wikidata_sitelink_not_title_search(self):
        def fetch(url, params):
            self.assertEqual(url, WIKIDATA)
            self.assertEqual(params["props"], "sitelinks")
            self.assertEqual(params["ids"], "Q1234|Q888")
            self.assertNotIn("search", params)
            return {"entities": {"Q1234": {"id": "Q1234", "sitelinks": {
                "enwiki": {"title": "Telugu Film (2026 film)"},
                "tewiki": {"title": "తెలుగు సినిమా"},
            }}, "Q888": {"id": "Q888", "sitelinks": {}}}}
        links, failed = article_sitelinks(["Q1234", "Q888"], fetch)
        self.assertEqual(links, {"Q1234": ("enwiki", "Telugu Film (2026 film)")})
        self.assertEqual(failed, 0)

    def test_rejects_wrong_page_qid_and_uses_film_article_poster(self):
        def fetch(url, params):
            self.assertEqual(url, "https://en.wikipedia.org/w/api.php")
            self.assertEqual(params["pilicense"], "any")
            self.assertIn("pageprops", params["prop"])
            return {"query": {"pages": {
                "1": {"title": "Telugu Film (2026 film)",
                      "pageprops": {"wikibase_item": "Q1234"},
                      "pageimage": "Film theatrical poster.jpg",
                      "thumbnail": {"source": "https://upload.wikimedia.org/wikipedia/en/thumb/a/abc/poster.jpg",
                                    "width": 480, "height": 700}},
                "2": {"title": "Wrong Film", "pageprops": {"wikibase_item": "Q9999"},
                      "thumbnail": {"source": "https://upload.wikimedia.org/unrelated.jpg"}},
            }}}
        found, failed = film_page_images({"Q1234": ("enwiki", "Telugu Film (2026 film)")}, fetch)
        self.assertEqual(failed, 0)
        self.assertEqual(list(found), ["Q1234"])
        self.assertEqual(found["Q1234"]["rights_status"], "REVIEW_REQUIRED_NON_FREE_POSSIBLE")
        self.assertIn("Telugu_Film", found["Q1234"]["file_page_url"])

    def test_merge_never_approves_nonfree_or_writes_database(self):
        photo = {
            "image_url": "https://upload.wikimedia.org/wikipedia/en/thumb/poster.jpg",
            "file_page_url": "https://en.wikipedia.org/wiki/Telugu_Film",
            "width": 500, "height": 800,
            "match_basis": "EXACT_PAGEPROP_WIKIBASE_ITEM",
            "pageimage_filename": "Film poster.jpg",
        }
        out = merge_images(snapshot(), {"Q1234": photo}, 0, 0)
        self.assertEqual(out["discovery_stats"]["wikipedia_new_article_images"], 1)
        self.assertEqual(out["discovery_stats"]["portrait_article_images"], 1)
        self.assertEqual(out["discovery_stats"]["total_visual_candidates"], 1)
        self.assertEqual(out["candidates"][0]["status"], "WIKIPEDIA_ARTICLE_IMAGE_REVIEW")
        self.assertFalse(out["candidates"][0]["approved_for_publication"])
        self.assertFalse(out["candidates"][0]["production_written"])
        self.assertEqual(out["d1_writes"], 0)
        self.assertFalse(out["publication_performed"])
        self.assertEqual(out["candidates"][1]["status"], "NO_SINGLE_P18_CLAIM")
        broken = snapshot()
        broken["publication_performed"] = True
        with self.assertRaises(ValueError):
            merge_images(broken, {}, 0, 0)

    def test_page_api_failures_are_explicit(self):
        def bad_fetch(url, params):
            raise OSError("rate limited")
        links, failed = article_sitelinks(["Q1234"], bad_fetch)
        self.assertEqual(links, {})
        self.assertEqual(failed, 1)


if __name__ == "__main__":
    unittest.main()
