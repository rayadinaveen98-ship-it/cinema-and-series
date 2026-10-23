"""Batch QA must use actual schema, preserve full rows and abort on drift."""
import copy
import unittest

from scripts.foundation_bulk_correction_rehearsal import (
    validate_snapshot, simulate, guard_statement, SCHEMA
)


def original(table,idx,language="Unknown"):
    qid=f"Q{1000000+idx}" if table=="catalogue_titles" else f"Q{2000000+idx}"
    row={
        "id":f"wd-{qid}","wikidata_qid":qid,
        "title":f"Example {idx}",
        "language_name":language,
        "country_code":"IN",
        "source_category":"test-recovery",
        "source_url":f"https://www.wikidata.org/wiki/{qid}",
        "language_source":None,"language_source_url":None,
        "created_at":"2026-01-05 04:00:00",
        "updated_at":"2026-01-05 04:00:00",
    }
    if table=="catalogue_titles":
        row.update(release_year=2018,date_precision="year",verification_status="unconfirmed")
    else:
        row.update(first_air_year=2018,series_kind="series",
                   verification_status="unconfirmed")
    return {
        "table":table,"qid":qid,"row":row,
        "proposed_language":"Telugu",
        "evidence_url":f"https://www.wikidata.org/wiki/{qid}"
    }


def fixture():
    return {
        "schema":"foundation-v2-full-row-recovery-v1",
        "production_database":"cinema-and-series",
        "ready_to_apply":False,"production_writes":0,
        "drift_issues":[],
        "full_rows":[original("catalogue_titles",i) for i in range(3)]+
                    [original("series_titles",i+10) for i in range(2)],
    }


class BulkBatchRehearsalTests(unittest.TestCase):
    def test_full_forward_exact_inverse_and_competing_write(self):
        data=fixture()
        items=validate_snapshot(data,expected_count=5)
        result=simulate(items,batch_size=2)
        self.assertEqual(result["archive_full_rows"],5)
        self.assertEqual(result["proposed_operations"],3)
        self.assertEqual(result["maximum_batch_size"],2)
        self.assertTrue(result["all_full_original_rows_restored_exactly"])
        self.assertTrue(result["stale_forward_aborts_without_partial_writes"])
        self.assertTrue(result["competing_edit_blocks_inverse"])
        self.assertTrue(result["unrelated_control_rows_preserved"])
        self.assertEqual(result["production_writes"],0)
        self.assertFalse(result["production_update_approved"])
        self.assertFalse(result["production_sql_generated"])
        self.assertEqual(result["schema"],SCHEMA)

    def test_unsupported_or_known_provenance_rejected(self):
        data=fixture()
        data["full_rows"][0]["row"]["language_name"]="Hindi"
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)
        data=fixture()
        data["full_rows"][0]["row"]["language_source"]="other"
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)
        data=fixture()
        data["full_rows"][0]["evidence_url"]="https://www.wikipedia.org/"
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)

    def test_duplicate_or_disputed_film_rejected(self):
        data=fixture()
        data["full_rows"][1]=copy.deepcopy(data["full_rows"][0])
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)
        data=fixture()
        data["full_rows"][0]["row"]["wikidata_qid"]="Q20649744"
        data["full_rows"][0]["qid"]="Q20649744"
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)

    def test_archive_approval_flag_and_partial_rows_rejected(self):
        data=fixture()
        data["ready_to_apply"]=True
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)
        data=fixture()
        del data["full_rows"][0]["row"]["title"]
        with self.assertRaises(ValueError):
            validate_snapshot(data,expected_count=5)
        data=fixture()
        with self.assertRaises(ValueError):
            simulate(validate_snapshot(data,expected_count=5),batch_size=101)

    def test_full_precondition_verifies_every_original_column(self):
        item=fixture()["full_rows"][0]
        sql,values=guard_statement(item,False)
        self.assertIn("updated_at IS ?",sql)
        self.assertIn("verification_status IS ?",sql)
        self.assertEqual(len(values),len(item["row"]))


if __name__=="__main__":
    unittest.main()
