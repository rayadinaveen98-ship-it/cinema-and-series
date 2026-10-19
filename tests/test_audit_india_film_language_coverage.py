"""Source-only film-language coverage audit regression checks."""
import unittest

from scripts.audit_india_film_language_coverage import audit


def evidence(qid, year, title, *, status="single_language_evidence",
             prop="P364", language="Telugu"):
    return {"qid": qid, "year": year, "title": title, "status": status,
            "property": prop, "language": language,
            "source_only": True, "officially_verified": False}


class FilmLanguageCoverageTests(unittest.TestCase):
    def test_decade_counts_and_p364_only(self):
        staged = {
            "Q100": {"year": 2024, "title": "A Film"},
            "Q101": {"year": 2021, "title": "B Film"},
            "Q102": {"year": 1967, "title": "Classic Film"},
            "Q103": {"year": 1962, "title": "Other Film"},
        }
        checkpoint = {"schema": "india-film-language-evidence-v1", "records": {
            "Q100": evidence("Q100", 2024, "A Film"),
            "Q101": evidence("Q101", 2021, "B Film", prop="P407", language="Hindi"),
            "Q102": evidence("Q102", 1967, "Classic Film", language="Tamil"),
        }}
        report = audit(staged, checkpoint)
        self.assertEqual(report["matched_reviewed_identities"], 3)
        self.assertEqual(report["strict_original_language"], 2)
        self.assertEqual(report["by_decade"]["1960"]["source_films"], 2)
        self.assertEqual(report["by_decade"]["1960"]["strict_original_language"], 1)
        self.assertEqual(report["by_decade"]["2020"]["reviewed_identities"], 2)
        self.assertEqual(report["by_decade"]["2020"]["strict_original_language"], 1)
        self.assertEqual(report["strict_languages"], {"Tamil": 1, "Telugu": 1})
        self.assertEqual(report["d1_reads"], 0)
        self.assertEqual(report["d1_writes"], 0)

    def test_identity_and_year_orphans_held_not_counted(self):
        staged = {
            "Q11": {"year": 1981, "title": "Film One"},
            "Q12": {"year": 1982, "title": "Film Two"},
            "Q13": {"year": 1983, "title": "Film Three"},
        }
        checkpoint = {"schema": "india-film-language-evidence-v1", "records": {
            "Q11": evidence("Q11", 1985, "Film One"),
            "Q12": evidence("Q12", 1982, "Different"),
            "Q13": evidence("Q999", 1983, "Film Three"),
            "Q14": evidence("Q14", 1984, "Other"),
        }}
        report = audit(staged, checkpoint)
        self.assertEqual(report["matched_reviewed_identities"], 0)
        held = report["held_for_review"]
        self.assertEqual(held["year_mismatch"]["count"], 1)
        self.assertEqual(held["title_mismatch"]["count"], 1)
        self.assertEqual(held["invalid_identity"]["count"], 1)
        self.assertEqual(held["not_in_stage"]["count"], 1)

    def test_unknown_schema_and_invalid_stage_fail(self):
        with self.assertRaises(ValueError):
            audit({"Q12": {"year": 2023, "title": "A"}},
                  {"schema": "old", "records": {}})
        with self.assertRaises(ValueError):
            audit({"invalid": {"year": 2023, "title": "A"}},
                  {"schema": "india-film-language-evidence-v1", "records": {}})


if __name__ == "__main__":
    unittest.main()
