"""Tests for 20-film review packet: balanced, guarded, never writing."""
import copy
import unittest

from scripts.foundation_20_film_dryrun import select_twenty, stable_hash, build, LANGUAGES


def fixture():
    names = list(LANGUAGES)
    population = []
    sample = []
    for lang_index, lang in enumerate(names):
        for k in range(8):
            i = lang_index * 8 + k + 1000
            qid = f"Q{i}"
            item = {
                "wikidata_qid": qid, "source_id":f"wd-{qid}",
                "source_table":"catalogue_titles",
                "title":f"Film {i}", "year":1950+k*8,
                "current_language":"Unknown", "proposed_language":lang,
                "claim_property":"P364", "source_url":f"https://www.wikidata.org/wiki/{qid}",
                "status":"REVIEW_REQUIRED",
            }
            population.append(item)
            sample.append({
                **item,"source_years":str(item["year"]),
                "source_language":lang if lang != "Bengali" else "Bangla",
                "language_qid":f"Q{lang_index+100}",
                "decision":"SOURCE_RECHECK_PASSED_REVIEW_REQUIRED",
                "review_only":True,"production_written":False,
            })
    for i in range(80,6048):
        i+=2000
        population.append({
            **population[0],
            "wikidata_qid":f"Q{i}",
            "source_id":f"wd-Q{i}",
            "source_url":f"https://www.wikidata.org/wiki/Q{i}",
        })
    review={"schema":"foundation-v2-language-review-v1",
            "d1_writes":0,"automatic_corrections":0,
            "publication_performed":False,"proposals":population}
    live={"schema":"data-foundation-v2-live-p364-sample-v1",
          "population_proposals":6048, "sample_count":80,
          "d1_reads":0,"d1_writes":0,"sql_generated":False,
          "automatically_approved":0,"source_error_batches":0,
          "review_queue":sample}
    return review,live


class FoundationTwentyTests(unittest.TestCase):
    def test_balanced_two_from_each_of_ten_languages(self):
        r,l=fixture()
        selected, seen=select_twenty(r,l)
        self.assertEqual(len(seen),80)
        self.assertEqual(len(selected),20)
        self.assertEqual({lang:2 for lang in LANGUAGES},
            {lang:sum(x["proposed_language"]==lang for x in selected)
             for lang in LANGUAGES})
        self.assertEqual([r["wikidata_qid"] for r in selected],
                         [r["wikidata_qid"] for r in select_twenty(
                            r,{**l,"review_queue":list(reversed(l["review_queue"]))})[0]])

    def test_rejects_mismatched_source_title_year_or_id(self):
        for key,bad in [
            ("year",9999),("source_id","wrong"),("title","Another film"),
            ("source_url","https://example.invalid"),
            ("claim_property","P407"),
            ("production_written",True),
        ]:
            r,l=fixture()
            l["review_queue"][0][key]=bad
            with self.subTest(key=key),self.assertRaises(ValueError):
                select_twenty(r,l)

    def test_missing_language_or_nonpassing_recheck_not_used(self):
        r,l=fixture()
        l["review_queue"][0]["decision"]="SOURCE_UNAVAILABLE"
        with self.assertRaises(ValueError):
            select_twenty(r,l)

    def test_frozen_baseline_guard_fails_before_any_changes(self):
        r,l=fixture()
        with self.assertRaisesRegex(ValueError,"Production snapshot"):
            build(r,l,[],[],[])

    def test_precondition_hash_is_deterministic(self):
        a={"id":"wd-Q1","title":"Film","language_name":"Unknown"}
        self.assertEqual(stable_hash(a),stable_hash(dict(reversed(list(a.items())))))
        self.assertNotEqual(stable_hash(a),stable_hash({**a,"language_name":"Hindi"}))


if __name__=="__main__":
    unittest.main()
