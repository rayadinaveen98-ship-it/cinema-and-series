"""Regression tests for the D1 anniversary query's selectivity and index."""
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_SQL = ROOT / "migrations" / "0026_on_this_day_month_day_index.sql"


class OnThisDayIndexTest(unittest.TestCase):
    def test_anniversary_query_uses_expression_index_and_excludes_future(self):
        conn = sqlite3.connect(":memory:")
        self.addCleanup(conn.close)
        conn.executescript(
            "CREATE TABLE movies ("
            "id TEXT PRIMARY KEY, title TEXT NOT NULL, "
            "release_date TEXT NOT NULL, language_name TEXT, "
            "wikidata_qid TEXT);"
        )
        conn.executemany(
            "INSERT INTO movies(id,title,release_date,language_name,wikidata_qid) VALUES(?,?,?,?,?)",
            [
                ("a", "Yesterday", "2000-10-17", "Telugu", None),
                ("b", "Anniversary", "2017-10-18", "Telugu", None),
                ("c", "Earlier anniversary", "2009-10-18", "Tamil", None),
                ("d", "Future release", "2027-10-18", "Hindi", None),
                ("e", "Q123", "2019-10-18", "Telugu", "Q123"),
            ],
        )
        conn.executescript(INDEX_SQL.read_text(encoding="utf-8"))

        sql = (
            "SELECT m.id, m.title FROM movies m "
            "WHERE substr(m.release_date, 6, 5) = ?1 "
            "AND m.release_date <= ?2 "
            "AND (m.wikidata_qid IS NULL OR m.title <> m.wikidata_qid) "
            "ORDER BY m.release_date DESC, m.title COLLATE NOCASE ASC LIMIT ?3"
        )
        plan = list(conn.execute("EXPLAIN QUERY PLAN " + sql, ("10-18", "2026-10-18", 200)))
        self.assertTrue(
            any("idx_movies_on_this_day_month_date" in row[3] for row in plan),
            f"Missing indexed anniversary search: {plan}",
        )
        rows = list(conn.execute(sql, ("10-18", "2026-10-18", 200)))
        self.assertEqual([row[0] for row in rows], ["b", "c"])


if __name__ == "__main__":
    unittest.main()
