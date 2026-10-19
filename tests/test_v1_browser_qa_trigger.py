"""Regression guard: mobile/browser QA must protect active V1 changes."""
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[1] / ".github/workflows/phase2-browser-qa.yml").read_text(encoding="utf-8")


class BrowserQATriggerTests(unittest.TestCase):
    def test_main_and_pull_requests_are_covered(self):
        self.assertIn("branches: [main]", WORKFLOW)
        self.assertIn("  pull_request:", WORKFLOW)
        self.assertNotIn("feature/phase2-pr-b-accessibility-20261018", WORKFLOW)
        for trigger in ('"src/**"', '"worker/**"', '"tests/browser/**"', '"playwright.config.mjs"'):
            self.assertEqual(WORKFLOW.count(trigger), 2)

    def test_local_browser_tests_are_not_connected_to_production_d1(self):
        self.assertIn("npx playwright test", WORKFLOW)
        self.assertIn("npx playwright install --with-deps chromium", WORKFLOW)
        self.assertIn("cinema-series-phase2-browser-qa", WORKFLOW)
        self.assertNotIn("CLOUDFLARE_API_TOKEN", WORKFLOW)
        self.assertNotIn("wrangler d1", WORKFLOW)
        config = (Path(__file__).resolve().parents[1] / "playwright.config.mjs").read_text(encoding="utf-8")
        for device in ("desktop-chromium", "tablet-chromium", "mobile-chromium", "small-mobile-chromium"):
            self.assertIn(device, config)


if __name__ == "__main__":
    unittest.main()
