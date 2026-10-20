"""Series growth must not duplicate movie or series identities."""
import tempfile
import unittest
from pathlib import Path
from scripts.oct20_new_series_import import choose, sql_for_series, apply, D1QuotaReached


def series(qid, year=2024, title=None):
    return {
        "id":"series-wd-"+qid,"wikidata_qid":qid,"wikipedia_page_id":int(qid[1:])+100,
        "title":title or "Show "+qid,"first_air_year":year,
        "source_category":f"Category:{year} Indian television series debuts",
        "source_url":"https://en.wikipedia.org/?curid="+str(int(qid[1:])+100),
        "country_code":"IN","series_kind":"series"
    }


class NewSeriesImportTests(unittest.TestCase):
    def test_identity_year_and_cross_type_collisions(self):
        src=[series("Q100"),series("Q101"),series("Q102"),series("Q103"),series("Q104")]
        exact=[{"wikidata_qid":"Q100","title":"Show Q100","release_date":"2024-01-01"}]
        catalogue=[{"wikidata_qid":"Q101","title":"Show Q101","release_year":2024}]
        prior=[{"wikidata_qid":"Q102","title":"Show Q102","first_air_year":2024}]
        selected,report=choose(src,exact,catalogue,prior)
        self.assertEqual([s["wikidata_qid"] for s in selected],["Q103","Q104"])
        self.assertEqual(report["selected_net_new"],2)

    def test_ambiguous_source_and_missing_qid_rejected(self):
        src=[series("Q201"),series("Q202")]
        src[0]["first_air_year"]=None
        src[1]["wikidata_qid"]=None
        selected,report=choose(src,[],[],[])
        self.assertEqual(selected,[])
        self.assertEqual(report["held_reasons"]["not_exact_year_country_series"],2)

    def test_insert_only_sql_and_cross_type_guards(self):
        sql=sql_for_series(series("Q990"))
        self.assertIn("INSERT OR IGNORE INTO series_titles",sql)
        self.assertIn("FROM catalogue_titles",sql)
        self.assertIn("FROM movies",sql)
        self.assertIn("FROM series_titles",sql)
        self.assertIn("'unconfirmed'",sql)
        self.assertNotIn("UPDATE series_titles",sql)
        with self.assertRaises(ValueError):
            bad=series("Q902")
            bad["source_category"]="Category:2024 Films"
            sql_for_series(bad)

    def test_actual_series_qids_verified_and_quota_stops(self):
        src=[series("Q333"),series("Q334")]
        with tempfile.TemporaryDirectory() as folder:
            result=apply(src,Path(folder),execute=lambda **kwargs:("",12),
                         get_qids=lambda qids:set(qids))
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["verified_present_new_qids"],2)
        with tempfile.TemporaryDirectory() as folder:
            def quota(**kwargs):
                raise D1QuotaReached("Cloudflare 7500")
            res=apply(src,Path(folder),execute=quota,get_qids=lambda qids:set(qids))
        self.assertEqual(res["status"],"cloudflare_quota_paused")
        self.assertEqual(res["verified_present_new_qids"],0)


if __name__=="__main__":
    unittest.main()
