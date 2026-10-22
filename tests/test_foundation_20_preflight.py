import unittest
from scripts.foundation_20_preflight import (
    evaluate,preflight_query,test_rollback_simulation,validate_sources,
)


def fixture():
    sources=[]
    packet={"schema":"data-foundation-v2-20-film-dryrun-v1","batch_size":20,
            "production_writes":0,"ready_for_production_write":False,"items":[]}
    for n in range(1,21):
        qid=f"Q{n}"
        old={"table":"catalogue_titles","id":f"wd-{qid}","wikidata_qid":qid,
             "title":f"Film {n}","release_year":2010+n,"country_code":"IN",
             "language_name":"Unknown"}
        packet["items"].append({
            "before":old,"proposed":{"language_name":"Telugu"},
            "rollback":{"restore_language_name":"Unknown"},
            "human_approval":False,
            "source_independent_confirmation":"NOT_YET_OBTAINED",
        })
        sources.append({
            "wikidata_qid":qid,"language":"Telugu",
            "status":("SECONDARY_CORROBORATION_REVIEW_REQUIRED" if n<=17 else "HOLD_IDENTITY_REVIEW"),
            "independent_source_url":"https://www.imdb.com/title/test" if n<=17 else None,
            "evidence_description":"Film matching year and language",
            "approve_production_update":False,"studio_verified":False,
        })
    evidence={"schema":"foundation-v2-independent-source-review-v1",
              "no_d1_writes":True,"automatically_approved":0,"entries":sources}
    return packet,evidence


class FoundationPreflightTests(unittest.TestCase):
    def test_only_indexed_qids_and_select_statement(self):
        items=validate_sources(*fixture())
        query=preflight_query(items)
        self.assertTrue(query.startswith("SELECT "))
        self.assertIn("FROM catalogue_titles WHERE wikidata_qid IN",query)
        self.assertEqual(query.count("'Q"),20)
        self.assertNotIn("UPDATE",query.upper())
        self.assertNotIn("DELETE",query.upper())

    def test_source_domain_status_and_approval_are_fail_closed(self):
        p,s=fixture()
        s["entries"][0]["independent_source_url"]="https://wikidata.org/wiki/Q1"
        with self.assertRaises(ValueError):
            validate_sources(p,s)
        p,s=fixture()
        s["entries"][0]["approve_production_update"]=True
        with self.assertRaises(ValueError):
            validate_sources(p,s)

    def test_current_row_changed_or_missing_is_held(self):
        items=validate_sources(*fixture())
        live=[{k:v for k,v in x["before"].items() if k!="table"} for x in items]
        live[0]["language_name"]="Hindi"
        missing=live.pop(1)
        report=evaluate(items,live)
        self.assertEqual(report["total"],20)
        self.assertEqual(report["status_counts"]["HOLD_LIVE_ROW_MISSING_OR_CHANGED"],2)
        self.assertEqual(report["status_counts"]["HOLD_EXTERNAL_SOURCE_REVIEW"],3)
        self.assertEqual(report["status_counts"]["SOURCE_AND_LIVE_PRECONDITIONS_MET_REVIEW_REQUIRED"],15)
        self.assertFalse(report["owner_approved"])
        self.assertEqual(report["d1_writes"],0)

    def test_local_rollback_round_trip_restores_exact_values(self):
        items=validate_sources(*fixture())
        simulation=test_rollback_simulation(items)
        self.assertTrue(simulation["rollback_restores_all_original_rows"])
        self.assertFalse(simulation["production_rollback_tested"])
        self.assertEqual(simulation["source_supported_rows_tested"],17)


if __name__=="__main__":
    unittest.main()
