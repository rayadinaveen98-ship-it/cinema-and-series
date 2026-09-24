import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "docs/10-execution/ARTWORK_FOUNDATION_P2_PREP.md"
REVIEW = ROOT / "docs/10-execution/ARTWORK_FOUNDATION_P2_SCHEMA_SELECTOR_REVIEW.md"
BASELINE = ROOT / "docs/02-sources/ARTWORK_PUBLICATION_BASELINE_V1.md"
P1_STATUS = ROOT / "docs/10-execution/RECOMMENDATION_METADATA_FOUNDATION_P1_STATUS.md"
MIGRATIONS = ROOT / "migrations"

PUBLIC_STATES = (
    "OPEN_LICENSE_VERIFIED",
    "PUBLIC_DOMAIN_VERIFIED",
    "PROVIDER_LICENSED",
    "RIGHTS_APPROVED",
    "PROMOTIONAL_PERMISSION_VERIFIED",
)

NON_PUBLIC_STATES = (
    "DISCOVERED",
    "PENDING_REVIEW",
    "REJECTED",
    "EXPIRED",
    "TAKEDOWN_PENDING",
    "TAKEN_DOWN",
)

PAIRINGS = {
    "OPEN_LICENSE_VERIFIED": "OPEN_LICENSE",
    "PUBLIC_DOMAIN_VERIFIED": "PUBLIC_DOMAIN",
    "PROVIDER_LICENSED": "PROVIDER_CONTRACT",
    "RIGHTS_APPROVED": "RIGHTSHOLDER_PERMISSION",
    "PROMOTIONAL_PERMISSION_VERIFIED": "PROMOTIONAL_PERMISSION",
}


class P2ArtworkPrepContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prep = PREP.read_text(encoding="utf-8")
        cls.review = REVIEW.read_text(encoding="utf-8")
        cls.baseline = BASELINE.read_text(encoding="utf-8")
        cls.p1_status = P1_STATUS.read_text(encoding="utf-8")

    def test_p2_remains_blocked_while_p1_is_active(self):
        self.assertIn("DO NOT ACTIVATE BEFORE P1 EXIT", self.prep)
        self.assertIn("P1 must be formally COMPLETE", self.review)
        self.assertIn("It creates no migration number", self.review)

        if "PRODUCTION POPULATION IN PROGRESS" in self.p1_status:
            premature = []
            for path in MIGRATIONS.glob("*.sql"):
                match = re.match(r"^(\d{4})_", path.name)
                if not match:
                    continue
                if int(match.group(1)) > 22 and "artwork" in path.name.lower():
                    premature.append(path.name)
            self.assertEqual([], premature, f"P2 artwork migration exists before P1 exit: {premature}")

    def test_locked_public_states_are_preserved(self):
        for state in PUBLIC_STATES:
            with self.subTest(state=state):
                self.assertIn(state, self.baseline)
                self.assertIn(state, self.review)

    def test_non_public_states_are_explicitly_fail_closed(self):
        for state in NON_PUBLIC_STATES:
            with self.subTest(state=state):
                self.assertIn(state, self.review)
        self.assertIn("are always non-public", self.review)

    def test_public_state_rights_basis_pairings_are_explicit(self):
        for state, basis in PAIRINGS.items():
            with self.subTest(state=state, basis=basis):
                self.assertIn(f"`{state}` | `{basis}`", self.review)
        self.assertIn("Any other pairing fails closed", self.review)

    def test_selector_order_is_rights_first_and_deterministic(self):
        expected = (
            "exact title links -> public eligibility -> role -> territory -> locale -> "
            "rights/source preference -> visual suitability -> stable tie-break"
        )
        self.assertIn(expected, self.review)
        self.assertIn("Selection must not depend on database row order", self.review)
        self.assertIn("A lower-resolution eligible asset always beats an ineligible higher-resolution asset", self.review)

    def test_discovery_cannot_self_authorize_publication(self):
        self.assertIn("Adapters never provide a trusted `is_publishable=true` flag", self.review)
        self.assertIn("A discovery adapter must not assign a public `publication_state`", self.review)
        self.assertIn("Missing required rights metadata leaves the asset non-public", self.review)

    def test_youtube_and_p18_are_not_image_publication_shortcuts(self):
        self.assertIn("`Wikidata P18` is discovery/reconciliation only", self.review)
        self.assertIn("OpenGraph images and thumbnails are candidate discovery only by default", self.review)
        self.assertIn("`EMBED_ONLY` video authorization never converts the thumbnail", self.review)

    def test_zero_artwork_is_a_supported_product_state(self):
        self.assertIn("A title with zero eligible assets is valid and returns the CAS fallback", self.review)
        self.assertIn("A Cinema and Series record never depends on having a poster", self.baseline)


if __name__ == "__main__":
    unittest.main()
