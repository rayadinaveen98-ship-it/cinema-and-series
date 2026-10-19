"""Offline correctness and checkpoint-resume tests for the source-only language queue."""
import json
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from india_film_language_evidence import (
    claim_qids, evidence_for, run, read_state, select_pending_films, MAX_PER_RUN,
)


def statement(qid, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {"snaktype": "value",
                     "datavalue": {"value": {"id": qid}}},
    }


def labels(name):
    return {"labels": {"en": {"language": "en", "value": name}}}


def film(qid):
    return {"qid": qid, "title": "Film " + qid, "year": 2023}


class SourceLanguageTests(unittest.TestCase):
    def test_specific_film_language_claim_wins_when_consistent(self):
        movie = {"claims": {"P364": [statement("Q111")],
                            "P407": [statement("Q111")]}}
        entry = evidence_for(film("Q50"), movie, {"Q111": labels("Telugu")})
        self.assertEqual(entry["language"], "Telugu")
        self.assertEqual(entry["property"], "P364")
        self.assertEqual(entry["status"], "single_language_evidence")
        self.assertFalse(entry["officially_verified"])
        self.assertTrue(entry["source_only"])

    def test_general_fallback_only_if_film_original_language_absent(self):
        entry = evidence_for(
            film("Q51"), {"claims": {"P407": [statement("Q9")]}},
            {"Q9": labels("Malayalam")},
        )
        self.assertEqual((entry["language"], entry["property"]), ("Malayalam", "P407"))

    def test_ambiguous_and_conflicting_languages_are_not_guessed(self):
        for claims in (
            {"P364": [statement("Q111"), statement("Q222")]},
            {"P364": [statement("Q111")], "P407": [statement("Q222")]},
        ):
            entry = evidence_for(
                film("Q52"), {"claims": claims},
                {"Q111": labels("Telugu"), "Q222": labels("Hindi")},
            )
            self.assertIsNone(entry["language"])
            self.assertEqual(entry["status"], "ambiguous_multilingual_or_conflicting")

    def test_deprecated_statement_ignored_and_silent_or_unknown_held(self):
        claims = {"P364": [statement("Q111", "deprecated")],
                  "P407": [statement("Q222")]}
        self.assertEqual(claim_qids({"claims": claims}, "P364"), set())
        entry = evidence_for(film("Q53"), {"claims": claims},
                             {"Q222": labels("Unmapped Example Language")})
        self.assertEqual(entry["status"], "unrecognized_language")
        self.assertIsNone(entry["language"])
        self.assertEqual(evidence_for(film("Q54"), {}, {})["status"], "missing_claim")

    def test_read_only_source_run_resumes_and_skips_fetched_qids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.executemany("INSERT INTO films VALUES (?,?,?,?,?)", [
                    ("Q100", "One", 2023, 0, 0),
                    ("Q101", "Two", 2023, 0, 0),
                    ("Q102", "Conflict", 2023, 1, 0),
                ])
            calls = []
            def fake_fetch(ids, props):
                calls.append((tuple(ids), props))
                if props == "claims":
                    return {qid: {"claims": {"P364": [statement("Q999")]}}
                            for qid in ids}
                return {"Q999": labels("Telugu")}

            checkpoint = root / "checkpoint.json"
            report_a = run(stage, checkpoint, 1, root / "report.json",
                           root / "proposals.json", fetcher=fake_fetch, cooldown=0)
            self.assertEqual(report_a["checked_this_run"], 1)
            self.assertEqual(report_a["pending_qids"], 1)
            report_b = run(stage, checkpoint, 2, root / "report.json",
                           root / "proposals.json", fetcher=fake_fetch, cooldown=0)
            self.assertEqual(report_b["checked_this_run"], 1)
            self.assertEqual(report_b["cumulative_checked_qids"], 2)
            self.assertEqual(report_b["proposed_single_language"], 2)
            self.assertEqual(report_b["strict_p364_original_language"], 2)
            self.assertEqual(report_b["general_p407_only_language"], 0)
            self.assertEqual(len(calls), 4)
            self.assertEqual(len(read_state(checkpoint)["records"]), 2)
            self.assertEqual(len(json.loads((root / "proposals.json").read_text())["proposals"]), 2)

    def test_general_p407_evidence_counted_separately_from_original_language(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.execute("INSERT INTO films VALUES ('Q305','Test',2024,0,0)")
            def fetcher(ids, props):
                if props == "claims":
                    return {"Q305": {"claims": {"P407": [statement("Q15")]}}}
                return {"Q15": labels("Telugu")}
            report = run(stage, root / "checkpoint.json", 1, root / "report.json",
                         root / "proposals.json", fetcher=fetcher, cooldown=0)
            self.assertEqual(report["proposed_single_language"], 1)
            self.assertEqual(report["strict_p364_original_language"], 0)
            self.assertEqual(report["general_p407_only_language"], 1)
            self.assertEqual(report["production_updates"], 0)

    def test_decade_balanced_source_selection_covers_old_and_new_films(self):
        films = [
            {"qid": "Q101", "title": "New A", "year": 2025},
            {"qid": "Q102", "title": "New B", "year": 2024},
            {"qid": "Q103", "title": "New C", "year": 2023},
            {"qid": "Q104", "title": "Classic A", "year": 1988},
            {"qid": "Q105", "title": "Classic B", "year": 1980},
            {"qid": "Q106", "title": "Vintage", "year": 1952},
        ]
        recent = select_pending_films(films, {}, 4, "recent")
        self.assertEqual([x["qid"] for x in recent], ["Q101", "Q102", "Q103", "Q104"])
        balanced = select_pending_films(films, {}, 4, "decade-balanced")
        self.assertEqual([x["qid"] for x in balanced], ["Q101", "Q104", "Q106", "Q102"])
        excluded = select_pending_films(films, {"Q101": {"status": "already_checked"}}, 3, "decade-balanced")
        self.assertEqual([x["qid"] for x in excluded], ["Q102", "Q104", "Q106"])
        self.assertEqual(len(select_pending_films(films, {}, 50, "decade-balanced")), 6)
        with self.assertRaises(ValueError):
            select_pending_films(films, {}, 5, "unknown")

    def test_decade_balanced_run_preserves_identity_and_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.executemany("INSERT INTO films VALUES (?,?,?,?,?)", [
                    ("Q701", "Modern", 2025, 0, 0),
                    ("Q702", "Recent", 2024, 0, 0),
                    ("Q703", "Vintage", 1952, 0, 0),
                ])
            def fetcher(ids, props):
                if props == "claims":
                    return {qid: {"id": qid, "claims": {"P364": [statement("Q999")]}}
                            for qid in ids}
                return {"Q999": labels("Telugu")}
            checkpoint = root / "checkpoint.json"
            report = run(stage, checkpoint, 2, root / "report.json",
                         root / "proposals.json", fetcher=fetcher, cooldown=0,
                         selection="decade-balanced")
            self.assertEqual(report["checked_this_run"], 2)
            self.assertEqual(report["source_selection"], "decade-balanced")
            self.assertEqual(report["checked_by_decade"], {1950: 1, 2020: 1})
            self.assertEqual(set(read_state(checkpoint)["records"]), {"Q701", "Q703"})
            self.assertEqual(report["production_updates"], 0)

    def test_rate_limit_does_not_mark_pending_qids_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.execute("INSERT INTO films VALUES ('Q202','Test',2024,0,0)")
            def rate_limited(ids, props):
                raise urllib.error.HTTPError(
                    "https://www.wikidata.org/", 429, "Too Many Requests", {}, None
                )
            checkpoint = root / "checkpoint.json"
            report = run(stage, checkpoint, 1, root / "r.json", root / "p.json",
                         fetcher=rate_limited, cooldown=0)
            self.assertEqual(report["halted_reason"], "rate_limited")
            self.assertEqual(report["checked_this_run"], 0)
            self.assertEqual(report["pending_qids"], 1)
            self.assertFalse(read_state(checkpoint)["records"])

    def test_partial_or_missing_wikidata_entity_does_not_poison_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.executemany("INSERT INTO films VALUES (?,?,?,?,?)", [
                    ("Q211", "One", 2024, 0, 0),
                    ("Q212", "Two", 2024, 0, 0),
                ])
            for missing in (True, False):
                def partial_fetch(ids, props):
                    if props == "labels":
                        return {"Q999": labels("Telugu")}
                    if missing:
                        return {"Q211": {"claims": {"P364": [statement("Q999")]}}}
                    return {
                        "Q211": {"claims": {"P364": [statement("Q999")]}},
                        "Q212": {"missing": "", "id": "Q212"},
                    }
                checkpoint = root / f"checkpoint-{missing}.json"
                report = run(stage, checkpoint, 2, root / "report.json",
                             root / "proposals.json", fetcher=partial_fetch, cooldown=0)
                self.assertEqual(report["checked_this_run"], 1)
                self.assertEqual(report["pending_qids"], 1)
                self.assertIsNone(report["halted_reason"])
                self.assertEqual(report["held_incomplete_film_entities"], 1)
                self.assertEqual(list(read_state(checkpoint)["records"]), ["Q211"])

    def test_missing_language_entity_is_deferred_not_guessed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.executemany("INSERT INTO films VALUES (?,?,?,?,?)", [
                    ("Q301", "Film A", 2024, 0, 0), ("Q302", "Film B", 2024, 0, 0)
                ])
            def fetcher(ids, props):
                if props == "claims":
                    return {"Q301": {"claims": {"P364": [statement("Q901")]}},
                            "Q302": {"claims": {"P364": [statement("Q902")]}}}
                return {"Q901": labels("Telugu")}  # Q902 omitted by API.
            report = run(stage, root / "checkpoint.json", 2, root / "r.json",
                         root / "p.json", fetcher=fetcher, cooldown=0)
            self.assertEqual(report["checked_this_run"], 1)
            self.assertEqual(report["held_incomplete_language_entities"], 1)
            self.assertEqual(report["pending_qids"], 1)
            self.assertEqual(read_state(root / "checkpoint.json")["records"]["Q301"]["language"], "Telugu")
            self.assertNotIn("Q302", read_state(root / "checkpoint.json")["records"])

    def test_transient_mediawiki_json_error_defers_without_corrupting_records(self):
        from india_film_language_evidence import WikidataRateLimited
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage.sqlite"
            with sqlite3.connect(stage) as db:
                db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                           "year_conflict INTEGER,title_conflict INTEGER)")
                db.execute("INSERT INTO films VALUES ('Q454','Test',2024,0,0)")
            def busy(ids, props):
                raise WikidataRateLimited("Wikidata API busy: maxlag")
            report = run(stage, root / "checkpoint.json", 1, root / "r.json",
                         root / "p.json", fetcher=busy, cooldown=0)
            self.assertEqual(report["halted_reason"], "rate_limited")
            self.assertEqual(report["checked_this_run"], 0)
            self.assertEqual(read_state(root / "checkpoint.json")["records"], {})

    def test_wikidata_error_payload_is_not_interpreted_as_empty_language(self):
        from unittest.mock import patch
        from india_film_language_evidence import fetch_entities, WikidataRateLimited
        class FakeResponse:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                return b'{"error":{"code":"maxlag","info":"Server lag"}}'
        with patch("india_film_language_evidence.urllib.request.urlopen",
                   return_value=FakeResponse()):
            with self.assertRaisesRegex(WikidataRateLimited, "maxlag"):
                fetch_entities(["Q123"], "claims")

    def test_run_limits_are_enforced(self):
        with self.assertRaises(ValueError):
            run(Path("unused"), Path("unused"), MAX_PER_RUN + 1,
                Path("unused"), Path("unused"))


if __name__ == "__main__":
    unittest.main()
