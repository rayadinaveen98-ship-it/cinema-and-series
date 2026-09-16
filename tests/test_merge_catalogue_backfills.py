import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
MODULE_PATH = SCRIPTS / "merge_catalogue_backfills.py"
spec = importlib.util.spec_from_file_location("merge_catalogue_backfills", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def movie(qid, title, date, *, languages=None, country_code="IN", country_codes=None, countries=None):
    return {
        "wikidata_qid": qid,
        "title": title,
        "release_date": date,
        "candidate_dates": [date],
        "languages": languages or ["Hindi"],
        "country_code": country_code,
        "country_codes": country_codes or [country_code],
        "countries": countries or [],
        "source_url": f"https://www.wikidata.org/wiki/{qid}",
        "verification_status": "unconfirmed",
    }


class CatalogueBackfillMergeTests(unittest.TestCase):
    def test_unique_rows_from_both_sources_are_kept(self):
        wdqs = {"profile": "bootstrap", "acquisition_path": "wdqs", "movies": [movie("Q1", "One", "2001-01-01")]}
        mediawiki = {"profile": "global-recent", "acquisition_path": "mediawiki", "movies": [movie("Q2", "Two", "2020-02-02", country_code="US", country_codes=["US"])]}
        merged = module.merge_payloads([wdqs, mediawiki], 5000)
        self.assertEqual({row["wikidata_qid"] for row in merged["movies"]}, {"Q1", "Q2"})
        self.assertEqual(merged["acquisition_path"], "hybrid")

    def test_duplicate_qid_merges_dates_languages_and_countries(self):
        first = movie("Q10", "Film", "2020-05-10", languages=["Hindi"], country_code="US", country_codes=["US"], countries=["United States"])
        first["candidate_dates"] = ["2020-05-10", "2020-05-12"]
        second = movie("Q10", "Film", "2020-05-08", languages=["Tamil", "Unknown"], country_code="IN", country_codes=["IN"], countries=["India"])
        payloads = [
            {"profile": "bootstrap", "acquisition_path": "wdqs", "movies": [first]},
            {"profile": "global-recent", "acquisition_path": "mediawiki", "movies": [second]},
        ]
        merged = module.merge_payloads(payloads, 5000)["movies"][0]
        self.assertEqual(merged["release_date"], "2020-05-08")
        self.assertEqual(merged["candidate_dates"], ["2020-05-08", "2020-05-10", "2020-05-12"])
        self.assertEqual(merged["languages"], ["Hindi", "Tamil"])
        self.assertEqual(merged["country_codes"], ["IN", "US"])
        self.assertEqual(merged["country_code"], "IN")
        self.assertEqual(merged["countries"], ["India", "United States"])
        self.assertEqual(merged["acquisition_paths"], ["mediawiki", "wdqs"])

    def test_identity_is_qid_not_title(self):
        same_title_a = movie("Q20", "Same Title", "2019-01-01")
        same_title_b = movie("Q21", "Same Title", "2019-01-01")
        merged = module.merge_payloads([
            {"profile": "bootstrap", "acquisition_path": "wdqs", "movies": [same_title_a]},
            {"profile": "global-recent", "acquisition_path": "mediawiki", "movies": [same_title_b]},
        ], 5000)
        self.assertEqual(len(merged["movies"]), 2)

    def test_round_robin_cap_represents_both_sources(self):
        wdqs_movies = [movie(f"Q{index}", f"India {index}", f"2000-01-{index:02d}") for index in range(1, 6)]
        mediawiki_movies = [movie("Q100", "Global", "2020-01-01", country_code="JP", country_codes=["JP"])]
        merged = module.merge_payloads([
            {"profile": "bootstrap", "acquisition_path": "wdqs", "movies": wdqs_movies},
            {"profile": "global-recent", "acquisition_path": "mediawiki", "movies": mediawiki_movies},
        ], 2)
        self.assertEqual({row["wikidata_qid"] for row in merged["movies"]}, {"Q1", "Q100"})

    def test_unknown_language_is_dropped_when_real_language_exists(self):
        rows = [
            movie("Q30", "Film", "2021-01-01", languages=["Unknown"]),
            movie("Q30", "Film", "2021-01-01", languages=["Telugu"]),
        ]
        merged = module.merge_payloads([
            {"profile": "bootstrap", "acquisition_path": "wdqs", "movies": [rows[0]]},
            {"profile": "global-recent", "acquisition_path": "mediawiki", "movies": [rows[1]]},
        ], 5000)["movies"][0]
        self.assertEqual(merged["languages"], ["Telugu"])


if __name__ == "__main__":
    unittest.main()
