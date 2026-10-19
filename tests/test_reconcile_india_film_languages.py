"""Tests for source-only-to-production film language reconciliation."""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_india_film_languages import (
    reconcile, guarded_update_sql, d1_rows, output_files
)


def evidence(qid="Q100", title="A Film", year=2024, language="Telugu",
             property="P364", status="single_language_evidence"):
    return {
        "qid": qid, "title": title, "year": year, "language": language,
        "property": property, "status": status,
        "source_only": True, "officially_verified": False,
        "source_url": "https://www.wikidata.org/wiki/" + qid,
    }


def prod(qid="Q100", title="A Film", year=2024, language="Unknown",
         country="IN", id="ct_100"):
    return {
        "id": id, "wikidata_qid": qid, "title": title,
        "release_year": year, "language_name": language, "country_code": country,
    }


def checkpoint(*records):
    return {"schema": "india-film-language-evidence-v1",
            "records": {record["qid"]: record for record in records}}


class FilmLanguageReconciliationTests(unittest.TestCase):
    def test_only_matching_unknown_indian_language_updated(self):
        result = reconcile(checkpoint(evidence()), [prod()])
        self.assertEqual(result["selected_count"], 1)
        self.assertEqual(result["selected"][0]["language_source"], "wikidata:P364")
        self.assertEqual(result["production_writes"], 0)

    def test_rejects_title_year_country_and_known_language_mismatches(self):
        tests = [
            (prod(title="Wrong Film"), "title_mismatch"),
            (prod(year=2023), "year_mismatch"),
            (prod(country="US"), "not_indian_film"),
            (prod(language="Hindi"), "already_known_language"),
        ]
        for row, reason in tests:
            with self.subTest(reason=reason):
                report = reconcile(checkpoint(evidence()), [row])
                self.assertEqual(report["selected_count"], 0)
                self.assertEqual(report["rejected_reasons"].get(reason), 1)

    def test_never_promotes_general_p407_or_ambiguous_evidence(self):
        for record in [
            evidence(property="P407"),
            evidence(status="ambiguous_multilingual_or_conflicting", language=None),
            {**evidence(), "officially_verified": True},
            evidence(language="Unverified Fake Language"),
        ]:
            with self.subTest(record=record):
                result = reconcile(checkpoint(record), [prod()])
                self.assertEqual(result["selected_count"], 0)
                self.assertEqual(result["rejected_reasons"]["not_strict_p364_evidence"], 1)

    def test_requires_exact_qid_year_title_and_unknown_at_apply_time(self):
        with sqlite3.connect(":memory:") as db:
            db.executescript(
                "CREATE TABLE catalogue_titles (id TEXT, wikidata_qid TEXT, title TEXT, "
                "release_year INTEGER, country_code TEXT, language_name TEXT, "
                "language_source TEXT, language_source_url TEXT, updated_at TEXT);"
            )
            db.execute("INSERT INTO catalogue_titles VALUES (?,?,?,?,?,?,?,?,?)",
                       ("ct_100","Q100","A Film",2024,"IN","Unknown",None,None,None))
            sql = guarded_update_sql(reconcile(checkpoint(evidence()), [prod()])["selected"][0])
            self.assertEqual(db.execute(sql).rowcount, 1)
            language, source, url = db.execute("SELECT language_name,language_source,language_source_url FROM catalogue_titles").fetchone()
            self.assertEqual((language,source,url),("Telugu","wikidata:P364","https://www.wikidata.org/wiki/Q100"))
            self.assertEqual(db.execute(sql).rowcount, 0, "Idempotent, no overwrite")
            db.execute("UPDATE catalogue_titles SET language_name='Hindi', language_source=NULL")
            self.assertEqual(db.execute(sql).rowcount, 0, "Never overwrite established language")
            db.execute("UPDATE catalogue_titles SET language_name='Unknown', title='Other film'")
            self.assertEqual(db.execute(sql).rowcount, 0, "Never apply when identity changed")

    def test_sql_quotes_titles_without_injection(self):
        item = reconcile(checkpoint(evidence(title="An 'Indian' Film")),
                         [prod(title="An 'Indian' Film")])["selected"][0]
        self.assertIn("An ''Indian'' Film", guarded_update_sql(item))

    def test_d1_payload_and_output_batches_bounded(self):
        self.assertEqual(len(d1_rows([{"results": [prod()]}, {"results": [prod("Q101")]}])),2)
        with self.assertRaises(ValueError):
            d1_rows({"unexpected": []})
        result = reconcile(checkpoint(evidence()), [prod()])
        with tempfile.TemporaryDirectory() as tmp:
            output_files(result, Path(tmp))
            self.assertEqual(len(list(Path(tmp).glob("language-*.sql"))),1)
            saved = json.loads((Path(tmp)/"reconciliation.json").read_text())
            self.assertEqual(saved["selected_count"],1)
            with self.assertRaises(ValueError):
                output_files(result, Path(tmp), chunk_size=200)


if __name__ == "__main__":
    unittest.main()
