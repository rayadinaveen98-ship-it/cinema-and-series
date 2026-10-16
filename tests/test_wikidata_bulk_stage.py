"""No-network tests for the Wikimedia CC0 bulk extraction and SQL staging lane."""
import json
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from wikidata_bulk_stage import (
    connect, quarter_dates, sparql_for_quarter, parse_rows, stage_quarter,
    run_stage, report_for,
)
from wikidata_bulk_import_sql import reconcile, sql_for_staged_movie, write_preview


def binding(qid, title, release):
    return {
        "film": {"type": "uri", "value": f"http://www.wikidata.org/entity/{qid}"},
        "filmLabel": {"type": "literal", "value": title},
        "release": {"type": "literal", "value": release},
    }


def result(*rows):
    return {"results": {"bindings": list(rows)}}


def film(qid="Q80", title="A Film", year=2020):
    return {"qid": qid, "title": title, "year": year}


class BulkWikidataStageTests(unittest.TestCase):
    def test_sparql_requires_film_india_release_in_quarter(self):
        sql = sparql_for_quarter(2020, 2)
        self.assertIn("wdt:P31 wd:Q11424", sql)
        self.assertIn("wdt:P495 wd:Q668", sql)
        self.assertIn("wdt:P577 ?release", sql)
        self.assertIn("2020-04-01T00:00:00Z", sql)
        self.assertIn("2020-07-01T00:00:00Z", sql)
        self.assertEqual(quarter_dates(2020, 4)[1], "2021-01-01T00:00:00Z")

    def test_source_validation_blocks_qid_placeholder_and_other_year(self):
        candidates, dropped = parse_rows(result(
            binding("Q100", "Film Title", "2020-05-06T00:00:00Z"),
            binding("Q101", "Q101", "2020-05-07T00:00:00Z"),
            binding("Q102", "Other Year", "2021-04-10T00:00:00Z"),
        ), 2020, 2)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["qid"], "Q100")
        self.assertEqual(dropped, 2)

    def test_staging_is_idempotent_and_quarantines_conflicting_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            with connect(Path(temp)/"stage.sqlite") as db:
                a = result(binding("Q90", "First Title", "2020-02-01T00:00:00Z"))
                self.assertEqual(stage_quarter(db, a, 2020, 1)["accepted"], 1)
                self.assertEqual(stage_quarter(db, a, 2020, 1)["accepted"], 1)
                b = result(binding("Q90", "Another Title", "2021-02-01T00:00:00Z"))
                stage_quarter(db, b, 2021, 1)
                conflict = db.execute("SELECT year_conflict,title_conflict FROM films").fetchone()
                self.assertEqual(conflict, (1, 1))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM films").fetchone()[0], 1)

    def test_truncated_result_remains_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            with connect(Path(temp)/"stage.sqlite") as db:
                res = stage_quarter(db, result(binding("Q70", "Known Film", "2020-01-01T00:00:00Z")),
                                    2020, 1, result_limit=1)
                self.assertTrue(res["truncated"])
                self.assertEqual(db.execute("SELECT outcome FROM shards").fetchone()[0],
                                 "incomplete")

    def test_run_resume_skips_complete_shard_and_bounded_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            with connect(Path(temp)/"stage.sqlite") as db:
                requested = []
                def fetch(query):
                    requested.append(query)
                    return result(binding(f"Q{100+len(requested)}", "Sample Film",
                                          f"2020-0{len(requested)}-05T00:00:00Z"))
                first = run_stage(db, 2020, 2020, 1, fetcher=fetch, cooldown=0)
                second = run_stage(db, 2020, 2020, 1, fetcher=fetch, cooldown=0)
                self.assertEqual(first["completed_shards"], 1)
                self.assertEqual(second["completed_shards"], 2)
                self.assertEqual(len(requested), 2)

    def test_rate_limited_stops_without_corrupt_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            with connect(Path(temp)/"stage.sqlite") as db:
                def fetch(_):
                    raise urllib.error.HTTPError(
                        "https://query.wikidata.org", 429, "rate limited", {}, None)
                report = run_stage(db, 2020, 2020, 4, fetcher=fetch, cooldown=0)
                self.assertEqual(report["completed_shards"], 0)
                self.assertEqual(report["stopped_reason"], "wikidata_rate_limited_429")
                self.assertFalse(report["all_shards_completed"])

    def test_excludes_existing_qid_title_year_and_series(self):
        rows = [film("Q10", "Old"), film("Q11", "Duplicate"),
                film("Q12", "Show"), film("Q13", "New Movie")]
        exact = [{"wikidata_qid": "Q10", "title": "Old", "release_date": "2020-05-01"},
                 {"wikidata_qid": "Q55", "title": "duplicate", "release_date": "2020-11-01"}]
        series = [{"wikidata_qid": "Q12", "title": "Show", "first_air_year": 2020}]
        chosen, summary = reconcile(rows, exact, [], series)
        self.assertEqual([x["qid"] for x in chosen], ["Q13"])
        self.assertEqual(summary["reconciled_net_new_candidates"], 1)
        self.assertTrue(summary["not_imported"])

    def test_sql_is_insert_only_and_respects_exact_titles_and_series_ids(self):
        with sqlite3.connect(":memory:") as db:
            db.executescript("""
            CREATE TABLE movies(id TEXT PRIMARY KEY,wikidata_qid TEXT UNIQUE,
                                title TEXT,release_date TEXT);
            CREATE INDEX idx_movies_title_nocase ON movies(title COLLATE NOCASE);
            CREATE TABLE series_titles(wikidata_qid TEXT UNIQUE);
            CREATE TABLE catalogue_titles(
              id TEXT PRIMARY KEY,wikidata_qid TEXT UNIQUE,wikipedia_page_id INTEGER UNIQUE,
              title TEXT,release_year INTEGER,date_precision TEXT,language_name TEXT,
              country_code TEXT,source_category TEXT,source_url TEXT,
              verification_status TEXT,updated_at TEXT);
            CREATE INDEX idx_catalogue_titles_year_title
              ON catalogue_titles(release_year DESC,title COLLATE NOCASE);
            """)
            stmt = sql_for_staged_movie(film("Q98", "Film O'Reilly"))
            self.assertIn("'unconfirmed'", stmt)
            self.assertIn("NULL", stmt)
            self.assertNotIn("'2020-01-01' AS release_date", stmt)
            db.executescript(stmt)
            db.executescript(stmt)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT wikipedia_page_id FROM catalogue_titles").fetchone()[0], None)
            db.execute("INSERT INTO movies VALUES ('m','Q20','Other','2020-06-01')")
            db.executescript(sql_for_staged_movie(film("Q21", "other")))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 1)
            db.execute("INSERT INTO series_titles VALUES ('Q22')")
            db.executescript(sql_for_staged_movie(film("Q22", "Series")))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 1)
            plan = db.execute("EXPLAIN QUERY PLAN " + sql_for_staged_movie(film("Q23"))).fetchall()
            details = " | ".join(row[3] for row in plan)
            self.assertIn("idx_movies_title_nocase", details)
            self.assertIn("idx_catalogue_titles_year_title", details)
            self.assertNotIn("SCAN c", details)

    def test_preview_files_are_never_executed(self):
        with tempfile.TemporaryDirectory() as temp:
            files = write_preview(Path(temp), [film("Q80"), film("Q81")], chunk_size=1)
            self.assertEqual(len(files), 2)
            self.assertTrue((Path(temp)/files[0]).read_text().startswith("-- PREVIEW ONLY"))


if __name__ == "__main__":
    unittest.main()
