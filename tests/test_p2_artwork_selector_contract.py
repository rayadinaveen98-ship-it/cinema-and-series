import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "worker/artwork.ts"
MIGRATION = ROOT / "migrations/0023_artwork_foundation_v2.sql"

class P2ArtworkSelectorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selector = SELECTOR.read_text(encoding="utf-8")
        cls.migration = MIGRATION.read_text(encoding="utf-8")

    def test_public_states_and_pairings_are_locked(self):
        for state, basis in {
            "OPEN_LICENSE_VERIFIED": "OPEN_LICENSE",
            "PUBLIC_DOMAIN_VERIFIED": "PUBLIC_DOMAIN",
            "PROVIDER_LICENSED": "PROVIDER_CONTRACT",
            "RIGHTS_APPROVED": "RIGHTSHOLDER_PERMISSION",
            "PROMOTIONAL_PERMISSION_VERIFIED": "PROMOTIONAL_PERMISSION",
        }.items():
            self.assertIn(f'{state}: "{basis}"', self.selector)

    def test_non_public_and_unsafe_hosting_fail_closed(self):
        self.assertIn("if (PUBLIC_PAIRINGS[candidate.publicationState] !== candidate.rightsBasis) return false;", self.selector)
        self.assertIn("if (!PUBLIC_HOSTING.has(candidate.hostingMode)) return false;", self.selector)
        self.assertIn('if (candidate.takedownStatus !== "clear") return false;', self.selector)
        self.assertIn("if (!candidate.rightsVerifiedAt || !atOrBefore(candidate.rightsVerifiedAt, nowIso)) return false;", self.selector)

    def test_context_and_delivery_checks_fail_closed(self):
        self.assertIn("if (candidate.validFrom && after(candidate.validFrom, nowIso)) return false;", self.selector)
        self.assertIn("if (candidate.validUntil && !after(candidate.validUntil, nowIso)) return false;", self.selector)
        self.assertIn("if (candidate.territoryCode && candidate.territoryCode !== territory) return false;", self.selector)
        self.assertIn("if (!httpsUrl(candidate.deliveryUrl)) return false;", self.selector)
        self.assertIn("if (candidate.attributionRequired && !candidate.attributionText?.trim()) return false;", self.selector)

    def test_rights_first_deterministic_order(self):
        self.assertIn("localeRank(a, language, territory), rightsRank(a)", self.selector)
        self.assertIn("...visualRank(a, requestedAspectRatio), a.assetId", self.selector)
        self.assertIn(".sort((a, b) => compareCandidates(a, b, language, territory, requestedAspectRatio))", self.selector)

    def test_fallback_is_first_class(self):
        self.assertIn("isFallback: true", self.selector)
        self.assertIn("hasPublishablePoster", self.selector)
        self.assertIn("hasPublishableBackdrop", self.selector)

    def test_schema_has_shared_media_identity_and_idempotent_link_key(self):
        self.assertIn("media_type TEXT NOT NULL CHECK (media_type IN ('movie','series'))", self.migration)
        self.assertIn("source_table TEXT NOT NULL", self.migration)
        self.assertIn("source_id TEXT NOT NULL", self.migration)
        self.assertIn("asset_id TEXT NOT NULL REFERENCES artwork_assets(id)", self.migration)
        self.assertIn("presentation_role TEXT NOT NULL CHECK (presentation_role IN ('poster','backdrop'))", self.migration)
        self.assertIn("UNIQUE (", self.migration)
        self.assertIn("language_code,", self.migration)
        self.assertIn("territory_code", self.migration)

    def test_public_states_require_verification_evidence(self):
        self.assertIn("publication_state NOT IN (", self.migration)
        self.assertIn("OR rights_verified_at IS NOT NULL", self.migration)

if __name__ == "__main__":
    unittest.main()
