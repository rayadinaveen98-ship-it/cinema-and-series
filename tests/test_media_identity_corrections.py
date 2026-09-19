import unittest

from scripts import media_identity_corrections as identity


class MediaIdentityCorrectionsTests(unittest.TestCase):
    def test_registry_has_durable_evidence(self):
        registry = identity.load_registry()
        self.assertIn("Q3049630", registry)
        self.assertIn("Q3146368", registry)
        for correction in registry.values():
            self.assertTrue(correction["evidence"]["entity_url"].startswith("https://www.wikidata.org/wiki/Q"))
            self.assertEqual(correction["evidence"]["verified_run_id"], "35420861375")

    def test_manga_series_is_excluded_from_movie_and_series(self):
        self.assertFalse(identity.is_media_type_allowed("Q3049630", "movie"))
        self.assertFalse(identity.is_media_type_allowed("Q3049630", "series"))

    def test_dual_typed_miniseries_is_canonical_series(self):
        self.assertFalse(identity.is_media_type_allowed("Q3146368", "movie"))
        self.assertTrue(identity.is_media_type_allowed("Q3146368", "series"))

    def test_unknown_qid_is_untouched(self):
        self.assertTrue(identity.is_media_type_allowed("Q999999999", "movie"))
        self.assertTrue(identity.is_media_type_allowed("Q999999999", "series"))

    def test_filter_rows_reports_suppression(self):
        kept, suppressed = identity.filter_rows(
            [
                {"wikidata_qid": "Q3049630", "title": "Manga"},
                {"wikidata_qid": "Q42", "title": "Ordinary"},
            ],
            "series",
        )
        self.assertEqual([row["wikidata_qid"] for row in kept], ["Q42"])
        self.assertEqual(suppressed, ["Q3049630"])


if __name__ == "__main__":
    unittest.main()
