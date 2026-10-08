import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_p2_production_artwork_snapshot import rows_from_wrangle_payload


class P2ProductionArtworkSnapshotTests(unittest.TestCase):
    def test_extracts_rows_from_wranger_result_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.json"
            path.write_text(
                json.dumps({"success": True, "result": [{"results": [{"id": "wd-Q1"}]}]}),
                encoding="utf-8",
            )
            self.assertEqual([{"id": "wd-Q1"}], rows_from_wrangle_payload(path))

    def test_extracts_rows_from_direct_statement_list_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.json"
            path.write_text(
                json.dumps([{"results": [{"id": "series-1"}]}]),
                encoding="utf-8",
            )
            self.assertEqual([{"id": "series-1"}], rows_from_wrangle_payload(path))


if __name__ == "__main__":
    unittest.main()
