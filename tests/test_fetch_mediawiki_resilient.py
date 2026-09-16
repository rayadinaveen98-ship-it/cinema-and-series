import importlib.util
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "fetch_mediawiki_resilient.py"
spec = importlib.util.spec_from_file_location("fetch_mediawiki_resilient", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class MediaWikiResilientTests(unittest.TestCase):
    def test_request_backoff_retries_429(self):
        error = urllib.error.HTTPError("https://example.test", 429, "Too Many Requests", {}, None)
        calls = []

        def fake_request(*args, **kwargs):
            calls.append(1)
            if len(calls) < 3:
                raise error
            return {"ok": True}

        sleeps = []
        with patch.object(module.base, "request_json", side_effect=fake_request):
            payload = module.request_with_backoff(
                "https://example.test",
                {"action": "query"},
                sleep_fn=sleeps.append,
            )
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [5, 12])

    def test_entity_resolution_keeps_later_success_after_failed_batch(self):
        qid_to_title = {f"Q{index}": f"Film {index}" for index in range(1, 26)}
        second_batch = {
            "entities": {
                f"Q{index}": {"id": f"Q{index}", "claims": {}, "labels": {"en": {"value": f"Film {index}"}}}
                for index in range(21, 26)
            }
        }
        with patch.object(module, "request_with_backoff", side_effect=[RuntimeError("throttled"), second_batch]):
            entities, reports = module.fetch_entities_by_qid(qid_to_title, sleep_fn=lambda _: None)

        self.assertEqual([entity["id"] for entity in entities], ["Q21", "Q22", "Q23", "Q24", "Q25"])
        self.assertEqual(reports[0]["status"], "deferred")
        self.assertEqual(reports[1]["status"], "ok")

    def test_wikipedia_qid_resolution_keeps_partial_batches(self):
        titles = [f"Film {index}" for index in range(1, 46)]
        second_payload = {
            "query": {
                "pages": [
                    {"title": f"Film {index}", "pageprops": {"wikibase_item": f"Q{index}"}}
                    for index in range(41, 46)
                ]
            }
        }
        with patch.object(module, "request_with_backoff", side_effect=[RuntimeError("temporary"), second_payload]):
            resolved, reports = module.resolve_qids_via_wikipedia(titles, sleep_fn=lambda _: None)

        self.assertEqual(resolved, {f"Q{index}": f"Film {index}" for index in range(41, 46)})
        self.assertEqual(reports[0]["status"], "deferred")
        self.assertEqual(reports[1]["status"], "ok")

    def test_normalization_survives_label_lookup_failure(self):
        entity = {
            "id": "Q99",
            "_discovered_title": "Global Film",
            "claims": {
                "P577": [
                    {"mainsnak": {"datavalue": {"value": {"time": "+2020-05-10T00:00:00Z", "precision": 11}}}}
                ],
                "P364": [
                    {"mainsnak": {"datavalue": {"value": {"entity-type": "item", "id": "Q1860"}}}}
                ],
            },
            "labels": {},
            "sitelinks": {},
        }
        seed = module.base.Seed("Category:2020 Japanese films", "JP", None, "country-JP")
        with patch.object(module, "fetch_labels_resilient", return_value=({}, [{"status": "deferred"}])):
            movies, reports = module.normalize_entities_resilient([entity], {"Global Film": [seed]}, sleep_fn=lambda _: None)

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]["country_code"], "JP")
        self.assertEqual(movies[0]["languages"], ["Unknown"])
        self.assertEqual(movies[0]["release_date"], "2020-05-10")
        self.assertEqual(reports, [{"status": "deferred"}])


if __name__ == "__main__":
    unittest.main()
