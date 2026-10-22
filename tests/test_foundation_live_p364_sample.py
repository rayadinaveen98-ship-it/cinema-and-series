"""Regression suite for source-only Wikidata P364 recheck: no DB writes."""
import unittest
from scripts.foundation_live_p364_sample import (
    LANGUAGES, choose_sample, recheck_item, recheck, claims_qids,
)


def proposal(lang, i):
    qid=f"Q{1000+i}"
    return {
        "source_table":"catalogue_titles", "source_id":"wd-"+qid,
        "wikidata_qid":qid,"title":f"Film {i}", "year":2000+i%20,
        "current_language":"Unknown", "proposed_language":lang,
        "claim_property":"P364","source_url":"https://www.wikidata.org/wiki/"+qid,
        "status":"REVIEW_REQUIRED",
    }


def claim(qid):
    return {"rank":"normal","mainsnak":{"snaktype":"value","datavalue":{"value":{"id":qid}}}}


def film_entity(row, original="Q123", date=True, multi=False, classname="Q11424",
                title=None):
    claims={"P31":[claim(classname)],"P364":[claim(original)]}
    if multi: claims["P364"].append(claim("Q999"))
    if date:
        claims["P577"]=[{
            "rank":"normal","mainsnak":{"snaktype":"value",
            "datavalue":{"value":{"time":f"+{row['year']:04d}-01-01T00:00:00Z"}}}
        }]
    return {"id":row["wikidata_qid"], "labels":{"en":{"value":title or row["title"]}},
            "aliases":{}, "claims":claims}


def sample_report():
    proposals=[]
    number=1000
    for lang in LANGUAGES:
        for _ in range(4):
            proposals.append(proposal(lang,number))
            number+=1
    return {"schema":"foundation-v2-language-review-v1",
            "d1_writes":0, "publication_performed":False,
            "automatic_corrections":0, "proposals":proposals}


class FoundationLiveSampleTests(unittest.TestCase):
    def test_sample_balanced_deterministic_and_order_independent(self):
        report=sample_report()
        a=choose_sample(report,per_language=2)
        b=choose_sample({**report,"proposals":list(reversed(report["proposals"]))},
                        per_language=2)
        self.assertEqual([x["wikidata_qid"] for x in a],
                         [x["wikidata_qid"] for x in b])
        self.assertEqual(len(a),20)
        self.assertEqual({l:2 for l in LANGUAGES},
                         {l:sum(x["proposed_language"]==l for x in a) for l in LANGUAGES})

    def test_current_source_requires_qid_title_year_language_and_film(self):
        row=proposal("Telugu",1111)
        self.assertEqual(
            recheck_item(row,film_entity(row),{"Q123":"Telugu"})["decision"],
            "SOURCE_RECHECK_PASSED_REVIEW_REQUIRED",
        )
        self.assertEqual(recheck_item(row,film_entity(row,title="Unrelated"),{"Q123":"Telugu"})["decision"],
                         "HOLD_CURRENT_SOURCE_TITLE_MISMATCH")
        self.assertEqual(recheck_item(row,film_entity(row,date=False),{"Q123":"Telugu"})["decision"],
                         "HOLD_CURRENT_SOURCE_RELEASE_YEAR")
        self.assertEqual(recheck_item(row,film_entity(row,classname="Q111"),{"Q123":"Telugu"})["decision"],
                         "HOLD_NOT_EXPLICIT_FILM_CLASS")
        self.assertEqual(recheck_item(row,film_entity(row,multi=True),{"Q123":"Telugu"})["decision"],
                         "HOLD_MULTILINGUAL_OR_MISSING_P364")
        self.assertEqual(recheck_item(row,film_entity(row),{"Q123":"Hindi"})["decision"],
                         "HOLD_CURRENT_SOURCE_LANGUAGE_MISMATCH")
        self.assertEqual(recheck_item(row,None,{"Q123":"Telugu"})["decision"],
                         "HOLD_IDENTITY_MISSING_OR_REDIRECTED")

    def test_bengali_bangla_equivalent_only_for_language_qid_q9610(self):
        row=proposal("Bengali",4040)
        self.assertEqual(
            recheck_item(row,film_entity(row,original="Q9610"),{"Q9610":"Bangla"})["decision"],
            "SOURCE_RECHECK_PASSED_REVIEW_REQUIRED",
        )
        # Same strings from an unrelated item must never be accepted.
        self.assertEqual(
            recheck_item(row,film_entity(row,original="Q99999"),{"Q99999":"Bangla"})["decision"],
            "HOLD_CURRENT_SOURCE_LANGUAGE_MISMATCH",
        )
        # A wrongly labeled proposed language is still held.
        wrong=proposal("Hindi",4041)
        self.assertEqual(
            recheck_item(wrong,film_entity(wrong,original="Q9610"),{"Q9610":"Bangla"})["decision"],
            "HOLD_CURRENT_SOURCE_LANGUAGE_MISMATCH",
        )

    def test_non_deprecated_claims_only(self):
        e={"claims":{"P364":[claim("Q1"),{**claim("Q2"),"rank":"deprecated"}]}}
        self.assertEqual(claims_qids(e,"P364"),{"Q1"})

    def test_api_error_never_results_in_passing_record(self):
        report=sample_report()
        def provider(ids):
            if all(int(q[1:]) >= 100000 for q in ids):
                return {},[{"qids":ids,"error_type":"OSError"}]
            return {},[{"qids":ids,"error_type":"OSError"}]
        out=recheck(report,per_language=1,get_entities=provider)
        self.assertEqual(out["sample_count"],10)
        self.assertEqual(out["decisions"]["SOURCE_UNAVAILABLE"],10)
        self.assertEqual(out["d1_writes"],0)
        self.assertEqual(out["automatically_approved"],0)

    def test_invalid_population_and_duplicate_qid_fail_closed(self):
        r=sample_report()
        r["proposals"][0]["source_url"]="https://evil.example"
        with self.assertRaises(ValueError):
            choose_sample(r,per_language=1)
        r=sample_report()
        r["proposals"][1]["wikidata_qid"]=r["proposals"][0]["wikidata_qid"]
        with self.assertRaises(ValueError):
            choose_sample(r,per_language=1)


if __name__=="__main__":
    unittest.main()
