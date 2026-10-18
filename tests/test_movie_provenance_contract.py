"""Run the actual Worker catalogue CTE in SQLite to verify source attribution.

No network, production calls or D1 mutations. Prevents a repeat of labeling
Wikidata-sourced, year-only Indian films as English Wikipedia categories.
"""
import re
import sqlite3
import unittest
from pathlib import Path


WORKER = Path(__file__).resolve().parents[1] / "worker" / "index.ts"


class MovieProvenanceContractTests(unittest.TestCase):
    def test_source_labels_and_safe_links_match_actual_cinema_source(self):
        worker = WORKER.read_text(encoding="utf-8")
        match = re.search(r"const combinedCatalogueCte = `(.*?)`;", worker, re.S)
        self.assertIsNotNone(match, "Combined catalogue SQL was not found")
        cte = match.group(1).replace(
            "${visibleMovieClause}",
            "(m.wikidata_qid IS NULL OR m.title <> m.wikidata_qid)"
        )

        with sqlite3.connect(":memory:") as db:
            db.executescript("""
                CREATE TABLE movies (
                    id TEXT, wikidata_qid TEXT, title TEXT, native_title TEXT,
                    language_name TEXT, country_code TEXT, release_date TEXT,
                    verification_status TEXT, release_date_source TEXT,
                    poster_url TEXT, backdrop_url TEXT, artwork_source TEXT,
                    artwork_source_url TEXT, updated_at TEXT
                );
                CREATE TABLE source_channels (source_key TEXT, source_name TEXT);
                CREATE TABLE catalogue_titles (
                    id TEXT, wikidata_qid TEXT, title TEXT, language_name TEXT,
                    country_code TEXT, release_year INTEGER, verification_status TEXT,
                    source_category TEXT, source_url TEXT, updated_at TEXT
                );
            """)
            db.execute(
                "INSERT INTO source_channels VALUES (?, ?)",
                ("studio", "Official studio release"),
            )
            db.execute(
                "INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("m1", "Q111", "Day Film", None, "Telugu", "IN", "2025-01-03",
                 "verified", "studio", None, None, None, None, "2026-01-01"),
            )
            rows = (
                ("wd-Q222", "Q222", "Wikidata Film", "Unknown", "IN", 2024,
                 "unconfirmed", "wikidata:P31=film;P495=India;P577=release_year",
                 "https://www.wikidata.org/wiki/Q222", "2026-01-01"),
                ("wp-Q333", "Q333", "Wikipedia Film", "Telugu", "IN", 2023,
                 "unconfirmed", "Category:2023 Indian films",
                 "https://en.wikipedia.org/wiki/Wikipedia_Film", "2026-01-01"),
                ("wp-Q444", "Q444", "Untrusted URL Film", "Tamil", "IN", 2022,
                 "unconfirmed", "Category:2022 Indian films",
                 "javascript:alert(1)", "2026-01-01"),
            )
            db.executemany(
                "INSERT INTO catalogue_titles VALUES (?,?,?,?,?,?,?,?,?,?)", rows
            )
            records = db.execute(
                cte + " SELECT title, release_date_source, release_source_name, "
                "release_source_url, verification_status, release_date "
                "FROM combined_catalogue"
            ).fetchall()
        by_title = {record[0]: record[1:] for record in records}
        self.assertEqual(by_title["Wikidata Film"],
                         ("wikidata", "Wikidata film and year claims",
                          "https://www.wikidata.org/wiki/Q222", "unconfirmed", None))
        self.assertEqual(by_title["Wikipedia Film"],
                         ("wikipedia", "English Wikipedia film category",
                          "https://en.wikipedia.org/wiki/Wikipedia_Film",
                          "unconfirmed", None))
        self.assertIsNone(by_title["Untrusted URL Film"][2])
        self.assertEqual(by_title["Day Film"],
                         ("studio", "Official studio release", None, "verified",
                          "2025-01-03"))

    def test_broken_poster_has_title_initial_fallback(self):
        app = (WORKER.parents[0] / "src" / "App.tsx").read_text(encoding="utf-8")
        self.assertIn("onError={() => setFailed(true)}", app)
        self.assertIn('if (!url || failed)', app)
        self.assertIn("PosterArtwork", app)


if __name__ == "__main__":
    unittest.main()
