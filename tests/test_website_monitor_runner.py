import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODULE_PATH = SCRIPTS / "website_monitor_runner.py"
spec = importlib.util.spec_from_file_location("website_monitor_runner", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class WebsiteMonitorRunnerTests(unittest.TestCase):
    def test_defaults_to_canonical_website_url(self):
        source = {
            "key": "example",
            "website_url": "https://www.studio.example/",
        }
        self.assertEqual(
            module.resolve_monitor_url(source, {}),
            "https://www.studio.example/",
        )

    def test_allows_same_normalized_host_seed(self):
        source = {
            "key": "example",
            "website_url": "https://www.studio.example/",
        }
        self.assertEqual(
            module.resolve_monitor_url(
                source,
                {
                    "mode": "automatic",
                    "monitor_url": "https://studio.example/news/releases",
                },
            ),
            "https://studio.example/news/releases",
        )

    def test_rejects_cross_domain_seed(self):
        source = {
            "key": "example",
            "website_url": "https://studio.example/",
        }
        with self.assertRaisesRegex(ValueError, "canonical first-party host"):
            module.resolve_monitor_url(
                source,
                {
                    "mode": "automatic",
                    "monitor_url": "https://mirror.example/news",
                },
            )

    def test_manual_mode_disables_scheduled_crawl(self):
        source = {
            "key": "example",
            "website_url": "https://studio.example/",
        }
        self.assertIsNone(
            module.resolve_monitor_url(
                source,
                {"mode": "manual", "reason": "blocked by first-party server"},
            )
        )

    def test_unknown_config_source_is_rejected(self):
        sources = [
            {
                "key": "example",
                "website_url": "https://studio.example/",
            }
        ]
        with self.assertRaisesRegex(ValueError, "unknown source keys"):
            module.build_monitor_plan(sources, {"not_registered": {"mode": "manual"}})

    def test_repository_monitor_config_is_valid_and_expected(self):
        registry = json.loads(module.REGISTRY.read_text(encoding="utf-8"))
        sources = [
            source
            for source in registry.get("sources", [])
            if source.get("active") and source.get("website_url")
        ]
        settings = module.load_monitor_config()
        plan, manual = module.build_monitor_plan(sources, settings)
        plan_by_key = {source["key"]: url for source, url in plan}
        manual_keys = {result["source_key"] for result in manual}

        self.assertEqual(
            plan_by_key["kvn_productions"],
            "https://www.kvnproductions.co.in/movies",
        )
        self.assertEqual(
            plan_by_key["t_series"],
            "https://www.tseries.com/news",
        )
        self.assertIn("zee_studios", manual_keys)
        self.assertNotIn("zee_studios", plan_by_key)


if __name__ == "__main__":
    unittest.main()
