"""Immediate artwork discovery must never confuse external QIDs with D1 records."""
import unittest

from scripts.artwork_bulk_500_source_now import run, select_external


def archive():
    rows=[]
    for i in range(100,170):
        rows.append({
            "source_table":"movies","source_id":f"movie-Q{i}",
            "wikidata_qid":f"Q{i}","title":f"Archived {i}","year":2026,
            "language":"Telugu","media_type":"movie","country":"IN",
            "status":"POSTER_CANDIDATE_REVIEW",
            "poster_candidate":None,"backdrop_candidate":None,"image":None,
            "approved_for_publication":False,"production_written":False,
        })
    return {"schema":"existing-title-artwork-pilot-v1",
            "selected_count":70,"d1_writes":0,
            "publication_performed":False,"candidates":rows}


def source_state():
    queue={}
    for i in range(150,650):
        queue[f"Q{i}"]={
            "wikidata_qid":f"Q{i}","page_id":i,
            "title":f"New Film {i}",
            "observed_years":[2026],
            "source_categories":["Category:2026 Indian films", "Category:2026 Telugu-language films"],
            "observed_languages":["Telugu"],
            "india_category":True,
        }
    return {"schema_version":1,"queue":queue}


class ImmediateArtworkTests(unittest.TestCase):
    def test_70_archived_plus_430_unconfirmed_source_identities(self):
        result=run(archive(), source_state(),
                   get_links=lambda qs: ({},0),
                   get_images=lambda links: ({},0),
                   get_p18=lambda qs: {},
                   get_commons=lambda names: {})
        self.assertEqual(result["selected"],500)
        self.assertEqual(result["from_existing_d1_archive"],70)
        self.assertEqual(result["from_unconfirmed_source_queue"],430)
        self.assertEqual(len({x["wikidata_qid"] for x in result["candidates"]}),500)
        self.assertEqual(sum(bool(x["database_identity_confirmed"]) for x in result["candidates"]),70)
        self.assertEqual(result["d1_reads"],0)
        self.assertEqual(result["d1_writes"],0)
        self.assertEqual(result["published_in_app"],0)
        self.assertEqual(result["rights_automatically_approved"],0)

    def test_external_article_poster_is_not_mislabeled_as_publishable(self):
        def links(qs):
            return {qid:("enwiki","Some Film (2026 film)") for qid in qs},0
        def images(chosen):
            return {qid:{
                "source":"wikipedia_article_pageimage",
                "file_page_url":"https://en.wikipedia.org/wiki/Some_Film_(2026_film)",
                "image_url":"https://upload.wikimedia.org/wikipedia/en/p/poster.jpg",
                "width":600,"height":900,"pageimage_filename":"Some_film_poster.jpg"
            } for qid in chosen},0
        r=run(archive(), source_state(),get_links=links,get_images=images,
              get_p18=lambda qs:{},get_commons=lambda names:{})
        self.assertEqual(r["new_external_poster_leads"],430)
        self.assertEqual(r["published_in_app"],0)
        self.assertFalse(any(x["approved_for_publication"] for x in r["candidates"]))
        self.assertTrue(all(x["source_id"] is None for x in r["candidates"][70:]))

    def test_rejects_archived_published_or_d1_tampered_sources(self):
        a=archive()
        a["candidates"][0]["approved_for_publication"]=True
        with self.assertRaises(ValueError):
            run(a,source_state(),get_links=lambda qs:({},0),get_images=lambda x:({},0))
        a=archive()
        a["d1_writes"]=1
        with self.assertRaises(ValueError):
            run(a,source_state(),get_links=lambda qs:({},0),get_images=lambda x:({},0))

    def test_rejects_unverified_source_queue_schema(self):
        with self.assertRaises(ValueError):
            select_external({"schema_version":2,"queue":{}},set(),430)


if __name__=="__main__":
    unittest.main()
