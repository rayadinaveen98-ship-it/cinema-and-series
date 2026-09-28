import tempfile
import unittest
from pathlib import Path

from scripts import build_p2_artwork_audit_snapshot as builder
from scripts import p2_artwork_coverage_audit as audit


class P2ArtworkAuditSnapshotBuilderTests(unittest.TestCase):
    def titles(self):
        return [
            {"media_type": "series", "source_table": "series_titles", "source_id": "s1", "language": "Hindi"},
            {"media_type": "movie", "source_table": "movies", "source_id": "m2", "language": "Tamil"},
            {"media_type": "movie", "source_table": "movies", "source_id": "m1", "language": "Telugu"},
        ]

    def candidates(self):
        return [
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
                "link_exact": True,
                "rights_verified_at": "2026-09-28T00:00:00Z",
                "validity_eligible": True,
                "takedown_clear": True,
                "territory_eligible": True,
                "delivery_url": "https://provider.test/p-1.jpg",
                "attribution_required": False,
            },
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
                "link_exact": True,
                "rights_verified_at": "2026-09-28T00:00:00Z",
                "validity_eligible": True,
                "takedown_clear": True,
                "territory_eligible": True,
                "delivery_url": "https://commons.test/a.jpg",
                "attribution_required": True,
                "attribution_text": "Creator / CC BY-SA",
            },
            {
                "media_type": "movie",
                "source_table": "movies",
                "source_id": "m2",
                "source_key": "official_page",
                "source_asset_id": "og-2",
                "presentation_role": "poster",
                "publication_state": "DISCOVERED",
                "rights_basis": "NO_RIGHTS_BASIS",
                "hosting_mode": "REFERENCE_ONLY",
            },
        ]

    def build(self, titles=None, candidates=None, **overrides):
        return builder.build_snapshot(
            self.titles() if titles is None else titles,
            self.candidates() if candidates is None else candidates,
            territory=overrides.get("territory", "IN"),
            evaluated_at=overrides.get("evaluated_at", "2026-09-28T00:00:00Z"),
        )

    def test_builder_emits_versioned_context_bound_valid_snapshot(self):
        snapshot = self.build()
        self.assertEqual(snapshot["snapshot_version"], audit.SNAPSHOT_VERSION)
        self.assertEqual(
            snapshot["audit_context"],
            {"territory": "IN", "evaluated_at": "2026-09-28T00:00:00Z"},
        )
        report = audit.build_report(snapshot)
        self.assertEqual(report["input"], {"titles": 3, "candidates": 3})
        self.assertEqual(report["candidates"]["publishable_image_candidates"], 2)

    def test_builder_sorts_titles_and_candidates_deterministically(self):
        first = self.build()
        second = self.build(
            titles=list(reversed(self.titles())),
            candidates=list(reversed(self.candidates())),
        )
        self.assertEqual(first, second)
        self.assertEqual(audit.snapshot_sha256(first), audit.snapshot_sha256(second))
        self.assertEqual(builder.render_snapshot(first), builder.render_snapshot(second))
        self.assertEqual(
            [(row["media_type"], row["source_id"]) for row in first["titles"]],
            [("movie", "m1"), ("movie", "m2"), ("series", "s1")],
        )

    def test_candidate_duplicates_are_preserved_for_audit_measurement(self):
        candidates = self.candidates()
        candidates.append(dict(candidates[1]))
        snapshot = self.build(candidates=candidates)
        self.assertEqual(len(snapshot["candidates"]), 4)
        report = audit.build_report(snapshot)
        self.assertEqual(report["candidates"]["duplicate_candidate_occurrences"], 1)

    def test_duplicate_title_identity_fails(self):
        titles = self.titles()
        titles.append(dict(titles[0]))
        with self.assertRaisesRegex(ValueError, "duplicate title identity"):
            self.build(titles=titles)

    def test_unknown_candidate_title_fails(self):
        candidates = self.candidates()
        candidates[0]["source_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown title identity"):
            self.build(candidates=candidates)

    def test_malformed_candidate_fails_before_snapshot_output(self):
        candidates = self.candidates()
        candidates[0]["publication_state"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "publication_state"):
            self.build(candidates=candidates)

    def test_context_validation_is_shared_with_auditor(self):
        with self.assertRaisesRegex(ValueError, "territory"):
            self.build(territory="in")
        with self.assertRaisesRegex(ValueError, "evaluated_at"):
            self.build(evaluated_at="2026-09-28T00:00:00+00:00")

    def test_input_files_have_strict_single_key_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "titles.json"
            good.write_text('{"titles": []}', encoding="utf-8")
            self.assertEqual(builder._load_records(good, "titles"), [])

            bad = root / "bad.json"
            bad.write_text('{"titles": [], "extra": true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one top-level field"):
                builder._load_records(bad, "titles")


if __name__ == "__main__":
    unittest.main()
