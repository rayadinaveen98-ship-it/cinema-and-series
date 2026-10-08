import unittest

from scripts.p2_artwork_discovery import TitleIdentity, discover_candidates, match_title, normalize_title


class P2ArtworkDiscoveryTests(unittest.TestCase):
    def test_title_normalization(self):
        self.assertEqual(normalize_title("RRR: The Movie!"), "rrr the movie")

    def test_exact_match_gets_year_bonus(self):
        score, basis = match_title(TitleIdentity("t1", "RRR", 2022), "rrr", 2022)
        self.assertEqual(score, 110)
        self.assertEqual(basis, "EXACT_NORMALIZED_TITLE+YEAR")

    def test_mismatched_title_is_rejected(self):
        score, _ = match_title(TitleIdentity("t1", "RRR", 2022), "RRR 2", 2022)
        self.assertEqual(score, 0)

    def test_discovery_is_deterministic_and_bounded(self):
        records = [
            {
                "source_title": "RRR",
                "source_year": 2022,
                "source_asset_id": "File:B.jpg",
                "source_page_url": "https://commons.wikimedia.org/wiki/File:B.jpg",
                "delivery_url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/B.jpg",
                "role": "POSTER",
                "attribution": "Author",
                "license_identifier": "CC BY-SA 4.0",
                "rights_evidence_url": "https://commons.wikimedia.org/wiki/Commons:Licensing",
                "language": "te",
                "territory": "IN",
                "width": 1000,
                "height": 1500,
                "discovered_at": "2026-10-08T00:00:00Z",
            }
        ]
        identity = TitleIdentity("t1", "RRR", 2022)
        a = discover_candidates(identity, records, source_key="wikimedia_commons")
        b = discover_candidates(identity, records, source_key="wikimedia_commons")
        self.assertEqual(a, b)
        self.assertEqual(a[0].match_score, 110)

    def test_discovery_cannot_bypass_missing_rights(self):
        record = {
            "source_title": "RRR",
            "source_year": 2022,
            "source_asset_id": "File:X.jpg",
            "source_page_url": "https://commons.wikimedia.org/wiki/File:X.jpg",
            "delivery_url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/X.jpg",
            "role": "POSTER",
            "license_identifier": None,
            "rights_evidence_url": None,
            "discovered_at": "2026-10-08T00:00:00Z",
        }
        with self.assertRaises(ValueError):
            discover_candidates(TitleIdentity("t1", "RRR", 2022), [record], source_key="wikimedia_commons")


if __name__ == "__main__":
    unittest.main()
