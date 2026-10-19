"""Guard against accidental full catalogue scans in automated API smoke jobs.

The smoke workflows deliberately do not use a simulated D1 instance: their
GETs run against production. These tests enforce that only the initial
catalogue check requests global facets and stats.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CatalogueSmokeReadBudgetTests(unittest.TestCase):
    def test_public_smoke_uses_lightweight_pages_except_initial_full_catalogue(self):
        source = (ROOT / ".github/workflows/public-movie-api-smoke.yml").read_text()
        path_block = source.split("          paths = (", 1)[1].split("          )", 1)[0]
        paths = re.findall(r'"(/api/(?:movies|series)[^"]+)"', path_block)
        self.assertGreaterEqual(len(paths), 8, "Expected broad production smoke coverage")
        full = [url for url in paths if "meta=0" not in url]
        self.assertEqual(full, ["/api/movies?scope=all&limit=60&offset=0"])
        self.assertIn("/api/movies?scope=all&limit=60&offset=60&meta=0", paths)
        self.assertIn("/api/series?limit=60&offset=60&meta=0", paths)
        self.assertIn("page_only_metadata_contract", source)
        # Path strings for pagination and India/year assertions must still
        # reference the paths actually present in the paths tuple.
        self.assertIn('pages.get("/api/movies?scope=all&country=IN&limit=10&offset=0&meta=0")', source)
        self.assertIn('pages.get("/api/movies?scope=all&country=IN&year=2024&limit=40&offset=0&meta=0")', source)

    def test_deploy_still_checks_full_first_page_but_pagination_omits_metadata(self):
        source = (ROOT / ".github/workflows/deploy-cloudflare.yml").read_text()
        self.assertIn('catalogue = get_json("/api/movies?scope=all&limit=60&offset=0")', source)
        self.assertIn('get_json(f"/api/movies?scope=all&official=1&limit=200&offset={offset}&meta=0")', source)
        self.assertIn('payload.get("metadataLevel") != "page-only"', source)
        self.assertNotIn('get_json(f"/api/movies?scope=all&official=1&limit=200&offset={offset}")', source)


if __name__ == "__main__":
    unittest.main()
