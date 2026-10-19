"""Offline regression tests for the Indian film-language source review queue."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.triage_india_film_languages import read_stage, triage


ROOT = Path(__file__).resolve().parents[1]


def evidence(qid, title, year, status, prop=None, language=None, ids=None):
    return {"qid": qid, "title": title, "year": year, "status": status,
            "property": prop, "language": language,
            "language_qids": ids or [], "source_only": True,
            "officially_verified": False}


class FilmLanguageTriageTests(unittest.TestCase):
    def test_accept_strict_language_and_triage_held_source_records(self):
        stage = {
            "Q10": {"title": "One", "year": 2020},
            "Q11": {"title": "Two", "year": 2021},
            "Q12": {"title": "Three", "year": 1974},
            "Q13": {"title": "Four", "year": 1950},
            "Q14": {"title": "Five", "year": 1965},
            "Q15": {"title": "Six", "year": 1999},
        }
        records = {
            "Q10": evidence("Q10", "One", 2020, "single_language_evidence", "P364", "Telugu", ["Q9199"]),
            "Q11": evidence("Q11", "Two", 2021, "single_language_evidence", "P407", "Hindi", ["Q1568"]),
            "Q12": evidence("Q12", "Three", 1974, "ambiguous_multilingual_or_conflicting", "P364", ids=["Q9199", "Q1568"]),
            "Q13": evidence("Q13", "Four", 1950, "unrecognized_language", "P364", ids=["Q234"]),
            "Q14": evidence("Q14", "Five", 1965, "missing_claim"),
            "Q15": evidence("Q15", "WRONG TITLE", 1999, "single_language_evidence", "P364", "Hindi"),
            "Q16": evidence("Q16", "Orphan", 1995, "single_language_evidence", "P364", "Telugu"),
        }
        original = deepcopy(records)
        report = triage(stage, {"schema": "india-film-language-evidence-v1", "records": records})
        self.assertEqual(records, original)  # No checkpoint mutation.
        self.assertEqual(report["checkpoint_records"], 7)
        self.assertEqual(report["accepted_source_p364"], 1)
        self.assertEqual(report["needs_review"], 6)
        self.assertEqual(report["d1_reads"], 0)
        self.assertEqual(report["d1_writes"], 0)
        self.assertEqual(report["production_updates"], 0)
        self.assertEqual(report["official_verifications"], 0)
        self.assertEqual(report["by_category"], {
            "conflicting_or_multiple_languages": 1,
            "general_language_only_P407": 1,
            "identity_mismatch": 1,
            "no_language_claim": 1,
            "not_in_stage": 1,
            "unrecognized_language": 1,
        })
        # Identity issues first; other labels cannot supersede identity checks.
        self.assertEqual([x["qid"] for x in report["review_queue"][:2]], ["Q16", "Q15"])
        self.assertEqual(report["review_queue"][2]["language_claim_qids"], ["Q234"])
        self.assertTrue(all(x["production_update_allowed"] is False for x in report["review_queue"]))
        self.assertNotIn("Q10", [x["qid"] for x in report["review_queue"]])

    def test_invalid_flags_and_unexpected_states_are_not_accepted(self):
        stage = {"Q20": {"title": "Valid", "year": 1982},
                 "Q21": {"title": "Another", "year": 2026},
                 "Q22": {"title": "Third", "year": 1999}}
        bad_flags = evidence("Q20", "Valid", 1982, "single_language_evidence", "P364", "Tamil")
        bad_flags["officially_verified"] = True
        missing_language = evidence("Q21", "Another", 2026, "single_language_evidence", "P364")
        invalid_identity = evidence("wrong-qid", "Third", 1999, "single_language_evidence", "P364", "Hindi")
        report = triage(stage, {"schema": "india-film-language-evidence-v1",
                                "records": {"Q20": bad_flags, "Q21": missing_language, "Q22": invalid_identity}})
        self.assertEqual(report["accepted_source_p364"], 0)
        self.assertEqual(set(report["by_category"]), {
            "source_flags_invalid", "unexpected_evidence", "invalid_identity",
        })

    def test_unknown_checkpoint_schema_fails_closed(self):
        for item in ({}, {"schema": "wrong", "records": {}},
                     {"schema": "india-film-language-evidence-v1", "records": []}):
            with self.assertRaises(ValueError):
                triage({}, item)

    def test_read_stage_rejects_conflicts_and_duplicate_qids(self):
        with tempfile.TemporaryDirectory() as temp:
            stage_path = Path(temp) / "stage.sqlite"
            with sqlite3.connect(stage_path) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.executemany("INSERT INTO films VALUES (?,?,?,?,?)", [
                    ("Q77", "Allowed", 1984, 0, 0),
                    ("Q78", "Conflict", 1983, 1, 0),
                ])
            stage = read_stage(stage_path)
            self.assertEqual(stage, {"Q77": {"title": "Allowed", "year": 1984}})
            with sqlite3.connect(stage_path) as db:
                db.execute("INSERT INTO films VALUES ('Q77','Duplicate',1982,0,0)")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                read_stage(stage_path)

    def test_cli_generates_source_only_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "films.sqlite"
            checkpoint = root / "checkpoint.json"
            out = root / "review.json"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.execute("INSERT INTO films VALUES ('Q800','Film',1980,0,0)")
            checkpoint.write_text(json.dumps({
                "schema": "india-film-language-evidence-v1",
                "records": {"Q800": evidence("Q800", "Film", 1980, "missing_claim")}
            }))
            run = subprocess.run(
                [sys.executable, str(ROOT / "scripts/triage_india_film_languages.py"),
                 "--stage", str(stage), "--checkpoint", str(checkpoint),
                 "--out", str(out)], capture_output=True, text=True, check=True)
            self.assertIn("INDIA_LANGUAGE_REVIEW_QUEUE=", run.stdout)
            report = json.loads(out.read_text())
            self.assertEqual(report["needs_review"], 1)
            self.assertEqual(report["review_queue"][0]["category"], "no_language_claim")
            self.assertEqual(report["production_updates"], 0)


if __name__ == "__main__":
    unittest.main()
