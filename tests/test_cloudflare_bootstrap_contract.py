import unittest
from unittest.mock import patch

from scripts import cloudflare_bootstrap as bootstrap


class CloudflareBootstrapContractTests(unittest.TestCase):
    def test_existing_database_is_reused(self):
        with patch.object(
            bootstrap,
            "list_databases",
            return_value=[{"name": bootstrap.DB_NAME, "uuid": "existing-db-id"}],
        ), patch.object(bootstrap, "ALLOW_D1_CREATE", False), patch.object(
            bootstrap, "run_wrangler"
        ) as run_wrangler:
            self.assertEqual(bootstrap.resolve_database_id(), "existing-db-id")
            run_wrangler.assert_not_called()

    def test_missing_database_fails_closed_by_default(self):
        with patch.object(bootstrap, "list_databases", return_value=[]), patch.object(
            bootstrap, "ALLOW_D1_CREATE", False
        ), patch.object(bootstrap, "run_wrangler") as run_wrangler:
            with self.assertRaisesRegex(RuntimeError, "refusing implicit creation"):
                bootstrap.resolve_database_id()
            run_wrangler.assert_not_called()

    def test_database_creation_requires_explicit_opt_in(self):
        with patch.object(
            bootstrap,
            "list_databases",
            side_effect=[[], [{"name": bootstrap.DB_NAME, "uuid": "new-db-id"}]],
        ), patch.object(bootstrap, "ALLOW_D1_CREATE", True), patch.object(
            bootstrap, "run_wrangler"
        ) as run_wrangler:
            self.assertEqual(bootstrap.resolve_database_id(), "new-db-id")
            run_wrangler.assert_called_once_with(
                "d1", "create", bootstrap.DB_NAME, "--location=apac"
            )

    def test_duplicate_named_databases_fail_closed(self):
        with patch.object(
            bootstrap,
            "list_databases",
            return_value=[
                {"name": bootstrap.DB_NAME, "uuid": "one"},
                {"name": bootstrap.DB_NAME, "uuid": "two"},
            ],
        ), patch.object(bootstrap, "ALLOW_D1_CREATE", False):
            with self.assertRaisesRegex(RuntimeError, "Expected exactly one D1 database"):
                bootstrap.resolve_database_id()

    def test_explicit_creation_must_resolve_to_exactly_one_database(self):
        with patch.object(
            bootstrap,
            "list_databases",
            side_effect=[[], []],
        ), patch.object(bootstrap, "ALLOW_D1_CREATE", True), patch.object(
            bootstrap, "run_wrangler"
        ):
            with self.assertRaisesRegex(RuntimeError, "after explicit creation"):
                bootstrap.resolve_database_id()


if __name__ == "__main__":
    unittest.main()
