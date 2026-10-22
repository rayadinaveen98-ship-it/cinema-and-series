"""Source-only film language review must not guess, write, or double-count."""
import unittest

from scripts.foundation_language_review import build


def movie(qid="Q55", *, title="Test Film", language="Unknown", year=2020):
    return {"id":"wd-"+qid, "wikidata_qid":qid, "title":title,
            "language_name":language, "country_code":"IN",
            "release_date":f"{year}-04-01"}


def evidence(qid="Q55", *, title="Test Film", language="Telugu", property="P364",
             status="single_language_evidence", year=2020):
    return {"qid":qid,"title":title,"year":year,"language":language,
            "property":property,"status":status,
            "source_only":True,"officially_verified":False,
            "source_url":"https://www.wikidata.org/wiki/"+qid}


def checkpoint(**records):
    return {"schema":"india-film-language-evidence-v1","records":records}


class FoundationLanguageReviewTests(unittest.TestCase):
    def test_proposes_only_exact_qid_title_year_original_language(self):
        r=build([movie()],[],[],checkpoint(Q55=evidence()))
        self.assertEqual(r["counts"]["review_proposals"],1)
        item=r["proposals"][0]
        self.assertEqual(item["proposed_language"],"Telugu")
        self.assertEqual(item["status"],"REVIEW_REQUIRED")
        self.assertEqual(r["d1_writes"],0)
        self.assertEqual(r["automatic_corrections"],0)

    def test_title_or_year_mismatch_is_held(self):
        for mismatch,source in (
            ("title",evidence(title="Another Film")),
            ("year",evidence(year=2019)),
        ):
            with self.subTest(mismatch=mismatch):
                r=build([movie()],[],[],checkpoint(Q55=source))
                self.assertEqual(r["counts"]["review_proposals"],0)
                self.assertEqual(r["counts"]["held_evidence_rows"],1)

    def test_general_language_p407_and_ambiguity_do_not_pass(self):
        for v in (evidence(property="P407"),evidence(status="ambiguous_multilingual_or_conflicting")):
            r=build([movie()],[],[],checkpoint(Q55=v))
            self.assertEqual(r["counts"]["review_proposals"],0)

    def test_existing_language_never_overwritten(self):
        r=build([movie(language="Hindi")],[],[],checkpoint(Q55=evidence()))
        self.assertEqual(r["counts"]["review_proposals"],0)
        self.assertEqual(r["counts"]["films_with_known_language"],1)

    def test_exact_date_film_prevents_second_proposal_for_same_year_only_record(self):
        cat=[{"id":"ct-Q55","wikidata_qid":"Q55","title":"Test Film",
              "language_name":"Unknown","country_code":"IN","release_year":2020}]
        r=build([movie()],cat,[],checkpoint(Q55=evidence()))
        self.assertEqual(r["counts"]["overlapping_film_table_records_excluded"],1)
        self.assertEqual(r["counts"]["review_proposals"],1)
        self.assertEqual(r["proposals"][0]["source_table"],"movies")

    def test_series_stay_out_of_film_evidence_and_are_counted_separately(self):
        series=[{"id":"s1","wikidata_qid":"Q55","language_name":"Unknown"}]
        r=build([movie()],[],series,checkpoint(Q55=evidence()))
        self.assertEqual(r["counts"]["series_unknown_language"],1)
        self.assertEqual(r["counts"]["review_proposals"],1)
        self.assertTrue(all(x["source_table"]!="series_titles" for x in r["proposals"]))

    def test_unknown_or_unmatched_records_do_not_invent_language(self):
        r=build([movie("Q56")],[],[],checkpoint(Q55=evidence()))
        self.assertEqual(r["counts"]["indian_unknown_films_without_checkpoint_evidence"],1)
        self.assertEqual(r["counts"]["review_proposals"],0)

    def test_source_provenance_and_checkpoint_schema_are_mandatory(self):
        item=evidence();item["source_url"]="https://elsewhere.example/Q55"
        r=build([movie()],[],[],checkpoint(Q55=item))
        self.assertEqual(r["counts"]["review_proposals"],0)
        with self.assertRaises(ValueError):
            build([movie()],[],[],{"schema":"wrong","records":{}})


if __name__=="__main__":
    unittest.main()
