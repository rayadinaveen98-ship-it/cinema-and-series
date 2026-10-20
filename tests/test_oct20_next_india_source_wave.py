"""Resume India-category years without duplicating titles or skipping failures."""
import unittest

from scripts.india_daily_autopilot import initial_state
from scripts.oct20_next_india_source_wave import gather_new_years


class Oct20NextIndiaWaveTests(unittest.TestCase):
    def test_source_only_scan_writes_no_title_updates(self):
        state=initial_state()
        seen=[]
        def mock_scan(s):
            seen.append(1)
            qid="Q"+str(1000+len(seen))
            s["queue"][qid]={
                "wikidata_qid":qid,"title":"Film "+qid,"page_id":10000+len(seen),
                "observed_years":[2026],"source_categories":["Category:2026 Indian films"],
                "observed_languages":["Telugu"],"india_category":True
            }
            return {"status":"category_batch_complete","new_source_qids":1,"failed_categories":0}
        report=gather_new_years(state,3,mock_scan)
        self.assertEqual(report["new_source_qids"],3)
        self.assertEqual(report["eligible_category_items_after"],3)
        self.assertEqual(report["production_titles_added"],0)
        self.assertTrue(report["read_only_source_discovery"])
        self.assertEqual(len(seen),3)

    def test_stop_on_wikimedia_rate_limit_without_skipping_cursor(self):
        state=initial_state()
        def mock_scan(s):
            return {"status":"wikipedia_rate_limit","wikipedia_rate_limited":True,
                    "new_source_qids":0,"failed_categories":1}
        report=gather_new_years(state,8,mock_scan)
        self.assertEqual(report["wave_count"],1)

    def test_transient_category_error_rewinds_cursor(self):
        state=initial_state()
        original=dict(state["scan"])
        def mock_scan(s):
            s["scan"]["offset"]=42
            return {"status":"category_batch_complete","new_source_qids":0,
                    "failed_categories":1,"wikipedia_rate_limited":False}
        report=gather_new_years(state,8,mock_scan)
        self.assertEqual(report["wave_count"],1)
        self.assertEqual(state["scan"],original)

    def test_bad_checkpoint_and_oversize_requests_fail_closed(self):
        with self.assertRaises(ValueError):
            gather_new_years({},1,lambda s:{})
        with self.assertRaises(ValueError):
            gather_new_years(initial_state(),9,lambda s:{})
        with self.assertRaises(ValueError):
            gather_new_years(initial_state(),0,lambda s:{})


if __name__=="__main__":
    unittest.main()
