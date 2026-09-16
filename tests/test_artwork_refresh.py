import unittest
from unittest.mock import patch

from scripts import artwork_refresh


class ArtworkRefreshTests(unittest.TestCase):
    def test_youtube_video_id_accepts_watch_and_short_links(self):
        self.assertEqual(
            artwork_refresh.youtube_video_id("https://www.youtube.com/watch?v=L7qEKA-e2qI"),
            "L7qEKA-e2qI",
        )
        self.assertEqual(
            artwork_refresh.youtube_video_id("https://youtu.be/bedocP4nRAo"),
            "bedocP4nRAo",
        )

    def test_youtube_video_id_rejects_unrelated_hosts(self):
        self.assertIsNone(artwork_refresh.youtube_video_id("https://example.com/watch?v=L7qEKA-e2qI"))

    def test_meta_parser_finds_open_graph_artwork(self):
        parser = artwork_refresh.MetaImageParser()
        parser.feed(
            '<html><head><meta property="og:image" content="/assets/poster.jpg">'
            '<meta name="twitter:image" content="https://cdn.example.com/social.jpg"></head></html>'
        )
        self.assertEqual(parser.images, ["/assets/poster.jpg", "https://cdn.example.com/social.jpg"])
        self.assertEqual(
            artwork_refresh.https_url(parser.images[0], "https://studio.example.com/movies/example"),
            "https://studio.example.com/assets/poster.jpg",
        )

    def test_root_homepage_is_not_used_as_movie_artwork(self):
        with patch.object(artwork_refresh, "request_bytes") as request:
            self.assertIsNone(artwork_refresh.official_page_artwork("https://studio.example.com/"))
            request.assert_not_called()

    def test_build_sql_never_overwrites_first_party_with_wikimedia(self):
        wiki = [
            {
                "wikidata_qid": "Q10",
                "poster_url": "https://commons.example/poster.jpg",
                "backdrop_url": None,
                "artwork_source": "wikimedia_commons",
                "artwork_source_url": "https://commons.example/wiki/File:Poster.jpg",
            }
        ]
        official = [
            {
                "title": "Example",
                "release_date": "2026-10-16",
                "poster_url": None,
                "backdrop_url": "https://i.ytimg.com/vi/example/maxresdefault.jpg",
                "artwork_source": "official_youtube",
                "artwork_source_url": "https://www.youtube.com/watch?v=example1",
            }
        ]
        sql = artwork_refresh.build_sql(wiki, official)
        self.assertIn("poster_url = COALESCE(poster_url", sql)
        self.assertIn("artwork_source = 'official_youtube'", sql)
        self.assertIn("WHERE wikidata_qid = 'Q10'", sql)
        self.assertIn("WHERE title = 'Example' AND release_date = '2026-10-16'", sql)

    def test_https_url_rejects_non_https_assets(self):
        self.assertIsNone(artwork_refresh.https_url("http://cdn.example.com/poster.jpg"))
        self.assertIsNone(artwork_refresh.https_url("javascript:alert(1)"))


if __name__ == "__main__":
    unittest.main()
