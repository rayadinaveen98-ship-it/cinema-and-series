import unittest

from scripts import p2_artwork_coverage_audit as audit


class P2ArtworkCoverageAuditTests(unittest.TestCase):
    def sample(self):
        return {
            "titles": [
                {"media_type": "movie", "source_table": "movies", "source_id": "m1", "language": "Telugu"},
                {"media_type": "series", "source_table": "series_titles", "source_id": "s1", "language": "Hindi"},
                {"media_type": "movie", "source_table": "movies", "source_id": "m2", "language": "Telugu"},
            ],
            "candidates": [
                {
                    "media_type": "movie",
                    "source_table": "movies",
                    "source_id": "m1",
                    "source_key": "commons",
                    "source_asset_id": "File:A.jpg",
                    "presentation_role": "poster",
                    "publication_state": "OPEN_LICENSE_VERIFIED",
                    "rights_basis": "OPEN_LICENSE",
                    "hosting_mode": "EXTERNAL_ALLOWED",
                    "attribution_required": True,
                    "attribution_text": "Creator / CC BY-SA",
                },
                {
                    "media_type": "movie",
                    "source_table": "movies",
                    "source_id": "m1",
                    "source_key": "official_page",
                    "source_asset_id": "og-1",
                    "presentation_role": "backdrop",
                    "publication_state": "DISCOVERED",
                    "rights_basis": "NO_RIGHTS_BASIS",
                    "hosting_mode": "REFERENCE_ONLY",
                },
                {
                    "media_type": "series",
                    "source_table": "series_titles",
                    "source_id": "s1",
                    "source_key": "provider",
                    "source_asset_id": "p-1",
                    "presentation_role": "backdrop",
                    "publication_state": "PROVIDER_LICENSED",
                    "rights_basis": "PROVIDER_CONTRACT",
                    "hosting_mode": "PROVIDER_CDN",
                    "territory_restrictions": ["IN"],
                },
                {
                    "media_type": "movie",
                    "source_table": "movies",
                    "source_id": "m2",
                    "source_key": "commons",
                    "source_asset_id": "File:B.jpg",
                    "presentation_role": "poster",
                    "publication_state": "OPEN_LICENSE_VERIFIED",
                    "rights_basis": "OPEN_LICENSE",
                    "hosting_mode": "EXTERNAL_ALLOWED",
                    "ambiguous_link": True,
                },
            ],
        }

    def test_report_separates_discovery_from_publishable_coverage(self):
        report = audit.build_report(self.sample())
        self.assertTrue(report["read_only"])
        self.assertEqual(report["input"], {"titles": 3, "candidates": 4})
        self.assertEqual(report["coverage"]["with_candidate"], 3)
        self.assertEqual(report["coverage"]["with_publishable_poster"], 1)
        self.assertEqual(report["coverage"]["with_publishable_backdrop"], 1)
        self.assertEqual(report["coverage"]["fallback_only"], 1)
        self.assertEqual(report["candidates"]["publishable_image_candidates"], 2)
        self.assertEqual(report["candidates"]["ambiguous_link_candidates"], 1)
        self.assertEqual(report["candidates"]["rejected_or_no_rights_basis_candidates"], 1)

    def test_state_rights_pairing_fails_closed(self):
        candidate = self.sample()["candidates"][0].copy()
        candidate["rights_basis"] = "PUBLIC_DOMAIN"
        self.assertFalse(audit.is_publishable_image_candidate(candidate))

    def test_embed_and_reference_only_do_not_count_as_image_publication(self):
        candidate = self.sample()["candidates"][0].copy()
        for mode in ("EMBED_ONLY", "REFERENCE_ONLY"):
            candidate["hosting_mode"] = mode
            with self.subTest(mode=mode):
                self.assertFalse(audit.is_publishable_image_candidate(candidate))

    def test_missing_required_attribution_fails_closed(self):
        candidate = self.sample()["candidates"][0].copy()
        candidate["attribution_text"] = ""
        self.assertFalse(audit.is_publishable_image_candidate(candidate))

    def test_takedown_expiry_territory_and_ambiguous_links_fail_closed(self):
        base = self.sample()["candidates"][0]
        for field in ("takedown", "expired", "ambiguous_link"):
            candidate = base.copy()
            candidate[field] = True
            with self.subTest(field=field):
                self.assertFalse(audit.is_publishable_image_candidate(candidate))
        candidate = base.copy()
        candidate["territory_eligible"] = False
        self.assertFalse(audit.is_publishable_image_candidate(candidate))

    def test_candidate_for_unknown_title_is_rejected(self):
        payload = self.sample()
        payload["candidates"][0]["source_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown title identity"):
            audit.build_report(payload)

    def test_duplicate_title_identity_is_rejected(self):
        payload = self.sample()
        payload["titles"].append(dict(payload["titles"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate title identity"):
            audit.build_report(payload)

    def test_duplicate_candidate_rate_and_provider_concentration_are_measured(self):
        payload = self.sample()
        payload["candidates"].append(dict(payload["candidates"][0]))
        report = audit.build_report(payload)
        self.assertEqual(report["candidates"]["duplicate_candidate_occurrences"], 1)
        self.assertEqual(report["provider_concentration"]["largest_candidate_source"], "commons")
        self.assertEqual(report["publishable_by_rights_basis"]["OPEN_LICENSE"], 2)

    def test_media_and_language_coverage_are_separate(self):
        report = audit.build_report(self.sample())
        self.assertEqual(report["coverage_by_media_type"]["movie"]["titles"], 2)
        self.assertEqual(report["coverage_by_media_type"]["series"]["titles"], 1)
        self.assertEqual(report["coverage_by_language"]["Telugu"]["titles"], 2)
        self.assertEqual(report["coverage_by_language"]["Hindi"]["titles"], 1)


if __name__ == "__main__":
    unittest.main()
