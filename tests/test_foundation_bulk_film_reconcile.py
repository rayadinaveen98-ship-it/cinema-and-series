"""Entire catalogue film reconciliation: exact-match, provenance and no write."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.foundation_bulk_film_reconcile import build, guarded_sql, write_package


def entry(qid="Q55", title="Film's Title", year=2020, *, table="catalogue", known=False):
    common={"id":"wd-"+qid,"wikidata_qid":qid,"title":title,
            "language_name":"Telugu" if known else "Unknown",
            "country_code":"IN"}
    if table=="movies":
        return {**common,"release_date":f"{year}-04-02"}
    return {**common,"release_year":year}


def source(qid="Q55", title="Film's Title", year=2020, language="Tamil",
           prop="P364"):
    return {"qid":qid,"title":title,"year":year,"language":language,
            "property":prop,"status":"single_language_evidence",
            "source_only":True,"officially_verified":False,
            "source_url":"https://www.wikidata.org/wiki/"+qid}


def cp(**records):
    return {"schema":"india-film-language-evidence-v1","records":records}


class BulkFilmReviewTests(unittest.TestCase):
    def test_exact_year_only_match_and_escaped_guarded_sql(self):
        result=build([], [entry()], [], cp(Q55=source()), require_production_baseline=False)
        self.assertEqual(result["correction_candidates"],1)
        self.assertEqual(result["by_table"],{"catalogue_titles":1})
        self.assertEqual(result["d1_writes"],0)
        self.assertFalse(result["writes_authorized"])
        statement=guarded_sql(result["records"][0])
        self.assertIn("Film''s Title",statement)
        self.assertIn("wikidata_qid='Q55'",statement)
        self.assertIn("release_year=2020",statement)
        self.assertIn("language_source='wikidata:P364'",statement)
        self.assertIn("language_source_url='https://www.wikidata.org/wiki/Q55'",statement)
        self.assertIn("language_name IS NULL",statement)
        with tempfile.TemporaryDirectory() as d:
            write_package(result,Path(d),chunk_size=1)
            plan=json.loads((Path(d)/"batch-plan.json").read_text())
            self.assertEqual(plan["correction_candidates"],1)
            self.assertEqual(len(plan["sql_batches"]),1)
            self.assertEqual(plan["writes_executed"],0)

    def test_exact_date_movies_get_exact_release_day_precondition(self):
        result=build([entry(table="movies")],[],[],cp(Q55=source()),
                     require_production_baseline=False)
        self.assertEqual(result["by_table"],{"movies":1})
        query=guarded_sql(result["records"][0])
        self.assertIn("release_date='2020-04-02'",query)
        self.assertNotIn("language_source=",query)
        self.assertIn("UPDATE movies SET",query)

    def test_existing_movie_suppresses_shadow_catalogue_record(self):
        result=build([entry(table="movies")],[entry()],[],
                     cp(Q55=source()),require_production_baseline=False)
        self.assertEqual(result["correction_candidates"],1)
        self.assertEqual(result["overlapping_catalogue_rows_suppressed"],1)

    def test_conflicting_title_year_p407_and_existing_known_held(self):
        result=build([],
          [entry("Q55"),entry("Q56",known=True),entry("Q57"),
           entry("Q58")],[],
          cp(Q55=source("Q55",year=2019),
             Q56=source("Q56"),Q57=source("Q57",prop="P407"),
             Q58=source("Q58",title="Other")),
          require_production_baseline=False)
        self.assertEqual(result["correction_candidates"],0)
        self.assertEqual(result["source_rule_holds"],3)

    def test_known_disputed_film_never_enters_sql_batches(self):
        qid="Q20967570"
        result=build([],[entry(qid)],[],cp(**{qid:source(qid)}),
                     require_production_baseline=False)
        self.assertEqual(result["correction_candidates"],0)
        self.assertEqual(result["manual_held"][0]["wikidata_qid"],qid)

    def test_strict_baseline_required_for_production(self):
        with self.assertRaisesRegex(ValueError,"Full production"):
            build([],[entry()],[],cp(Q55=source()),require_production_baseline=True)

    def test_sql_generator_rejects_unreviewed_record_or_bad_batch_size(self):
        result=build([],[entry()],[],cp(Q55=source()),require_production_baseline=False)
        bad=dict(result["records"][0],review_status="APPROVED")
        with self.assertRaises(ValueError):
            guarded_sql(bad)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_package(result,Path(d),chunk_size=500)


if __name__=="__main__":
    unittest.main()
