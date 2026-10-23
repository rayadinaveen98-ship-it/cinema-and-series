"""QID-bounded D1 read queries must never allow arbitrary SQL or writes."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.foundation_bulk_qid_selects import create_queries,combine_sql_results
from tests.test_foundation_bulk_sealed_backup import fixture


class BulkReadOnlyChunksTests(unittest.TestCase):
    def test_exact_2000_source_qids_bounded_and_reassembled(self):
        films,series,rows_f,rows_s=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            plan=create_queries(films,series,root/"queries",size=400)
            self.assertEqual(plan["total_candidates"],2000)
            for table in ("catalogue_titles","series_titles"):
                batches=plan["tables"][table]["queries"]
                self.assertEqual(len(batches),3)
                for index,file in enumerate(batches):
                    sql=(root/"queries"/file).read_text()
                    self.assertTrue(sql.startswith("SELECT * FROM "+table+" WHERE wikidata_qid IN ("))
                    self.assertNotIn("UPDATE",sql)
                    self.assertNotIn("DELETE",sql)
                    raw=(rows_f if table=="catalogue_titles" else rows_s)
                    qids=[r for r in raw.values() if "'"+r["wikidata_qid"]+"'" in sql]
                    target=root/"private-reads"/(table+"-"+str(index).zfill(3)+".json")
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text(json.dumps([{"success":True,"results":qids}]))
                dest=root/(table+"-snapshot.json")
                combine_sql_results(root,table,dest)
                result=json.loads(dest.read_text())
                self.assertEqual(len(result[0]["results"]),1000)

    def test_reject_unsafe_chunk_or_overlapping_current_qids(self):
        f,s,rows_f,_=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):
                create_queries(f,s,root/"queries",size=1000)
            create_queries(f,s,root/"queries",size=400)
            folder=root/"private-reads"
            folder.mkdir()
            for i in range(3):
                row=copy.deepcopy(next(iter(rows_f.values())))
                (folder/("catalogue_titles-"+str(i).zfill(3)+".json")).write_text(
                    json.dumps([{"success":True,"results":[row]}]))
            with self.assertRaisesRegex(ValueError,"duplicate"):
                combine_sql_results(root,"catalogue_titles",root/"combined.json")
            with self.assertRaises(ValueError):
                combine_sql_results(root,"movies",root/"combined.json")


if __name__=="__main__":
    unittest.main()
