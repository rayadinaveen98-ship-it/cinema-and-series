"""Verify third-party evidence and bounded live D1 preflight never approve a write."""
import copy
import unittest

from scripts.foundation_external_preflight import build


def fixtures():
    items=[];sources=[];current=[]
    for i in range(20):
        qid=f"Q{i+10000}"
        lang="Hindi"
        items.append({
            "before":{"table":"catalogue_titles","id":"wd-"+qid,"wikidata_qid":qid,
                      "title":f"Title {i}","release_year":2000+i,
                      "country_code":"IN","language_name":"Unknown"},
            "proposed":{"language_name":lang}
        })
        sources.append({"wikidata_qid":qid,"proposed_language":lang,
                        "frozen_release_year":2000+i,
                        "source_url":"https://www.imdb.com/title/tt0000001/",
                        "decision":"SUPPORT","production_update_authorized":False,
                        "review_note":"validated source"})
        current.append({"id":"wd-"+qid,"wikidata_qid":qid,
                        "title":f"Title {i}","release_year":2000+i,
                        "country_code":"IN","language_name":"Unknown"})
    packet={"schema":"data-foundation-v2-20-film-dryrun-v1",
            "batch_size":20,"ready_for_production_write":False,
            "production_writes":0,"items":items}
    evidence={"schema":"data-foundation-v2-external-evidence-20-v1",
              "proposed_writes":0,"records":sources}
    return packet,evidence,current


class EvidencePreflightTests(unittest.TestCase):
    def test_nonmutating_all_supported(self):
        p,e,rows=fixtures()
        r=build(p,e,rows)
        self.assertEqual(r["preflight_existing_titles"],20)
        self.assertEqual(r["review_candidates"],20)
        self.assertEqual(r["held"],0)
        self.assertEqual(r["d1_writes"],0)
        self.assertEqual(r["automatically_approved"],0)
        self.assertFalse(r["production_write_authorized"])
        self.assertFalse(r["sql_generated"])

    def test_date_conflict_and_weak_source_remain_held(self):
        p,e,rows=fixtures()
        e["records"][0]["decision"]="HOLD_YEAR_CONFLICT"
        e["records"][1]["decision"]="HOLD_WEAK_INDEPENDENT_IDENTITY"
        r=build(p,e,rows)
        self.assertEqual(r["held"],2)
        self.assertEqual(r["review_candidates"],18)

    def test_live_database_value_drift_is_held(self):
        p,e,rows=fixtures()
        rows[2]["language_name"]="Telugu"
        rows[3]["release_year"]=1990
        r=build(p,e,rows)
        self.assertEqual(r["held"],2)
        self.assertEqual(r["results"][2]["production_status"],"HOLD_PRODUCTION_DRIFT")
        self.assertEqual(r["results"][3]["production_status"],"HOLD_PRODUCTION_DRIFT")

    def test_duplicate_db_qid_and_missing_db_qid_are_held(self):
        p,e,rows=fixtures()
        rows.pop(1)
        rows.append(dict(rows[2]))
        r=build(p,e,rows)
        self.assertEqual(r["held"],2)
        self.assertEqual(r["results"][1]["production_status"],"HOLD_MISSING_OR_MULTIPLE_CURRENT_ROWS")
        self.assertEqual(r["results"][2]["production_status"],"HOLD_MISSING_OR_MULTIPLE_CURRENT_ROWS")

    def test_no_writes_approved_through_evidence(self):
        p,e,rows=fixtures()
        e["records"][0]["production_update_authorized"]=True
        with self.assertRaises(ValueError):
            build(p,e,rows)

    def test_missing_evidence_and_no_external_source_fail(self):
        p,e,rows=fixtures()
        e["records"][0]["source_url"]="https://www.wikidata.org/wiki/Q10000"
        with self.assertRaises(ValueError):
            build(p,e,rows)
        p,e,rows=fixtures()
        e["records"].pop()
        with self.assertRaises(ValueError):
            build(p,e,rows)


if __name__=="__main__":
    unittest.main()
