"""Offline tests for the scheduled Indian film autopilot and recovery gates."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from india_daily_autopilot import (
    D1QuotaReached, bootstrap, d1_execute, eligible_queue_items,
    initial_state, merge_source, run, safe_queue_selection, source_step
)


def item(qid, year=1988, title=None, cat=True):
    return {
        "wikidata_qid": qid, "page_id": int(qid[1:]) + 100,
        "title": title or f"Example Film {qid}", "year": year,
        "observed_years": [year], "observed_languages": ["Telugu"],
        "source_categories": [f"Category:{year} Indian films"] if cat else
                             [f"Category:{year} Telugu-language films"],
        "india_category": cat,
    }


class DailyAutopilotTests(unittest.TestCase):
    def test_initial_target_does_not_claim_unverified_2000s(self):
        state = initial_state()
        self.assertEqual(state["goal_additional_indian_films"], 10000)
        self.assertEqual(state["previously_confirmed"], 1552)
        self.assertEqual(state["2000s_import_present"], 0)
        self.assertFalse(state["attempted_by_autopilot"])

    def test_persists_qid_evidence_but_excludes_conflicting_years(self):
        queue = {}
        merge_source(queue, item("Q12", 1988))
        merge_source(queue, item("Q12", 1989))
        merge_source(queue, item("Q13", 1988))
        merge_source(queue, item("Q14", 1988, cat=False))
        self.assertEqual(len(queue), 3)
        self.assertEqual([x["wikidata_qid"] for x in eligible_queue_items(queue)], ["Q13"])

    def test_bootstrap_preserves_exact_2000s_import_identifiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "years.json", root / "history.json"
            a.write_text(json.dumps({
                "schema_version": "india-movie-discovery-audit-v1",
                "candidates": [{**item("Q21", 2001),
                                "classification": "new_indian_category_candidates"},
                               {**item("Q22", 2001, cat=False),
                                "classification": "new_language_only_candidates"}],
            }))
            b.write_text(json.dumps({
                "schema_version": "indian-historical-source-merge-v1",
                "candidates": [item("Q23", 1987)],
            }))
            state = initial_state()
            bootstrap(state, a, b)
            self.assertEqual(state["2000s_seed_qids"], ["Q21"])
            self.assertEqual(len(state["queue"]), 3)
            # A repeated execution keeps one copy of each QID.
            bootstrap(state, None, None)
            self.assertEqual(len(state["queue"]), 3)

    def test_scan_resume_position_survives_rate_limit(self):
        state = initial_state()
        state["scan"]["decade_index"] = 0
        state["scan"]["offset"] = 0
        with patch("india_daily_autopilot.discover", return_value=(
            [item("Q25", 1969)],
            {"halt_reason": "wikipedia_rate_limit", "next_category_offset": 5,
             "categories_failed": 1},
        )):
            result = source_step(state)
        self.assertEqual(result["status"], "wikipedia_rate_limit")
        self.assertEqual(state["scan"]["offset"], 5)
        self.assertEqual(len(state["queue"]), 1)

    def test_existing_movie_and_series_are_not_imported(self):
        state = initial_state()
        for qid in ("Q50", "Q51", "Q52"):
            merge_source(state["queue"], item(qid, 1985))
        exact = []
        year = [{"id": "wd-Q50", "wikidata_qid": "Q50",
                 "wikipedia_page_id": 150, "title": "Example Film Q50",
                 "release_year": 1985}]
        series = [{"wikidata_qid": "Q51"}]
        selection = safe_queue_selection(state, exact, year, series, 100)
        self.assertEqual([x["wikidata_qid"] for x in selection], ["Q52"])

    def test_7500_d1_quota_stops_and_does_not_retry(self):
        failed = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="",
            stderr="Your account has exceeded D1's free tier daily row read limit. [code: 7500]",
        )
        with patch("india_daily_autopilot.subprocess.run", return_value=failed) as sub:
            with self.assertRaises(D1QuotaReached):
                d1_execute(sql="SELECT COUNT(*) FROM catalogue_titles")
        self.assertEqual(sub.call_count, 1)

    def test_source_only_never_touches_d1(self):
        state = initial_state()
        merge_source(state["queue"], item("Q90"))
        with tempfile.TemporaryDirectory() as tmp, \
             patch("india_daily_autopilot.d1_execute") as d1:
            result = run(state, Path(tmp), 100, 100000, no_db=True,
                         discover_enabled=False)
        self.assertEqual(result["production"]["status"], "source_only")
        d1.assert_not_called()


if __name__ == "__main__":
    unittest.main()
