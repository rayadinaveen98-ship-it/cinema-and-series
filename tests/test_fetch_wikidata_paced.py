import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "fetch_wikidata_paced.py"
spec = importlib.util.spec_from_file_location("fetch_wikidata_paced", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class PacedWikidataTests(unittest.TestCase):
    def setUp(self):
        self.original_delay = module.base.INTER_SHARD_DELAY_SECONDS
        self.original_attempts = module.base.MAX_ATTEMPTS_PER_SHARD

    def tearDown(self):
        module.base.INTER_SHARD_DELAY_SECONDS = self.original_delay
        module.base.MAX_ATTEMPTS_PER_SHARD = self.original_attempts

    def test_default_outage_spacing_is_at_least_one_minute(self):
        with patch.dict(os.environ, {}, clear=True):
            delay = module.configure()
        self.assertEqual(delay, 65)
        self.assertEqual(module.base.INTER_SHARD_DELAY_SECONDS, 65)
        self.assertEqual(module.base.MAX_ATTEMPTS_PER_SHARD, 1)

    def test_spacing_is_safely_clamped(self):
        with patch.dict(os.environ, {"WDQS_INTER_SHARD_DELAY_SECONDS": "10"}, clear=True):
            self.assertEqual(module.configure(), 60)
        with patch.dict(os.environ, {"WDQS_INTER_SHARD_DELAY_SECONDS": "999"}, clear=True):
            self.assertEqual(module.configure(), 180)

    def test_invalid_spacing_falls_back_to_default(self):
        with patch.dict(os.environ, {"WDQS_INTER_SHARD_DELAY_SECONDS": "not-a-number"}, clear=True):
            self.assertEqual(module.configure(), 65)


if __name__ == "__main__":
    unittest.main()
