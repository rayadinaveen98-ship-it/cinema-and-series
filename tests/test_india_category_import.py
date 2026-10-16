"""Offline quality gates for one-time India-category movie pilot."""
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_india_category_import import eligible, select_batch
from verify_indian_movie_candidates import sql_for_movie


def candidate(qid="Q123", title="Indian Film", year=2025):
    return {
        "classification": "new_indian_category_candidates",
        "wikidata_qid": qid, "title": title, "year": year, "page_id": 121,
        "source_categories": ["Category:2025 Indian films", "Category:2025 Telugu-language films"],
        "observed_languages": ["Telugu"], "india_category": True,
    }


class IndiaImportTests(unittest.TestCase):
    def test_strong_origin_and_year_category_required(self):
        self.assertEqual(eligible(candidate()), "eligible")
        self.assertEqual(eligible({**candidate(), "source_categories":
                                   ["Category:2025 Telugu-language films"]}),
                         "missing_matching_year_india_category")
        self.assertEqual(eligible(candidate(qid="bad")), "missing_valid_wikidata_id")
        self.assertEqual(eligible({**candidate(), "year": None}), "uncertain_year")

    def test_cap_and_duplicate_source_qid(self):
        rows = [candidate(), candidate(title="Film alternative"),
                candidate(qid="Q124", title="Film 2"),
                {**candidate(qid="Q125"), "classification": "already_in_production"}]
        chosen, summary = select_batch({"candidates": rows}, 1)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(summary["eligible_source_category_records"], 2)
        self.assertEqual(summary["excluded_reasons"]["duplicate_discovery_qid"], 1)

    def test_disjoint_candidate_offsets(self):
        rows = [candidate(qid=f"Q{123 + i}", title=f"Film {i}") for i in range(7)]
        report = {"candidates": rows}
        first, f = select_batch(report, 3, 0)
        second, s = select_batch(report, 3, 3)
        third, t = select_batch(report, 3, 6)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(second), 3)
        self.assertEqual(len(third), 1)
        self.assertTrue({x["wikidata_qid"] for x in first}.isdisjoint(
            {x["wikidata_qid"] for x in second}))
        self.assertEqual(s["batch_offset"], 3)
        self.assertEqual(t["proposed_batch_count"], 1)

    def test_production_indexes_can_serve_all_duplicate_guards(self):
        db = sqlite3.connect(":memory:")
        db.executescript("""
          CREATE TABLE movies(id TEXT PRIMARY KEY, wikidata_qid TEXT UNIQUE,
                              title TEXT, release_date TEXT);
          CREATE INDEX idx_movies_title_nocase ON movies(title COLLATE NOCASE);
          CREATE TABLE series_titles(wikidata_qid TEXT UNIQUE);
          CREATE TABLE catalogue_titles(
              id TEXT PRIMARY KEY, wikidata_qid TEXT UNIQUE,
              wikipedia_page_id INTEGER UNIQUE, title TEXT,
              release_year INTEGER, date_precision TEXT, language_name TEXT,
              country_code TEXT, source_category TEXT,
              source_url TEXT, verification_status TEXT, updated_at TEXT);
          CREATE INDEX idx_catalogue_titles_year_title
              ON catalogue_titles(release_year DESC, title COLLATE NOCASE);
        """)
        explain = db.execute("EXPLAIN QUERY PLAN " + sql_for_movie(candidate())).fetchall()
        details = " | ".join(str(row[3]) for row in explain)
        self.assertNotIn("SCAN m", details)
        self.assertNotIn("SCAN c", details)
        self.assertNotIn("SCAN s", details)
        self.assertIn("idx_movies_title_nocase", details)
        self.assertIn("idx_catalogue_titles_year_title", details)
        db.close()

    def test_case_insensitive_title_year_still_blocks_duplicate(self):
        db = sqlite3.connect(":memory:")
        db.executescript("""
          CREATE TABLE movies(id TEXT PRIMARY KEY, wikidata_qid TEXT, title TEXT, release_date TEXT);
          CREATE TABLE series_titles(wikidata_qid TEXT);
          CREATE TABLE catalogue_titles(
              id TEXT PRIMARY KEY, wikidata_qid TEXT UNIQUE, wikipedia_page_id INTEGER UNIQUE,
              title TEXT, release_year INTEGER, date_precision TEXT,
              language_name TEXT, country_code TEXT, source_category TEXT,
              source_url TEXT, verification_status TEXT, updated_at TEXT);
        """)
        db.execute("INSERT INTO movies VALUES ('x', 'Q999', 'indian FILM', '2025-01-05')")
        db.executescript(sql_for_movie(candidate()))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 0)
        db.close()

    def test_insert_protects_existing_movie_title_year_and_series_id(self):
        db = sqlite3.connect(":memory:")
        db.executescript("""
          CREATE TABLE movies(id TEXT, wikidata_qid TEXT, title TEXT, release_date TEXT);
          CREATE TABLE series_titles(wikidata_qid TEXT);
          CREATE TABLE catalogue_titles(
            id TEXT PRIMARY KEY, wikidata_qid TEXT UNIQUE, wikipedia_page_id INTEGER UNIQUE,
            title TEXT, release_year INTEGER, date_precision TEXT,
            language_name TEXT, country_code TEXT, source_category TEXT, source_url TEXT,
            verification_status TEXT, updated_at TEXT);
        """)
        movie = candidate()
        db.executescript(sql_for_movie(movie))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 1)
        db.executescript(sql_for_movie(movie))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 1)

        db.execute("DELETE FROM catalogue_titles")
        db.execute("INSERT INTO movies VALUES ('x','Q999','Indian Film','2025-09-10')")
        db.executescript(sql_for_movie(movie))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 0)

        db.execute("DELETE FROM movies")
        db.execute("INSERT INTO series_titles VALUES ('Q123')")
        db.executescript(sql_for_movie(movie))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM catalogue_titles").fetchone()[0], 0)
        db.close()


if __name__ == "__main__":
    unittest.main()
