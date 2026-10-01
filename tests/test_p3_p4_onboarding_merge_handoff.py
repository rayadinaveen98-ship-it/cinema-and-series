import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
P3 = ROOT / "docs/10-execution/IDENTITY_AND_PROFILES_P3_PREP.md"
P4 = ROOT / "docs/10-execution/FIRST_TIME_ONBOARDING_P4_PREP.md"
HANDOFF = ROOT / "docs/10-execution/P3_P4_ONBOARDING_MERGE_HANDOFF.md"


class P3P4OnboardingMergeHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p3 = P3.read_text(encoding="utf-8")
        cls.p4 = P4.read_text(encoding="utf-8")
        cls.handoff = HANDOFF.read_text(encoding="utf-8")

    def test_overlay_stays_prep_only(self):
        self.assertIn("DO NOT IMPLEMENT BEFORE P3/P4 AUTHORIZATION", self.handoff)
        self.assertIn("creates no migration, endpoint, UI, D1 write path", self.handoff)
        self.assertIn("PREPARED / DO NOT IMPLEMENT BEFORE P2 EXIT", self.p3)
        self.assertIn("PREPARED / DO NOT IMPLEMENT BEFORE P3 EXIT", self.p4)

    def test_existing_parent_contracts_require_preservation_and_idempotency(self):
        self.assertIn("Signing in must never silently discard local state", self.p3)
        self.assertIn("Upgrade must be safe to retry", self.p3)
        self.assertIn("preserve valid local answers", self.p4)
        self.assertIn("do not force the user to repeat completed steps", self.p4)

    def test_cloud_complete_cannot_be_reopened_by_local_merge(self):
        self.assertIn("A completed cloud profile remains complete", self.handoff)
        self.assertIn("local onboarding progress does not reopen first-time onboarding", self.handoff)

    def test_in_progress_conflicts_are_explicit_not_timestamp_overwrites(self):
        self.assertIn("Client timestamps are not trusted to overwrite cloud state", self.handoff)
        self.assertIn("both have different valid values → create an explicit conflict", self.handoff)
        self.assertIn("do not choose by client timestamp", self.handoff)
        self.assertIn("needs_resolution", self.handoff)

    def test_seed_union_is_bounded_by_revalidation(self):
        self.assertIn("Seed titles are safe to union only after validation", self.handoff)
        self.assertIn("revalidate against the merged `content_scope`", self.handoff)
        self.assertIn("recompute distinct eligible seed count", self.handoff)

    def test_merge_id_is_idempotent_and_reuse_with_different_payload_fails(self):
        self.assertIn("Replaying the same `merge_id` with the same canonical payload returns the same merge result", self.handoff)
        self.assertIn("Reusing a consumed `merge_id` with a materially different payload fails closed", self.handoff)

    def test_local_state_is_not_deleted_on_auth_success_alone(self):
        self.assertIn("must not clear the local profile merely because Google authentication succeeded", self.handoff)
        self.assertIn("only after the server returns a durable merge result of `resolved`", self.handoff)
        self.assertIn("If the request fails, times out, or returns `rejected`, keep local state", self.handoff)

    def test_reset_is_not_account_or_interaction_deletion(self):
        self.assertIn("Reset onboarding” is not account deletion, logout, or local-profile deletion", self.handoff)
        self.assertIn("saves/watched history", self.handoff)
        self.assertIn("canonical catalogue data", self.handoff)

    def test_merge_never_owns_canonical_catalogue_truth(self):
        self.assertIn("No merge may write canonical catalogue, recommendation, artwork, genre, person, or title metadata", self.handoff)


if __name__ == "__main__":
    unittest.main()
