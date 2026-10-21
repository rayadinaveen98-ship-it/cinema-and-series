"""Archived artwork pilot must fail closed and show real identity blockers."""
import unittest
from scripts.audit_artwork70_snapshot import audit


def source(qid, title, url, name, year=2026, table="movies"):
    return {
        "source_table":table, "source_id":"wd-"+qid, "wikidata_qid":qid,
        "title":title, "year":year, "language":"Telugu","country":"IN",
        "media_type":"series" if table=="series_titles" else "movie",
        "status":"POSTER_CANDIDATE_REVIEW",
        "approved_for_publication":False, "production_written":False,
        "image":{
            "source":"wikipedia_article_pageimage", "file_page_url":url,
            "pageimage_filename":name,"image_url":"https://upload.wikimedia.org/poster.jpg",
            "width":500,"height":750,
        },
    }


def snapshot(items):
    return {"schema":"existing-title-artwork-pilot-v1",
            "selected_count":len(items),"candidates":items,
            "d1_writes":0, "publication_performed":False}


class AuditArtwork70Tests(unittest.TestCase):
    def test_identifies_panchanama_dragon_and_unrelated_file(self):
        data=snapshot([
            source("Q991","Panchanama","https://en.wikipedia.org/wiki/Panchanama_(2026_TV_series)","Panchanama_series.jpg"),
            source("Q992","Dragon","https://en.wikipedia.org/wiki/Dragon_(2025_film)","Dragon_2025_poster.jpg",year=2027),
            source("Q993","Dharmasthala Niyojakavargam","https://en.wikipedia.org/wiki/Dharmasthala_Niyojakavargam",
                   "Theatrical_poster_for_the_Telugu_film_Vaarasthula.jpg"),
            source("Q994","Peddi","https://en.wikipedia.org/wiki/Peddi","Peddi_Poster.jpg"),
        ])
        result=audit(data)
        self.assertEqual(result["selected_count"],4)
        self.assertEqual(result["media_type_mismatch_holds"],1)
        self.assertEqual(result["year_mismatch_holds"],1)
        self.assertEqual(result["poster_filename_review_count"],1)
        self.assertEqual({i["title"] for i in result["review_blockers"]},
                         {"Panchanama","Dragon","Dharmasthala Niyojakavargam"})
        self.assertTrue(all(not x["approved_for_publication"] for x in result["candidates"]))
        self.assertEqual(result["new_database_queries"],0)

    def test_does_not_trust_approved_or_duplicate_archive(self):
        a=source("Q1001","Peddi","https://en.wikipedia.org/wiki/Peddi","Peddi.jpg")
        with self.assertRaises(ValueError):
            audit(snapshot([{**a,"approved_for_publication":True}]))
        with self.assertRaises(ValueError):
            audit(snapshot([a,a]))

    def test_retains_both_saved_article_and_commons_candidates(self):
        a=source("Q1003","Peddi","https://en.wikipedia.org/wiki/Peddi_(2026_film)","Peddi.jpg")
        article={**a["image"],"width":900,"height":450}
        commons={**a["image"],"source":"wikidata_p18_commons",
                 "file_page_url":"https://commons.wikimedia.org/wiki/File:Peddi_poster.jpg",
                 "pageimage_filename":"Peddi_poster.jpg","width":500,"height":750}
        a["poster_candidate"]=commons
        a["backdrop_candidate"]=article
        a["image"]=commons
        report=audit(snapshot([a]))
        self.assertEqual(report["visible_artwork_candidates"],1)
        self.assertEqual(report["poster_candidates"],1)
        self.assertEqual(report["backdrop_candidates"],1)
        self.assertEqual(report["candidates"][0]["poster_candidate"]["source"],"wikidata_p18_commons")
        self.assertEqual(report["candidates"][0]["article_year"],2026)
        self.assertFalse(report["candidates"][0]["approved_for_publication"])

    def test_unknown_source_and_duplicate_qid_fail_closed(self):
        a=source("Q1004","Peddi","https://en.wikipedia.org/wiki/Peddi","Peddi.jpg")
        b={**a,"source_table":"catalogue_titles","source_id":"other-id"}
        with self.assertRaises(ValueError):
            audit(snapshot([a,b]))
        a["image"]["source"]="unverified_external_provider"
        with self.assertRaises(ValueError):
            audit(snapshot([a]))

    def test_missing_image_stays_unpublished(self):
        a=source("Q1001","Peddi","https://en.wikipedia.org/wiki/Peddi","Peddi.jpg")
        a["image"]=None
        result=audit(snapshot([a]))
        self.assertEqual(result["visible_artwork_candidates"],0)
        self.assertEqual(result["review_blockers"],[])


if __name__=="__main__":
    unittest.main()
