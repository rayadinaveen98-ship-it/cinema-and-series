import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import enrich_series_languages as module


def language_claim(qid, rank="normal"):
    return {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": {"entity-type": "item", "id": qid}},
        },
    }


class SeriesLanguageEnrichmentTests(unittest.TestCase):
    def test_candidates_require_unknown_language_and_valid_qid(self):
        rows = [
            {"id": "s1", "wikidata_qid": "Q1", "language_name": "Unknown"},
            {"id": "s2", "wikidata_qid": "Q2", "language_name": "Telugu"},
            {"id": "s3", "wikidata_qid": None, "language_name": "Unknown"},
            {"id": "s4", "wikidata_qid": "bad", "language_name": "Unknown"},
        ]
        selected = module.select_candidates(rows, 10)
        self.assertEqual([row["id"] for row in selected], ["s1"])

    def test_single_p364_claim_resolves(self):
        entity = {"claims": {"P364": [language_claim("Q1860")]}}
        self.assertEqual(module.claim_language_qids(entity), ("resolved", "Q1860"))

    def test_multiple_normal_languages_remain_ambiguous(self):
        entity = {"claims": {"P364": [language_claim("Q1860"), language_claim("Q809")]}}
        self.assertEqual(module.claim_language_qids(entity), ("ambiguous", None))

    def test_unique_preferred_language_wins_over_normal_claim(self):
        entity = {
            "claims": {
                "P364": [
                    language_claim("Q1860", rank="normal"),
                    language_claim("Q809", rank="preferred"),
                ]
            }
        }
        self.assertEqual(module.claim_language_qids(entity), ("resolved", "Q809"))

    def test_deprecated_claim_is_ignored(self):
        entity = {"claims": {"P364": [language_claim("Q1860", rank="deprecated")]}}
        self.assertEqual(module.claim_language_qids(entity), ("missing", None))

    def test_build_enrichment_requires_resolved_label(self):
        candidates = [
            {"id": "series-wd-Q10", "wikidata_qid": "Q10", "title": "Example", "language_name": "Unknown"}
        ]
        entities = {"Q10": {"claims": {"P364": [language_claim("Q809")]}}}
        report = module.build_enrichment(candidates, entities, {"Q809": "Polish"})
        self.assertEqual(report["update_count"], 1)
        self.assertEqual(report["updates"][0]["language"], "Polish")
        self.assertEqual(report["updates"][0]["language_source"], "wikidata:P364")

    def test_sql_never_overwrites_resolved_language(self):
        report = {
            "updates": [
                {
                    "id": "series-wd-Q10",
                    "wikidata_qid": "Q10",
                    "language": "Telugu",
                    "language_source": "wikidata:P364",
                    "language_source_url": "https://www.wikidata.org/wiki/Q10",
                }
            ]
        }
        sql = module.build_sql(report)
        self.assertIn("UPDATE series_titles", sql)
        self.assertIn("wikidata_qid='Q10'", sql)
        self.assertIn("LOWER(language_name)='unknown'", sql)
        self.assertIn("language_source='wikidata:P364'", sql)
        self.assertNotIn("country_code", sql)


if __name__ == "__main__":
    unittest.main()
