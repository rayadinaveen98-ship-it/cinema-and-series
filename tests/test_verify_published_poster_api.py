"""The actual Worker must expose every published CC poster and its credit."""
import unittest
from scripts.verify_published_poster_api import verify_all, verify_film, public_url


def item():
    return {
        "title":"Yaanai","year":2022,"ticket":"2022031910001078",
        "source_url":"https://commons.wikimedia.org/wiki/File:Yaanai_Poster.jpg",
        "delivery_url":"https://thumb.wikimedia.org/wikipedia/commons/jaanai.jpg",
        "license":"https://creativecommons.org/licenses/by-sa/4.0/",
        "source_ids":[{"table":"catalogue_titles","id":"wd-Q400","qid":"Q400"}],
    }


def payload(**changes):
    film = {
        "id":"wd-Q400","wikidataQid":"Q400","title":"Yaanai",
        "posterUrl":item()["delivery_url"],
        "artworkSource":"wikimedia_commons_vrt",
        "artworkSourceUrl":item()["source_url"],
        "artworkAttribution":"Yaanai poster CC BY-SA 4.0 VRT #2022031910001078",
        "artworkLicenseUrl":item()["license"],
    }
    film.update(changes)
    return {"source":"d1","movies":[film]}


class LivePublishedPosterAcceptanceTests(unittest.TestCase):
    def test_exact_id_poster_and_license_source_is_accepted(self):
        approved = item()
        result = verify_film(approved,payload())
        self.assertTrue(result["poster_displayed_in_api"])
        self.assertEqual(result["linked_ids"],["wd-Q400"])

    def test_hidden_year_duplicate_does_not_fail_public_api_acceptance(self):
        film = item()
        film["source_ids"].append({
            "table":"movies","id":"movie-Q400","qid":"Q400"
        })
        result=verify_film(film,payload())
        self.assertEqual(result["linked_ids"],["wd-Q400"])

    def test_wrong_qid_id_or_attribution_is_rejected(self):
        for film_change in (
            {"wikidataQid":"Q401"},{"id":"wrong-title"},
            {"posterUrl":"https://example.com/unapproved.jpg"},
            {"artworkLicenseUrl":None},{"artworkSource":"wikipedia_nonfree"},
            {"artworkSourceUrl":None},{"artworkAttribution":"No evidence"},
        ):
            with self.subTest(change=film_change),self.assertRaises(ValueError):
                verify_film(item(),payload(**film_change))

    def test_fresh_query_and_exact_year_are_required(self):
        value=public_url("https://example.com/",item(),"run393",1)
        self.assertTrue(value.startswith("https://example.com/api/movies?"))
        self.assertIn("q=Yaanai",value)
        self.assertIn("year=2022",value)
        self.assertIn("artworkBatch02=run393-1-2022031910001078",value)
        self.assertIn("meta=0",value)

    def test_exact_verified_d1_readback_required_before_api(self):
        proof={"ready":[item()],"verified_titles":["Other film"],"published":1}
        with self.assertRaises(ValueError):
            verify_all(proof,fetch=lambda url:payload(),delay_seconds=0)
        proof["verified_titles"]=["Yaanai"]
        proof["published"]=0
        with self.assertRaises(ValueError):
            verify_all(proof,fetch=lambda url:payload(),delay_seconds=0)

    def test_missing_live_artwork_fails_with_specific_error(self):
        proof={"ready":[item()],"verified_titles":["Yaanai"],"published":1}
        urls=[]
        def missing(url):
            urls.append(url)
            return payload(artworkLicenseUrl=None)
        outcome=verify_all(proof,fetch=missing,attempts=2,delay_seconds=0,cache_nonce="test")
        self.assertEqual(outcome["published_in_d1"],1)
        self.assertEqual(outcome["visible_in_public_api"],0)
        self.assertEqual(len(outcome["failed"]),1)
        self.assertEqual(len(urls),2)
        self.assertNotEqual(urls[0],urls[1])

    def test_successful_production_api_counts_each_verified_title(self):
        proof={"ready":[item()],"verified_titles":["Yaanai"],"published":1}
        outcome=verify_all(proof,fetch=lambda url:payload(),attempts=1,delay_seconds=0)
        self.assertEqual(outcome["visible_in_public_api"],1)
        self.assertEqual(outcome["failed"],[])

    def test_skipped_source_candidates_never_count_as_published(self):
        proof={"ready":[],"verified_titles":[],"published":0}
        outcome=verify_all(proof,fetch=lambda url:None,attempts=1)
        self.assertEqual(outcome["visible_in_public_api"],0)
        self.assertEqual(outcome["published_in_d1"],0)


if __name__=="__main__":
    unittest.main()
