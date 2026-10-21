"""Fast visible artwork candidates for actual 50+20 production identities."""
import unittest

from scripts.artwork_fast_70 import select, shape, run, attach_candidates


def row(prefix: str, number: int):
    table={"m":"movies","c":"catalogue_titles","s":"series_titles"}[prefix]
    return {
        "id":table+"-Q"+str(number), "wikidata_qid":"Q"+str(number),
        "title": "Title "+str(number), "year":2025,
        "language_name":"Telugu", "country_code":"IN",
    }


class ArtworkFast70Tests(unittest.TestCase):
    def test_selects_exact_35_movie_15_catalogue_20_series_and_deduplicates(self):
        rows={
            "movies":[row("m",i) for i in range(100,150)],
            "catalogue_titles":[row("c",i) for i in range(100,150)]
                               +[row("c",i) for i in range(150,180)],
            "series_titles":[row("s",i) for i in range(180,240)],
        }
        selected=select(rows)
        self.assertEqual(len(selected),70)
        self.assertEqual(len({x["wikidata_qid"] for x in selected}),70)
        self.assertEqual([sum(x["source_table"]==t for x in selected)
                          for t in ("movies","catalogue_titles","series_titles")],
                          [35,15,20])
        self.assertTrue(all(x["approved_for_publication"] is False
                            and not x["production_written"] for x in selected))

    def test_separates_portrait_and_backdrop_not_a_random_poster(self):
        self.assertEqual(shape({"width":600,"height":900}),"poster")
        self.assertEqual(shape({"width":1600,"height":900}),"backdrop")
        self.assertEqual(shape({"width":950,"height":900}),"unknown")
        self.assertEqual(shape({"width":0,"height":600}),"unknown")
        self.assertEqual(shape(None),"unknown")
        qid="Q777"
        rows={"movies":[row("m",777)],"catalogue_titles":[],"series_titles":[]}
        article={
            "image_url":"https://upload.wikimedia.org/wikipedia/en/thumb/poster.jpg",
            "width":650,"height":975,
            "file_page_url":"https://en.wikipedia.org/wiki/Film",
            "match_basis":"EXACT_PAGEPROP_WIKIBASE_ITEM",
        }
        backdrop={
            "image_url":"https://upload.wikimedia.org/wikipedia/commons/thumb/backdrop.jpg",
            "width":1600,"height":900,
            "file_page_url":"https://commons.wikimedia.org/wiki/File:Backdrop.jpg",
            "match_basis":"EXACT_WIKIDATA_QID_P18",
        }
        result=run(rows,
            get_links=lambda qs:({qid:("enwiki","Title 777")},0),
            get_images=lambda link:({qid:article},0),
            get_p18=lambda qs:{qid:"Backdrop.jpg"},
            get_commons=lambda names:{"backdrop.jpg":backdrop})
        self.assertEqual(result["selected_count"],1)
        self.assertEqual(result["poster_candidates"],1)
        self.assertEqual(result["backdrop_candidates"],0)
        self.assertEqual(result["d1_writes"],0)
        self.assertEqual(result["candidates"][0]["poster_candidate"]["image_url"],article["image_url"])
        self.assertFalse(result["candidates"][0]["approved_for_publication"])

    def test_no_image_is_not_marked_as_publishable(self):
        selected=select({"movies":[row("m",333)]})
        outcome=attach_candidates(selected,{}, {}, {"site":0})
        self.assertEqual(outcome["poster_candidates"],0)
        self.assertEqual(outcome["visible_artwork_candidates"],0)
        self.assertEqual(outcome["status_counts"],{"NO_IMAGE_FOUND":1})
        self.assertFalse(outcome["publication_performed"])

    def test_unclear_title_and_year_never_selected(self):
        a=row("m",900)
        a["title"]="Q900"
        b=row("m",901)
        b["year"]=None
        c=row("m",902)
        c["wikidata_qid"]=None
        self.assertEqual(select({"movies":[a,b,c]}),[])

    def test_source_errors_are_explicit_but_do_not_publish(self):
        rows={"movies":[row("m",200)],"catalogue_titles":[],"series_titles":[]}
        result=run(rows,
            get_links=lambda qs:({},1),
            get_images=lambda links:({},0),
            get_p18=lambda qs:{},
            get_commons=lambda files:{})
        self.assertEqual(result["source_errors"]["wikidata_sitelink_batches"],1)
        self.assertEqual(result["status_counts"],{"NO_IMAGE_FOUND":1})


if __name__=="__main__":
    unittest.main()
