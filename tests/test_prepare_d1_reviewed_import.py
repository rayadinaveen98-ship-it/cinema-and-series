from __future__ import annotations

import unittest

from scripts.prepare_d1_reviewed_import import estimate_rows_written, prepare_sql


FINGERPRINT = "4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448"


def sample_sql(extra: str = "") -> str:
    return f"""-- Projection manifest SHA-256: {FINGERPRINT}
-- Projection candidate count: 14115
PRAGMA foreign_keys = ON;
BEGIN;
INSERT INTO recommendation_titles (id) VALUES ('wikidata:Q1');
INSERT INTO genres (id) VALUES ('wikidata:Q2');
INSERT INTO people (id) VALUES ('wikidata:Q3');
INSERT OR IGNORE INTO title_genres (title_id) VALUES ('wikidata:Q1');
INSERT OR IGNORE INTO title_credits (title_id) VALUES ('wikidata:Q1');
{extra}COMMIT;
"""


class PrepareD1ReviewedImportTests(unittest.TestCase):
    def test_removes_only_execution_controls(self) -> None:
        original = sample_sql()
        executable, manifest = prepare_sql(original, FINGERPRINT)
        self.assertNotIn("PRAGMA foreign_keys = ON;", executable)
        self.assertNotIn("\nBEGIN;", "\n" + executable)
        self.assertNotIn("\nCOMMIT;", "\n" + executable)
        self.assertIn("INSERT INTO recommendation_titles", executable)
        self.assertIn("INSERT OR IGNORE INTO title_credits", executable)
        self.assertEqual(manifest["data_statement_count"], 5)
        self.assertEqual(
            manifest["removed_controls"],
            ["PRAGMA foreign_keys = ON;", "BEGIN;", "COMMIT;"],
        )
        self.assertNotEqual(manifest["original_sha256"], manifest["executable_sha256"])
        self.assertEqual(manifest["estimated_rows_written"], 19)
        self.assertEqual(manifest["free_daily_rows_written_headroom"], 99_981)

    def test_rows_written_cost_model_matches_schema_indexes(self) -> None:
        self.assertEqual(
            estimate_rows_written(
                {
                    "INSERT INTO recommendation_titles": 1744,
                    "INSERT INTO genres": 235,
                    "INSERT INTO people": 6184,
                    "INSERT OR IGNORE INTO title_genres": 1641,
                    "INSERT OR IGNORE INTO title_credits": 6931,
                }
            ),
            65_299,
        )

    def test_rejects_unknown_cost_model_statement(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown P1 statement types"):
            estimate_rows_written({"DELETE FROM people": 1})

    def test_rejects_wrong_projection_fingerprint(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected projection fingerprint"):
            prepare_sql(sample_sql(), "deadbeef")

    def test_rejects_unreviewed_statement(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsafe or unexpected SQL statement"):
            prepare_sql(sample_sql("DELETE FROM people;\n"), FINGERPRINT)

    def test_rejects_missing_transaction_wrapper(self) -> None:
        broken = sample_sql().replace("BEGIN;\n", "")
        with self.assertRaisesRegex(ValueError, "exactly one 'BEGIN;'" ):
            prepare_sql(broken, FINGERPRINT)

    def test_rejects_duplicate_control(self) -> None:
        broken = sample_sql().replace("BEGIN;\n", "BEGIN;\nBEGIN;\n")
        with self.assertRaisesRegex(ValueError, "exactly one 'BEGIN;'" ):
            prepare_sql(broken, FINGERPRINT)


if __name__ == "__main__":
    unittest.main()
