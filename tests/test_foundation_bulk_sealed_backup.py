"""Full-bulk AES recovery: no secrets in logs, no unsourced production update."""
import base64
import json
import unittest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from scripts.foundation_bulk_sealed_backup import (
    check_key,checked_manifest,collect_matches,make_capsule,AAD,
)


def fixture():
    films={"schema":"foundation-v2-bulk-existing-films-v1",
           "frozen_catalogue_movies":51872,
           "correction_candidates":1000,"writes_authorized":False,
           "d1_writes":0,"records":[],"records_sha256":"test-film"}
    series={"schema":"foundation-v2-bulk-existing-series-v1",
            "total_existing_series":18303,
            "language_candidates":1000,"writes_authorized":False,
            "d1_writes":0,"records":[],"records_sha256":"test-series"}
    existing_films={}
    existing_series={}
    for n in range(1000):
        qid="Q"+str(n+1000000)
        films["records"].append({
            "source_table":"catalogue_titles","source_id":"wd-"+qid,
            "wikidata_qid":qid,"title":"Film "+str(n),
            "year":2000,"proposed_language":"Tamil","source_url":"https://www.wikidata.org/wiki/"+qid,
            "claim_property":"P364","review_status":"SOURCE_MATCH_ONLY_NOT_PRODUCTION_APPROVED"})
        existing_films[qid]={"id":"wd-"+qid,"wikidata_qid":qid,
            "title":"Film "+str(n),"release_year":2000,
            "language_name":"Unknown","country_code":"IN",
            "language_source":None,"language_source_url":None,
            "created_at":"2026-01-01"}
        sqid="Q"+str(n+2000000)
        series["records"].append({
            "id":"series-wd-"+sqid,"wikidata_qid":sqid,
            "title":"Show "+str(n),"first_air_year":2009,
            "proposed_language":"Telugu","source":"wikidata:P364",
            "source_url":"https://www.wikidata.org/wiki/"+sqid,
            "review_status":"SOURCE_P364_ONLY_NOT_APPROVED"})
        existing_series[sqid]={"id":"series-wd-"+sqid,
            "wikidata_qid":sqid,"title":"Show "+str(n),"first_air_year":2009,
            "language_name":"Unknown","language_source":None,
            "language_source_url":None,"updated_at":"2026-01-01"}
    return films,series,existing_films,existing_series


class FullBulkBackupTests(unittest.TestCase):
    def test_chat_disclosed_key_and_missing_key_are_rejected(self):
        unsafe="fx0rj90g7+YrEHwqPeRpidHOHdqivglz/4eioE4W0uw="
        for item in (unsafe,"",base64.b64encode(b"too short").decode(),"%%"):
            with self.subTest(item=item[:4]),self.assertRaises(ValueError):
                check_key(item)

    def test_valid_owner_key_encrypted_round_trip_exact_full_rows(self):
        films,series,f,s=fixture()
        key=check_key(base64.b64encode(bytes(range(32))).decode())
        result,backup=make_capsule(films,series,f,s,key=key,bookmark="testbook",
                                    bookmark_status="captured_read_only")
        self.assertEqual(result["total_source_candidates"],2000)
        self.assertEqual(result["full_production_rows_backed_up"],2000)
        self.assertEqual(result["held_on_fresh_live_check"],0)
        self.assertFalse(result["writes_authorized"])
        self.assertEqual(result["production_writes"],0)
        self.assertNotIn("testbook",json.dumps(result))
        self.assertNotIn("testbook",json.dumps(backup))
        data=AESGCM(key).decrypt(base64.b64decode(backup["nonce_base64"]),
                                  base64.b64decode(backup["ciphertext_base64"]),AAD)
        plain=json.loads(data)
        self.assertEqual(len(plain["full_rows"]),2000)
        self.assertEqual(plain["bookmark"],"testbook")
        self.assertIn("created_at",plain["full_rows"][0]["row"])
        self.assertFalse(plain["ready_to_apply"])

    def test_fresh_drift_is_held_not_merged_into_backup(self):
        film,show,current_f,current_s=fixture()
        key=bytes(range(32))
        current_f["Q1000000"]["release_year"]=1988
        current_s.pop("Q2000000")
        summary,backup=make_capsule(film,show,current_f,current_s,key=key,
                                      bookmark=None,bookmark_status="unavailable")
        self.assertEqual(summary["full_production_rows_backed_up"],1998)
        self.assertEqual(summary["held_on_fresh_live_check"],2)
        self.assertEqual(summary["issue_counts"]["film_release_year_or_country_changed"],1)
        self.assertEqual(summary["issue_counts"]["missing_current_or_known_language"],1)
        self.assertFalse(summary["writes_authorized"])

    def test_source_provenance_and_held_qids_rejected(self):
        film,show,f,s=fixture()
        film["records"][0]["wikidata_qid"]="Q20967570"
        with self.assertRaises(ValueError):
            checked_manifest(film,show)
        film,show,f,s=fixture()
        show["records"][1]["source"]="wikidata:P407"
        with self.assertRaises(ValueError):
            checked_manifest(film,show)

    def test_provenance_or_known_language_change_held(self):
        film,show,f,s=fixture()
        f["Q1000000"]["language_name"]="Hindi"
        s["Q2000000"]["language_source"]="third-party"
        records,held=collect_matches(*checked_manifest(film,show),f,s)
        self.assertEqual(len(records),1998)
        self.assertEqual(len(held),2)


if __name__=="__main__":
    unittest.main()
