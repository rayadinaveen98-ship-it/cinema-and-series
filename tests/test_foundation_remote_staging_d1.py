"""Security and identity tests for remote disposable staging D1 controller."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.foundation_remote_staging_d1 import (
    EXPECTED_HELD, PRODUCTION, PREFIX, cleanup_exact_stage,
    guarded_sql, lookup, seed_sql, sql_literal, sql_statements,
    stage_config, stage_name, state_from_inputs,
)


class RemoteStagingSafetyTests(unittest.TestCase):
    def test_stage_name_generated_only_from_numeric_workflow_ids(self):
        self.assertEqual(stage_name("39801908508", "1"), "foundation-v2-qa-39801908508-1")
        for values in (("abc", "1"), ("39801908508; rm -rf /", "1"),
                       ("39801908508", "foo"), ("1", "1")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                stage_name(*values)

    def test_stage_config_binds_only_new_qid_not_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "staging.jsonc"
            id_ = "11111111-1111-4111-8111-111111111111"
            stage_config(path, stage_name("39801908508", "1"), id_)
            config = json.loads(path.read_text())
            self.assertEqual(len(config["d1_databases"]), 1)
            self.assertEqual(config["d1_databases"][0]["database_id"], id_)
            self.assertNotEqual(config["d1_databases"][0]["database_name"], PRODUCTION)
            with self.assertRaises(ValueError):
                stage_config(path, PRODUCTION, id_)

    def test_check_sql_is_explicitly_atomic_or_rejects_stale(self):
        entries = []
        for i in range(17):
            qid = f"Q{1111+i}"
            entries.append({
                "before": {
                    "id": f"wd-{qid}", "wikidata_qid": qid,
                    "title": "Film's special title" if i == 0 else f"Film {i}",
                    "release_year": 1970+i, "country_code": "IN",
                    "language_name": "Unknown",
                },
                "after": "Telugu"
            })
        forward = guarded_sql(entries)
        reverse = guarded_sql(entries, reverse=True)
        self.assertEqual(forward.count("INSERT INTO qa_guard"), 17)
        self.assertEqual(forward.count("UPDATE catalogue_titles"), 17)
        self.assertEqual(reverse.count("INSERT INTO qa_guard"), 17)
        self.assertEqual(reverse.count("UPDATE catalogue_titles"), 17)
        self.assertIn("Film''s special title", forward)
        self.assertIn("language_source IS NULL", forward)
        self.assertIn("language_source_url IS NULL", forward)
        self.assertIn("language_source=NULL", reverse)
        self.assertNotIn("UPDATE movies", forward)
        self.assertNotIn("UPDATE series_titles", reverse)

    def test_seed_only_twenty_real_snapshot_rows_and_sentinel(self):
        rows = []
        for i in range(20):
            qid = f"Q{1000+i}"
            rows.append({"id": "wd-" + qid, "wikidata_qid": qid,
                         "title": f"Title {i}", "release_year": 1900+i,
                         "country_code": "IN", "language_name": "Unknown"})
        value=seed_sql(rows)
        self.assertEqual(value.count("INSERT INTO catalogue_titles"), 21)
        self.assertIn("Q999999999", value)
        with self.assertRaises(ValueError):
            seed_sql(rows[:19])
        self.assertEqual(sql_literal("It's a film"), "'It''s a film'")

    def test_only_trusted_schema_statements(self):
        self.assertGreater(len(sql_statements(Path("migrations/0017_year_precision_catalogue.sql"))), 2)
        self.assertEqual(len(sql_statements(Path("migrations/0027_catalogue_title_language_provenance.sql"))), 2)

    def test_uuid_mismatch_never_deletes_resource(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "owned.json"
            id_ = "22222222-2222-4222-8222-222222222222"
            stage = stage_name("39801908508", "1")
            state.write_text(json.dumps({
                "name": stage, "uuid": id_,
                "production_uuid": "11111111-1111-4111-8111-111111111111",
            }))
            wrong = [{"name": stage, "uuid": "33333333-3333-4333-8333-333333333333"}]
            with patch("scripts.foundation_remote_staging_d1.all_databases", return_value=wrong), \
                 patch("scripts.foundation_remote_staging_d1.wrangler") as cli:
                with self.assertRaisesRegex(ValueError,"UUID changed"):
                    cleanup_exact_stage(state)
                cli.assert_not_called()

    def test_no_deletion_of_production_or_unknown_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "wrong.json"
            id_ = "22222222-2222-4222-8222-222222222222"
            state.write_text(json.dumps({
                "name": PRODUCTION, "uuid": id_,
                "production_uuid": "11111111-1111-4111-8111-111111111111",
            }))
            with patch("scripts.foundation_remote_staging_d1.wrangler") as cli:
                with self.assertRaises(ValueError):
                    cleanup_exact_stage(state)
                cli.assert_not_called()
            self.assertTrue(cleanup_exact_stage(Path(tmp) / "missing.json"))


if __name__ == "__main__":
    unittest.main()
