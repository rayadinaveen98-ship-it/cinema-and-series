"""Offline visual gallery should remain source-only and escape untrusted metadata."""
import unittest
from scripts.artwork70_html_gallery import render_gallery, safe_url
from scripts.artwork_review_queue_70 import make_queue
from tests.test_artwork_review_queue_70 import candidate, snapshot


def report(items):
    return {
        "schema": "artwork70-manual-review-queue-v1",
        "selected_count": len(items),
        "action_counts": {
            "RESOLVE_IDENTITY_BEFORE_IMAGE_REVIEW": 0,
            "CHECK_ORIGINAL_POSTER_AND_USAGE_RIGHTS": len(items),
            "BACKDROP_ONLY_FIND_POSTER": 0,
            "NO_POSTER_FOUND_FIND_TRUSTED_SOURCE": 0,
        },
        "queue": items,
        "database_reads": 0, "database_writes": 0,
        "ready_for_publication": 0,
        "publication_performed": False,
    }


def entry():
    return {
        "title": "Peddi", "year": 2026, "language": "Telugu",
        "media_type": "movie", "wikidata_qid": "Q1200",
        "action": "CHECK_ORIGINAL_POSTER_AND_USAGE_RIGHTS",
        "poster_page_url": "https://en.wikipedia.org/wiki/Peddi",
        "poster_preview_url": "https://upload.wikimedia.org/wikipedia/commons/p/poster.jpg",
        "backdrop_page_url": "", "backdrop_preview_url": "",
        "rights_status": "UNVERIFIED_NOT_FOR_PUBLICATION",
        "approved_for_publication": False,
    }


class GalleryTests(unittest.TestCase):
    def test_produces_searchable_cards_with_links_and_warnings(self):
        page = render_gallery(report([entry()]))
        self.assertIn('id="search"', page)
        self.assertIn('data-filter="poster"', page)
        self.assertIn("Peddi", page)
        self.assertIn('loading="lazy"', page)
        self.assertIn('href="https://en.wikipedia.org/wiki/Peddi"', page)
        self.assertIn("Do not publish", page)
        self.assertNotIn("APPROVED_FOR_PUBLICATION", page)

    def test_escapes_html_and_blocks_untrusted_remote_images(self):
        unsafe = {**entry(),
                  "title": '</script><script>alert("xss")</script>',
                  "poster_preview_url": "https://upload.wikimedia.org.evil.org/a.jpg",
                  "poster_page_url": "javascript:alert(1)"}
        page = render_gallery(report([unsafe]))
        self.assertNotIn('</script><script>alert("xss")</script>', page)
        self.assertIn("&lt;/script&gt;&lt;script&gt;", page)
        self.assertNotIn("https://upload.wikimedia.org.evil.org", page)
        self.assertNotIn("javascript:alert", page)
        self.assertEqual(safe_url("https://upload.wikimedia.org.evil.org/test.jpg", thumbnail=True), "")
        self.assertEqual(safe_url("https://upload.wikimedia.org@evil.org/test.jpg", thumbnail=True), "")
        self.assertEqual(safe_url("https://upload.wikimedia.org/wikipedia/a.jpg", thumbnail=True),
                         "https://upload.wikimedia.org/wikipedia/a.jpg")

    def test_backdrop_only_is_visible_without_adding_fake_poster(self):
        archived = candidate("Q1300", "Backdrop only", poster=False)
        queue = make_queue(snapshot([archived]))
        self.assertEqual(queue["queue"][0]["action"], "BACKDROP_ONLY_FIND_POSTER")
        self.assertTrue(queue["queue"][0]["backdrop_preview_url"])
        page = render_gallery(queue)
        self.assertIn("Backdrop source", page)
        self.assertIn('src="https://upload.wikimedia.org/wikipedia/en/thumb/example.jpg"', page)
        self.assertNotIn("Rights verified", page)

    def test_never_accepts_published_or_invalid_report(self):
        good = entry()
        with self.assertRaises(ValueError):
            render_gallery(report([{**good, "approved_for_publication": True}]))
        with self.assertRaises(ValueError):
            render_gallery({**report([good]), "database_writes": 1})
        with self.assertRaises(ValueError):
            render_gallery({**report([good]), "ready_for_publication": 1})
        with self.assertRaises(ValueError):
            render_gallery({**report([good]), "publication_performed": True})


if __name__ == "__main__":
    unittest.main()
