"""New growth goal uses genuinely new exact-year Wikipedia category identities."""
import tempfile
import unittest
from pathlib import Path
from scripts.oct20_existing_queue_import import choose, apply
from scripts.india_daily_autopilot import D1QuotaReached


def film(qid, year=2026, name=None):
    return {
        "wikidata_qid": qid, "page_id": int(qid[1:]) + 1000,
        "title": name or ("Example " + qid), "observed_years": [year], "year": year,
        "source_categories": [f"Category:{year} Indian films"],
        "observed_languages": ["Telugu"],
        "india_category": True,
    }


class NewCategoryProductionImportTests(unittest.TestCase):
    def test_new_qids_selected_beyond_old_10k_goal_and_collisions_are_held(self):
        queue = {x["wikidata_qid"]: x for x in [
            film("Q101"), film("Q102"), film("Q103"), film("Q104")
        ]}
        state = {"schema_version":1, "queue":queue, "goal_additional_indian_films":10000}
        exact=[{"wikidata_qid":"Q101","title":"Example Q101","release_date":"2026-05-01"}]
        year=[{"wikidata_qid":"Q102","title":"Example Q102","release_year":2026}]
        series=[{"wikidata_qid":"Q103","title":"Example Q103","first_air_year":2026}]
        rows, info=choose(state,exact,year,series,500)
        self.assertEqual([r["wikidata_qid"] for r in rows],["Q104"])
        self.assertEqual(info["selected_count"],1)

    def test_fresh_year_title_collision_rejected(self):
        state = {"schema_version":1,"queue":{"Q200":film("Q200",name="Same Film")}}
        year = [{"wikidata_qid":"Q99","title":"Same Film","release_year":2026}]
        out, report=choose(state,[],year,[],100)
        self.assertEqual(out,[])
        self.assertEqual(report["selected_count"],0)

    def test_apply_verifies_qids_and_stops_on_quota(self):
        values=[film("Q3"),film("Q4")]
        seen=[]
        def execute(*,sql_file):
            raw=Path(sql_file).read_text()
            self.assertEqual(raw.count("INSERT OR IGNORE INTO catalogue_titles"),2)
            seen.append(raw)
            return "ok",170
        def present(ids):
            return set(ids)
        with tempfile.TemporaryDirectory() as temp:
            result=apply(values,Path(temp),[],execute=execute,present=present)
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["verified_net_new_qids"],2)
        self.assertEqual(result["submitted_to_d1"],2)
        self.assertEqual(result["rows_read_reported_by_sql_batches"],170)
        self.assertEqual(len(seen),1)
        def quota(*,sql_file):
            raise D1QuotaReached("Cloudflare 7500 limit")
        with tempfile.TemporaryDirectory() as temp:
            blocked=apply(values,Path(temp),[],execute=quota,present=present)
        self.assertEqual(blocked["status"],"cloudflare_quota_paused")
        self.assertEqual(blocked["verified_net_new_qids"],0)

    def test_import_is_insert_only_and_year_unconfirmed(self):
        with tempfile.TemporaryDirectory() as temp:
            apply([film("Q44")],Path(temp),[],execute=lambda **kw: ("ok",2),
                  present=lambda q:set(q))
            sql=(Path(temp)/"india-new-000.sql").read_text()
        self.assertIn("INSERT OR IGNORE INTO catalogue_titles",sql)
        self.assertIn("'unconfirmed'",sql)
        self.assertIn("'year'",sql)
        self.assertNotIn("DELETE FROM",sql)
        self.assertNotIn("UPDATE catalogue_titles",sql)

    def test_invalid_state_or_limits_fail_closed(self):
        with self.assertRaises(ValueError):
            choose({"schema_version":1,"queue":[]},[],[],[],100)
        with self.assertRaises(ValueError):
            choose({"schema_version":1,"queue":{}},[],[],[],5001)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                apply([],Path(temp),[],row_read_budget=5)


if __name__=="__main__":
    unittest.main()
