"""Fast source-only collection remains bounded, checkpointed, and respectful."""
import tempfile
import unittest
from pathlib import Path

from scripts.accelerate_india_language_source import accelerate


class SourceAcceleratorTests(unittest.TestCase):
    def test_chains_progress_without_touching_d1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); checkpoint=root/"checkpoint.json"; checkpoint.write_text("{}")
            calls=[]
            def fake(stage,check,limit,report,proposals,selection):
                calls.append((limit,selection))
                return {
                    "schema":"india-film-language-evidence-v1",
                    "production_updates":0,"production_d1_access":False,
                    "checked_this_run":min(500, 1250-500*(len(calls)-1)),
                    "pending_qids":max(0,1250-500*len(calls)),
                    "cumulative_checked_qids":min(1250,500*len(calls)),
                    "strict_p364_original_language":min(1250,500*len(calls)),
                    "halted_reason":None,
                }
            report=accelerate(root/"stage.sqlite",checkpoint,root/"report.json",
                              root/"proposals.json",root/"accelerator.json",
                              max_passes=8,run_fn=fake,sleep_fn=lambda _:None)
            self.assertEqual(report["checked_this_run"],1250)
            self.assertEqual(report["passes_completed"],3)
            self.assertEqual(report["remaining_source_qids"],0)
            self.assertEqual(report["d1_reads"],0)
            self.assertEqual(report["d1_writes"],0)
            self.assertTrue(all(n==500 and mode=="decade-balanced" for n,mode in calls))

    def test_honors_upstream_limit_and_preserves_partial_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); checkpoint=root/"checkpoint.json"; checkpoint.write_text("checkpoint")
            count=[0]
            def fake(*args,**kwargs):
                count[0]+=1
                return {
                    "schema":"india-film-language-evidence-v1",
                    "production_updates":0,"production_d1_access":False,
                    "checked_this_run":500 if count[0]==1 else 0,
                    "pending_qids":1000,"cumulative_checked_qids":500,
                    "strict_p364_original_language":400,
                    "halted_reason":"rate_limited" if count[0]==2 else None,
                }
            report=accelerate(root/"stage",checkpoint,root/"report.json",
                              root/"proposals.json",root/"accelerator.json",
                              run_fn=fake,sleep_fn=lambda _:None)
            self.assertEqual(count[0],2)
            self.assertEqual(report["checked_this_run"],500)
            self.assertEqual(report["halted_reason"],"rate_limited")
            self.assertEqual(checkpoint.read_text(),"checkpoint")
            self.assertEqual(report["production_updates"],0)

    def test_rejects_unsafe_limits_or_d1_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); a=(r/"stage",r/"checkpoint",r/"report",r/"proposals",r/"accel")
            for kwargs in ({"max_passes":9},{"per_pass":501},{"max_passes":0}):
                with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                    accelerate(*a,**kwargs)
            def unsafe(*args,**kwargs):
                return {"schema":"india-film-language-evidence-v1",
                        "production_updates":0,"production_d1_access":True}
            with self.assertRaisesRegex(ValueError,"never access D1"):
                accelerate(*a,run_fn=unsafe)


if __name__=="__main__":
    unittest.main()
