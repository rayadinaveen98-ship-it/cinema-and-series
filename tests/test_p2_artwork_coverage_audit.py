import unittest

from scripts import p2_artwork_coverage_audit as audit


class P2ArtworkCoverageAuditTests(unittest.TestCase):
    def publishable_proof(self, *, url="https://example.test/image.jpg"):
        return {
            "link_exact": True,
            "rights_verified_at": "2026-09-28T00:00:00Z",
            "validity_eligible": True,
            "takedown_clear": True,
            "territory_eligible": True,
            "delivery_url": url,
            "attribution_required": False,
        }

    def sample(self):
        return {
            "snapshot_version": audit.SNAPSHOT_VERSION,
            "audit_context": {
                "territory": "IN",
                "evaluated_at": "2026-09-28T00:00:00Z",
            },
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
                    **self.publishable_proof(url="https://commons.test/a.jpg"),
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
                    **self.publishable_proof(url="https://provider.test/p-1.jpg"),
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
                    **self.publishable_proof(url="https://commons.test/b.jpg"),
                    "ambiguous_link": True,
                },
            ],
        }

    def reverse_dict_order(self, value):
        if isinstance(value, dict):
            return {
                key: self.reverse_dict_order(value[key])
                for key in reversed(list(value.keys()))
            }
        if isinstance(value, list):
            return [self.reverse_dict_order(item) for item in value]
        return value

    def test_report_separates_discovery_from_publishable_coverage(self):
        report = audit.build_report(self.sample())
        self.assertTrue(report["read_only"])
        self.assertEqual(report["audit_version"], "p2-artwork-coverage-audit-v3")
        self.assertEqual(report["snapshot_version"], audit.SNAPSHOT_VERSION)
        self.assertEqual(
            report["audit_context"],
            {"territory": "IN", "evaluated_at": "2026-09-28T00:00:00Z"},
        )
        self.assertEqual(report["input_attestation"]["algorithm"], "sha256-canonical-json-v1")
        self.assertEqual(len(report["input_attestation"]["sha256"]), 64)
        self.assertEqual(report["input"], {"titles": 3, "candidates": 4})
        self.assertEqual(report["coverage"]["with_candidate"], 3)
        self.assertEqual(report["coverage"]["with_publishable_poster"], 1)
        self.assertEqual(report["coverage"]["with_publishable_backdrop"], 1)
        self.assertEqual(report["coverage"]["fallback_only"], 1)
        self.assertEqual(report["candidates"]["publishable_image_candidates"], 2)
        self.assertEqual(report["candidates"]["ambiguous_link_candidates"], 1)
        self.assertEqual(report["candidates"]["rejected_or_no_rights_basis_candidates"], 1)
        self.assertEqual(report["publishability_rejection_reasons"]["ambiguous_link"], 1)

    def test_audit_context_is_required_and_strict(self):
        payload = self.sample()
        payload.pop("audit_context")
        with self.assertRaisesRegex(ValueError, "audit_context"):
            audit.build_report(payload)

        for territory in ("in", "IND", "I1", ""):
            payload = self.sample()
            payload["audit_context"]["territory"] = territory
            with self.subTest(territory=territory):
                with self.assertRaisesRegex(ValueError, "territory"):
                    audit.build_report(payload)

        for evaluated_at in (
            "2026-09-28T00:00:00+00:00",
            "2026-09-28 00:00:00Z",
            "2026-02-30T00:00:00Z",
            "",
        ):
            payload = self.sample()
            payload["audit_context"]["evaluated_at"] = evaluated_at
            with self.subTest(evaluated_at=evaluated_at):
                with self.assertRaisesRegex(ValueError, "evaluated_at"):
                    audit.build_report(payload)

    def test_snapshot_version_is_required_and_exact(self):
        for value in (None, "", "p2-artwork-coverage-snapshot-v0"):
            payload = self.sample()
            if value is None:
                payload.pop("snapshot_version")
            else:
                payload["snapshot_version"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "snapshot_version"):
                    audit.build_report(payload)

    def test_input_attestation_is_stable_across_dict_key_order(self):
        payload = self.sample()
        reordered = self.reverse_dict_order(payload)
        self.assertEqual(audit.snapshot_sha256(payload), audit.snapshot_sha256(reordered))
        self.assertEqual(
            audit.build_report(payload)["input_attestation"]["sha256"],
            audit.build_report(reordered)["input_attestation"]["sha256"],
        )

    def test_context_change_changes_input_attestation(self):
        payload = self.sample()
        original = audit.snapshot_sha256(payload)

        changed_territory = self.sample()
        changed_territory["audit_context"]["territory"] = "US"
        self.assertNotEqual(original, audit.snapshot_sha256(changed_territory))

        changed_time = self.sample()
        changed_time["audit_context"]["evaluated_at"] = "2026-09-28T01:00:00Z"
        self.assertNotEqual(original, audit.snapshot_sha256(changed_time))

    def test_state_rights_pairing_fails_closed(self):
        candidate = self.sample()["candidates"][0].copy()
        candidate["rights_basis"] = "PUBLIC_DOMAIN"
        self.assertFalse(audit.is_publishable_image_candidate(candidate))
        self.assertIn("state_rights_pairing", audit.publishability_failures(candidate))

    def test_missing_positive_safety_evidence_fails_closed(self):
        base = self.sample()["candidates"][0]
        cases = {
            "link_exact": "exact_link_unverified",
            "rights_verified_at": "rights_verification_missing",
            "validity_eligible": "validity_unverified",
            "takedown_clear": "takedown_unverified",
            "territory_eligible": "territory_unverified",
            "delivery_url": "delivery_url",
            "attribution_required": "attribution_requirement_unknown",
        }
        for field, reason in cases.items():
            candidate = base.copy()
            candidate.pop(field, None)
            with self.subTest(field=field):
                self.assertFalse(audit.is_publishable_image_candidate(candidate))
                self.assertIn(reason, audit.publishability_failures(candidate))

    def test_invalid_or_non_https_delivery_url_fails_closed(self):
        base = self.sample()["candidates"][0]
        for value in ("", "http://example.test/a.jpg", "not-a-url"):
            candidate = base.copy()
            candidate["delivery_url"] = value
            with self.subTest(value=value):
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
        self.assertIn("attribution_missing", audit.publishability_failures(candidate))

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

    def test_malformed_candidate_vocabulary_is_rejected(self):
        mutations = {
            "publication_state": "UNKNOWN_STATE",
            "rights_basis": "UNKNOWN_RIGHTS",
            "hosting_mode": "UNKNOWN_HOST",
            "presentation_role": "thumbnail",
        }
        for field, value in mutations.items():
            payload = self.sample()
            payload["candidates"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    audit.build_report(payload)

    def test_candidate_requires_stable_source_evidence_identity(self):
        payload = self.sample()
        candidate = payload["candidates"][0]
        candidate.pop("source_asset_id")
        candidate.pop("source_page_url", None)
        with self.assertRaisesRegex(ValueError, "source_asset_id or source_page_url"):
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
