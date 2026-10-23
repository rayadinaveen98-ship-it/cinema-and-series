"""Source-only 18k-series four-way P364 reconciliation invariants."""
import copy
import unittest
from scripts.foundation_bulk_series_summary import combine


def fixtures():
    rows=[
        {"id":f"s-{n}","wikidata_qid":f"Q{n}","title":f"Series {n}",
         "language_name":"Unknown","first_air_year":2000+n}
        for n in range(1,5)
    ]
    rows += [
        {"id":"s-5","wikidata_qid":"Q5","title":"Known","language_name":"Hindi","first_air_year":2005},
        {"id":"s-6","wikidata_qid":None,"title":"Unidentified",
         "language_name":"Unknown","first_air_year":2006},
    ]
    shards=[]
    for i in range(4):
        report={
            "schema_version":"series-language-enrichment-v1","property":"P364",
            "shard_index":i,"shard_count":4,"candidate_count":1,
            "update_count":0,"ambiguous_count":0,"missing_claim_count":0,
            "missing_label_count":0,
            "updates":[],"ambiguous":[],"missing_claim":[],"missing_label":[],
        }
        n={0:4,1:1,2:2,3:3}[i]
        basic={"id":f"s-{n}","wikidata_qid":f"Q{n}","title":f"Series {n}"}
        status={0:"updates",1:"ambiguous",2:"missing_claim",3:"missing_label"}[i]
        if status=="updates":
            report[status].append({
                **basic,"language":"Telugu","language_qid":"Q8097",
                "language_source":"wikidata:P364",
                "language_source_url":f"https://www.wikidata.org/wiki/Q{n}"})
            report["update_count"]=1
        else:
            report[status].append(basic)
            report[status+"_count"]=1
        shards.append(report)
    return rows,shards


class BulkSeriesTests(unittest.TestCase):
    def test_all_unknown_qids_accounted_and_known_never_updated(self):
        rows,shards=fixtures()
        r=combine(rows,shards,baseline=False)
        self.assertEqual(r["total_existing_series"],6)
        self.assertEqual(r["series_unknown_language"],5)
        self.assertEqual(r["source_candidates"],4)
        self.assertEqual(r["series_without_valid_qid"],1)
        self.assertEqual(r["language_candidates"],1)
        self.assertEqual(r["ambiguous_count"],1)
        self.assertEqual(r["missing_claim_count"],1)
        self.assertEqual(r["missing_label_count"],1)
        self.assertEqual(r["records"][0]["wikidata_qid"],"Q4")
        self.assertEqual(r["records"][0]["source_url"],"https://www.wikidata.org/wiki/Q4")
        self.assertEqual(r["d1_reads"],r["d1_writes"])
        self.assertFalse(r["writes_authorized"])

    def test_missing_shard_rejected(self):
        rows,shards=fixtures()
        with self.assertRaises(ValueError):
            combine(rows,shards[:3],baseline=False)

    def test_duplicate_shard_or_ambiguous_report_rejected(self):
        rows,shards=fixtures()
        broken=copy.deepcopy(shards)
        broken[1]["shard_index"]=0
        with self.assertRaises(ValueError):
            combine(rows,broken,baseline=False)
        rows,shards=fixtures()
        shards[0]["updates"][0]["language_source"]="wikipedia:guessed"
        with self.assertRaises(ValueError):
            combine(rows,shards,baseline=False)

    def test_source_identity_and_before_value_must_match(self):
        rows,shards=fixtures()
        rows[3]["language_name"]="Kannada"
        with self.assertRaises(ValueError):
            combine(rows,shards,baseline=False)
        rows,shards=fixtures()
        shards[0]["updates"][0]["title"]="Wrong show"
        with self.assertRaises(ValueError):
            combine(rows,shards,baseline=False)

    def test_baseline_requires_all_series(self):
        rows,shards=fixtures()
        with self.assertRaisesRegex(ValueError,"baseline"):
            combine(rows,shards)


if __name__=="__main__":
    unittest.main()
