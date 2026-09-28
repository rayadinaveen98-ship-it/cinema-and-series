import unittest

from scripts import p1_status_snapshot as status


class P1StatusSnapshotTests(unittest.TestCase):
    def row_payload(self, rows):
        return [{"results": rows}]

    def state_map(self, completed=(), unsafe=None):
        completed = set(completed)
        result = {}
        for op in status.OPERATION_ORDER:
            state = "complete" if op in completed else "not_started"
            if unsafe == op:
                state = "unsafe_partial"
            result[op] = {
                "state": state,
                "projection_sha256": status.EXPECTED_PROJECTION_SHA256,
                "expected": {},
                "current": {},
            }
        return result

    def clean_counts(self):
        return {
            **status.EXPECTED_TARGET,
            "orphan_title_genres_title": 0,
            "orphan_title_genres_genre": 0,
            "orphan_title_credits_title": 0,
            "orphan_title_credits_person": 0,
            "invalid_provenance": 0,
        }

    def available_guard(self):
        return {"state": "available", "row": None, "violations": []}

    def test_cleanup_complete_exact_state(self):
        movies = self.row_payload([])
        catalogue = self.row_payload([])
        series = self.row_payload([
            {"id": "series-wd-Q3146368", "wikidata_qid": "Q3146368"}
        ])
        self.assertEqual(status.cleanup_state(movies, catalogue, series), "complete")

    def test_cleanup_needed_exact_pre_state(self):
        movies = self.row_payload([
            {"id": "wd-Q3049630", "wikidata_qid": "Q3049630"}
        ])
        catalogue = self.row_payload([
            {"id": "wd-Q3146368", "wikidata_qid": "Q3146368"}
        ])
        series = self.row_payload([
            {"id": "series-wd-Q3049630", "wikidata_qid": "Q3049630"},
            {"id": "series-wd-Q3146368", "wikidata_qid": "Q3146368"},
        ])
        self.assertEqual(status.cleanup_state(movies, catalogue, series), "needed")

    def test_cleanup_unknown_shape_is_unsafe(self):
        movies = self.row_payload([
            {"id": "unexpected", "wikidata_qid": "Q3049630"}
        ])
        self.assertEqual(
            status.cleanup_state(movies, self.row_payload([]), self.row_payload([])),
            "unsafe",
        )

    def test_next_operation_is_first_gap_after_complete_prefix(self):
        states = self.state_map(completed=["topup", "1", "2"])
        self.assertEqual(status.plan_next_operation(states), ("in_progress", "3"))

    def test_later_complete_operation_after_gap_is_unsafe(self):
        states = self.state_map(completed=["topup", "2"])
        self.assertEqual(status.plan_next_operation(states), ("unsafe_out_of_order", "1"))

    def test_partial_operation_is_unsafe(self):
        states = self.state_map(completed=["topup", "1"], unsafe="2")
        self.assertEqual(status.plan_next_operation(states), ("unsafe", "2"))

    def test_all_operations_complete(self):
        states = self.state_map(completed=status.OPERATION_ORDER)
        self.assertEqual(
            status.plan_next_operation(states),
            ("operations_complete", "complete"),
        )

    def test_daily_guard_empty_is_available(self):
        self.assertEqual(status.guard_state(self.row_payload([])), self.available_guard())

    def test_daily_guard_single_valid_row_is_used(self):
        result = status.guard_state(self.row_payload([
            {
                "utc_date": "2026-09-20",
                "shard_index": 0,
                "projection_sha256": status.EXPECTED_PROJECTION_SHA256,
                "workflow_run_id": "123:cleanup",
                "created_at": "2026-09-20 05:01:00",
            }
        ]))
        self.assertEqual(result["state"], "used")
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["row"]["workflow_run_id"], "123:cleanup")

    def test_daily_guard_wrong_projection_is_unsafe(self):
        result = status.guard_state(self.row_payload([
            {
                "utc_date": "2026-09-28",
                "shard_index": 7,
                "projection_sha256": "wrong",
                "workflow_run_id": "123:7",
                "created_at": "2026-09-28 05:00:00",
            }
        ]))
        self.assertEqual(result["state"], "unsafe")
        self.assertIn("projection_sha256", result["violations"])

    def test_daily_guard_blank_owner_is_unsafe(self):
        result = status.guard_state(self.row_payload([
            {
                "utc_date": "2026-09-28",
                "shard_index": 7,
                "projection_sha256": status.EXPECTED_PROJECTION_SHA256,
                "workflow_run_id": "",
                "created_at": "2026-09-28 05:00:00",
            }
        ]))
        self.assertEqual(result["state"], "unsafe")
        self.assertIn("workflow_run_id", result["violations"])

    def test_daily_guard_invalid_shard_index_is_unsafe(self):
        result = status.guard_state(self.row_payload([
            {
                "utc_date": "2026-09-28",
                "shard_index": 9,
                "projection_sha256": status.EXPECTED_PROJECTION_SHA256,
                "workflow_run_id": "123:9",
                "created_at": "2026-09-28 05:00:00",
            }
        ]))
        self.assertEqual(result["state"], "unsafe")
        self.assertIn("shard_index", result["violations"])

    def test_final_verification_eligibility_is_not_completion(self):
        eligible = status.is_final_verification_eligible(
            cleanup="complete",
            overall_state="operations_complete",
            counts=self.clean_counts(),
            health_violations={},
            guard=self.available_guard(),
        )
        self.assertTrue(eligible)

        snapshot = {
            "daily_quota_guard": self.available_guard(),
            "next_operation": "complete",
            "next_operation_estimated_rows_written": None,
            "production_counts": self.clean_counts(),
            "source_cleanup_state": "complete",
            "overall_operation_state": "operations_complete",
            "completed_operation_count": 15,
            "total_operation_count": 15,
            "exit_gate_state": "ready_for_final_verification",
            "final_verification_eligible": True,
            "operation_states": {op: {"state": "complete"} for op in status.OPERATION_ORDER},
            "operation_costs": {op: 1 for op in status.OPERATION_ORDER},
            "health_violations": {},
        }
        rendered = status.render_markdown(snapshot)
        self.assertIn("final verification eligible: **yes**", rendered.lower())
        self.assertIn("P1 complete: **not determined by this snapshot**", rendered)
        self.assertIn("S0=0/S1=0", rendered)

    def test_final_verification_eligibility_fails_on_target_count_mismatch(self):
        counts = self.clean_counts()
        counts["recommendation_titles"] -= 1
        self.assertFalse(status.is_final_verification_eligible(
            cleanup="complete",
            overall_state="operations_complete",
            counts=counts,
            health_violations={},
            guard=self.available_guard(),
        ))

    def test_final_verification_eligibility_fails_on_unsafe_guard(self):
        self.assertFalse(status.is_final_verification_eligible(
            cleanup="complete",
            overall_state="operations_complete",
            counts=self.clean_counts(),
            health_violations={},
            guard={"state": "unsafe", "row": {}, "violations": ["projection_sha256"]},
        ))

    def test_final_verification_eligibility_fails_on_health_violation(self):
        self.assertFalse(status.is_final_verification_eligible(
            cleanup="complete",
            overall_state="operations_complete",
            counts=self.clean_counts(),
            health_violations={"invalid_provenance": 1},
            guard=self.available_guard(),
        ))


if __name__ == "__main__":
    unittest.main()
