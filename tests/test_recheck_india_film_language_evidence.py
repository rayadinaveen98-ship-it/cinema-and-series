"""No-D1, fail-closed regression tests for bounded Wikidata P364 rechecks."""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from india_film_language_evidence import WikidataRateLimited, read_state
from recheck_india_film_language_evidence import (
    candidates, run, select_round_robin, MAX_RECHECK,
)


def source(qid, title, year, status, prop=None, language=None, source_only=True):
    return {"qid": qid, "title": title, "year": year, "status": status,
            "property": prop, "language": language,
            "language_qids": [], "source_only": source_only,
            "officially_verified": False}


def statement(qid):
    return {"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": qid}}}}


def labels(language):
    return {"labels": {"en": {"value": language}}}


class SourceRecheckTests(unittest.TestCase):
    def make_stage(self, root, films):
        stage = root / "stage.sqlite"
        with sqlite3.connect(stage) as db:
            db.execute("CREATE TABLE films (qid TEXT,title TEXT,year INTEGER,"
                       "year_conflict INTEGER,title_conflict INTEGER)")
            db.executemany("INSERT INTO films VALUES (?,?,?,?,?)",
                           [(f["qid"], f["title"], f["year"], 0, 0) for f in films])
        return stage

    def test_candidates_skip_promoted_and_mismatched_and_bad_flags(self):
        films = [{"qid": f"Q{i}", "title": f"Film {i}", "year": 2000 + i}
                 for i in range(10, 16)]
        records = {
            "Q10": source("Q10", "Film 10", 2010, "missing_claim"),
            "Q11": source("Q11", "Film 11", 2011, "single_language_evidence", "P407", "Telugu"),
            "Q12": source("Q12", "Film 12", 2012, "single_language_evidence", "P364", "Hindi"),
            "Q13": source("Q13", "WRONG", 2013, "missing_claim"),
            "Q14": source("Q14", "Film 14", 2014, "missing_claim", source_only=False),
            "Q15": source("Q15", "Film 15", 2015, "ambiguous_multilingual_or_conflicting", "P364"),
            "Q99": source("Q99", "Out of stage", 2016, "missing_claim"),
        }
        eligible = candidates(films, {"schema": "india-film-language-evidence-v1", "records": records})
        self.assertEqual([r["qid"] for r in eligible], ["Q10", "Q11", "Q15"])

    def test_cursor_rotates_instead_of_retrying_the_same_first_candidates(self):
        rows = [{"qid": q, "title": q, "year": 1980}
                for q in ("Q10", "Q11", "Q12", "Q13")]
        self.assertEqual([x["qid"] for x in select_round_robin(rows, "", 2)], ["Q10", "Q11"])
        self.assertEqual([x["qid"] for x in select_round_robin(rows, "Q11", 2)], ["Q12", "Q13"])
        self.assertEqual([x["qid"] for x in select_round_robin(rows, "Q13", 2)], ["Q10", "Q11"])
        self.assertEqual(select_round_robin(rows, "", 0), [])

    def test_upgrade_only_strict_original_language_and_preserve_other_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            films = [{"qid": q, "title": q, "year": 1978}
                     for q in ("Q101", "Q102", "Q103", "Q104")]
            stage = self.make_stage(root, films)
            checkpoint = root / "checkpoint.json"
            checkpoint.write_text(json.dumps({
                "schema": "india-film-language-evidence-v1",
                "records": {
                    "Q101": source("Q101", "Q101", 1978, "missing_claim"),
                    "Q102": source("Q102", "Q102", 1978, "single_language_evidence", "P407", "Hindi"),
                    "Q103": source("Q103", "Q103", 1978, "ambiguous_multilingual_or_conflicting", "P364"),
                    "Q104": source("Q104", "Q104", 1978, "single_language_evidence", "P364", "Telugu"),
                }
            }))
            def fetcher(ids, props):
                if props == "labels":
                    return {"Q999": labels("Telugu"), "Q888": labels("Hindi")}
                return {
                    "Q101": {"id": "Q101", "claims": {"P364": [statement("Q999")]}},
                    "Q102": {"id": "Q102", "claims": {"P407": [statement("Q888")]}},
                    "Q103": {"id": "Q103", "claims": {"P364": [statement("Q999"), statement("Q888")]}},
                }
            report = run(stage, checkpoint, root / "report.json", max_films=3, fetcher=fetcher)
            state = read_state(checkpoint)
            self.assertEqual(report["attempted"], 3)
            self.assertEqual(report["promoted_to_p364"], 1)
            self.assertEqual(report["still_unresolved"], 2)
            self.assertEqual(report["cursor_qid"], "Q103")
            self.assertEqual(state["records"]["Q101"]["property"], "P364")
            self.assertEqual(state["records"]["Q101"]["language"], "Telugu")
            self.assertEqual(state["records"]["Q101"]["recheck_previous"]["status"], "missing_claim")
            self.assertEqual(state["records"]["Q102"]["property"], "P407")
            self.assertEqual(state["records"]["Q103"]["status"], "ambiguous_multilingual_or_conflicting")
            self.assertEqual(state["records"]["Q104"]["language"], "Telugu")
            self.assertEqual(report["production_updates"], 0)
            self.assertEqual(report["d1_reads"], 0)
            self.assertEqual(json.loads((root / "report.json").read_text())["promoted_to_p364"], 1)

    def test_partial_or_redirected_source_and_missing_labels_never_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            films = [{"qid": "Q20", "title": "A", "year": 1950},
                     {"qid": "Q21", "title": "B", "year": 1951},
                     {"qid": "Q22", "title": "C", "year": 1952}]
            stage = self.make_stage(root, films)
            checkpoint = root / "checkpoint.json"
            records = {f["qid"]: source(f["qid"], f["title"], f["year"], "missing_claim")
                       for f in films}
            checkpoint.write_text(json.dumps({"schema": "india-film-language-evidence-v1",
                                              "records": records}))
            def fetcher(ids, props):
                if props == "labels":
                    return {}  # Q999 missing: must not be inferred as unknown.
                return {"Q20": {"id": "Q999", "claims": {}},
                        "Q21": {"missing": "", "id": "Q21"},
                        "Q22": {"id": "Q22", "claims": {"P364": [statement("Q999")]}}}
            report = run(stage, checkpoint, root / "report.json", max_films=3, fetcher=fetcher)
            self.assertEqual(report["deferred_entities"], 3)
            self.assertEqual(report["promoted_to_p364"], 0)
            self.assertEqual(report["cursor_qid"], "Q22")
            self.assertEqual(read_state(checkpoint)["records"], records)

    def test_throttle_does_not_touch_cursor_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = self.make_stage(root, [{"qid": "Q55", "title": "A", "year": 2001}])
            checkpoint = root / "checkpoint.json"
            checkpoint.write_text(json.dumps({
                "schema": "india-film-language-evidence-v1",
                "records": {"Q55": source("Q55", "A", 2001, "missing_claim")}
            }))
            original = checkpoint.read_bytes()
            def busy(ids, props):
                raise WikidataRateLimited("maxlag")
            report = run(stage, checkpoint, root / "report.json", max_films=1, fetcher=busy)
            self.assertEqual(report["halted_reason"], "rate_limited")
            self.assertEqual(report["attempted"], 0)
            self.assertEqual(checkpoint.read_bytes(), original)

    def test_bounds_enforced_before_any_source_access(self):
        for bad in (0, MAX_RECHECK + 1, 500):
            with self.assertRaises(ValueError):
                run(Path("unused"), Path("unused"), Path("unused"), max_films=bad)


if __name__ == "__main__":
    unittest.main()
