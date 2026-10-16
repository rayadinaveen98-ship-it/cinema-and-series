"""Offline checks for Wikidata-validated Indian film SQL preview."""
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_indian_movie_candidates import (
    validate, years_for_release, ids_for_claim, find_candidates, verify, sql_for_movie
)


def claim_id(qid):
    return {"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": qid}}}}


def claim_date(value, precision=11):
    return {"mainsnak": {"snaktype": "value", "datavalue": {
        "value": {"time": value, "precision": precision}}}}


def entity(kind="Q11424", country="Q668", date="+2025-07-03T00:00:00Z"):
    return {"claims": {"P31": [claim_id(kind)], "P495": [claim_id(country)],
                       "P577": [claim_date(date)]}}


def candidate(qid="Q123", year=2025, title="A Film", country=True):
    return {"wikidata_qid": qid, "year": year, "title": title, "page_id": 42,
            "india_category": country, "observed_languages": ["Telugu"],
            "source_categories": ["Category:2025 Telugu-language films"],
            "classification": "new_indian_category_candidates"}


class VerifiedMovieTests(unittest.TestCase):
    def test_claim_ids_and_year(self):
        e = entity()
        self.assertEqual(ids_for_claim(e, "P31"), {"Q11424"})
        self.assertEqual(years_for_release(e), {2025})
        self.assertEqual(validate(candidate(), e), "eligible")

    def test_rejects_non_film_and_non_india_and_bad_year(self):
        self.assertEqual(validate(candidate(), entity(kind="Q5398426")), "not_confirmed_film")
        self.assertEqual(validate(candidate(), entity(country="Q30")), "not_confirmed_indian_origin")
        self.assertEqual(validate(candidate(), entity(date="+2023-01-01T00:00:00Z")),
                         "release_year_not_corroborated")
        self.assertEqual(validate(candidate(), None), "entity_unavailable")

    def test_selects_only_net_new_candidates_with_qid(self):
        rows = [
            candidate(qid="Q10"),
            {**candidate(qid="Q20"), "classification": "already_in_production"},
            candidate(qid="Q10"),
            candidate(qid="bad"),
            {**candidate(qid="Q30"), "classification": "new_language_only_candidates"},
        ]
        selected = find_candidates({"candidates": rows}, 50)
        self.assertEqual({r["wikidata_qid"] for r in selected}, {"Q10", "Q30"})

    def test_sql_is_insert_only_and_guards_existing_records(self):
        sql = sql_for_movie(candidate(title="An Actor's Movie"))
        self.assertIn("INSERT OR IGNORE INTO catalogue_titles", sql)
        self.assertIn("NOT EXISTS (SELECT 1 FROM movies", sql)
        self.assertIn("NOT EXISTS (SELECT 1 FROM catalogue_titles", sql)
        self.assertIn("An Actor''s Movie", sql)
        self.assertNotIn("UPDATE SET", sql)

    def test_verify_stops_on_rate_limit(self):
        candidates = [candidate(qid=f"Q{i}") for i in range(20, 55)]
        exc = urllib.error.HTTPError("https://wikidata.org", 429, "Too Many", {}, None)
        with patch("verify_indian_movie_candidates.time.sleep"):
            result = verify(candidates, request_fn=lambda *_: (_ for _ in ()).throw(exc))
        self.assertTrue(result["rate_limited"])
        self.assertEqual(result["checked"], 0)
        self.assertEqual(len(result["rejected"]), 15)

    def test_verify_accepts_corroborated_film(self):
        candidates = [candidate()]
        with patch("verify_indian_movie_candidates.time.sleep"):
            out = verify(candidates, request_fn=lambda *_: {"entities": {"Q123": entity()}})
        self.assertEqual(len(out["accepted"]), 1)
        self.assertEqual(out["checked"], 1)


if __name__ == "__main__":
    unittest.main()
