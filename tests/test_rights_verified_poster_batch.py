"""The VRT poster batch must fail closed on identity and permission mismatches."""
import tempfile
import unittest
from pathlib import Path

from scripts.rights_verified_poster_batch import POSTERS, prepare, sql, matches, verified_metadata, LICENSE


def movie(entry, table="catalogue_titles", qid="Q2100"):
    return {"id":"wd-"+qid,"title":entry["title"],"release_year":entry["year"],
            "wikidata_qid":qid,"country_code":"IN","source_table":table}


def commons_response(entry, license_name="CC BY-SA 4.0", ticket=True):
    return {"query":{"pages":{"12":{
        "title":"File:"+entry["file"],
        "imageinfo":[{"thumburl":"https://thumb.wikimedia.org/wikipedia/commons/thumb/p/poster.jpg",
                      "thumbwidth":600,"thumbheight":900,"extmetadata":{
                      "LicenseShortName":{"value":license_name},
                      "LicenseUrl":{"value":LICENSE}}}],
        "revisions":[{"slots":{"main":{"*":'{{PermissionOTRS|id='+entry["ticket"]+'}}' if ticket else 'All rights reserved'}}}]
    }}}}

def probe(entry, license_name="CC BY-SA 4.0", ticket=True):
    def fetch(url,params):
        if params.get("action")=="parse":
            return {"parse":{"title":"File:"+entry["file"],"text":{"*":
                "<div class='VRT permission'>ticket #"+entry["ticket"]+"</div>"
                if ticket else "<div>No permission</div>"}}}
        return commons_response(entry,license_name=license_name,ticket=ticket)
    return fetch

class RightsVerifiedBatchTests(unittest.TestCase):
    def test_exact_qid_year_and_conflicting_identities(self):
        p=POSTERS[0]
        good=movie(p)
        self.assertEqual(matches([good],p),[good])
        self.assertEqual(matches([{**good,"release_year":2023}],p),[])
        self.assertEqual(matches([good,{**good,"id":"other","wikidata_qid":"Q8888"}],p),[])
        self.assertEqual(matches([good,{**good,"id":"other","source_table":"catalogue_titles"}],p),[])
        self.assertEqual(matches([good,{**good,"id":"day-id","source_table":"movies"}],p).__len__(),2)

    def test_license_file_ticket_and_url_are_not_guessed(self):
        p=POSTERS[0]
        ok=verified_metadata(p,probe(p))
        self.assertEqual(ok["ticket"],p["ticket"])
        self.assertEqual(ok["license"],LICENSE)
        for settings in ({"license_name":"Non-free"},{"ticket":False}):
            with self.assertRaises(ValueError):
                verified_metadata(p,probe(p,**settings))
        wrong=commons_response(p)
        wrong["query"]["pages"]["12"]["imageinfo"][0]["thumburl"]="https://example.org/spoof.jpg"
        def wrong_host(url,params):
            return wrong if params.get("action")=="query" else probe(p)(url,params)
        with self.assertRaises(ValueError):
            verified_metadata(p,wrong_host)

    def test_insert_only_provenance_and_exact_db_binding(self):
        p=POSTERS[1]
        row=movie(p)
        image=verified_metadata(p,probe(p))
        statement=sql(p,[row],image)
        self.assertIn("OPEN_LICENSE_VERIFIED",statement)
        self.assertIn("INSERT OR IGNORE INTO artwork_assets",statement)
        self.assertIn("INSERT OR IGNORE INTO title_artwork_links",statement)
        self.assertIn(row["id"],statement)
        self.assertIn(row["wikidata_qid"],statement)
        self.assertIn("rights_reference",statement)
        self.assertIn("Permission",p["ticket"]+" Permission")
        self.assertNotIn("UPDATE ",statement)
        self.assertNotIn("DELETE ",statement)

    def test_only_current_existing_titles_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            records=[movie(POSTERS[0])]
            def fetch(url,params):
                return probe(POSTERS[0])(url,params)
            report=prepare([],records,Path(td),fetch=fetch)
            self.assertEqual(report["planned_sql_writes"],1)
            self.assertEqual(len(report["ready"]),1)
            self.assertEqual(len(report["held"]),len(POSTERS)-1)
            self.assertFalse(report["published"])
            self.assertTrue((Path(td)/report["ready"][0]["sql_filename"]).exists())

if __name__=="__main__":
    unittest.main()
