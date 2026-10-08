import unittest

from scripts.p2_artwork_adapters import ArtworkCandidate, normalize_candidate, validate_candidate


class P2ArtworkAdapterTests(unittest.TestCase):
    def base(self):
        return ArtworkCandidate(
            source_key="wikimedia_commons",
            source_asset_id="File:Example.jpg",
            source_page_url="https://commons.wikimedia.org/wiki/File:Example.jpg",
            delivery_url="https://commons.wikimedia.org/wiki/Special:Redirect/file/Example.jpg",
            role="POSTER",
            attribution="Example author",
            license_identifier="CC BY-SA 4.0",
            rights_evidence_url="https://commons.wikimedia.org/wiki/Commons:Licensing",
            language="en",
            territory="IN",
            width=1000,
            height=1500,
            discovered_at="2026-10-08T00:00:00Z",
        )

    def test_valid_candidate_passes(self):
        validate_candidate(self.base())

    def test_missing_rights_evidence_fails_closed(self):
        c = self.base()
        validate_candidate(c.__class__(**{**c.__dict__, "rights_evidence_url": None}))

    def test_wrong_host_fails_closed(self):
        c = self.base()
        validate_candidate(c.__class__(**{**c.__dict__, "delivery_url": "https://example.com/a.jpg"}))

    def test_normalization_is_deterministic(self):
        raw = {
            "source_asset_id": " File:Example.jpg ",
            "source_page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
            "delivery_url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Example.jpg",
            "role": "POSTER",
            "attribution": " Example author ",
            "license_identifier": "CC BY-SA 4.0",
            "rights_evidence_url": "https://commons.wikimedia.org/wiki/Commons:Licensing",
            "language": " en ",
            "territory": " IN ",
            "width": 1000,
            "height": 1500,
            "discovered_at": "2026-10-08T00:00:00Z",
        }
        a = normalize_candidate(raw, source_key="wikimedia_commons")
        b = normalize_candidate(raw, source_key="wikimedia_commons")
        self.assertEqual(a, b)
        self.assertEqual(a.aspect_ratio, 2 / 3)


if __name__ == "__main__":
    unittest.main()
