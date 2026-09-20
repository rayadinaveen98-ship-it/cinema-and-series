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
        self.assertEqual(
            status.guard_state(self.row_payload([])),
            {"state": "available", "row": None},
        )

    def test_daily_guard_single_row_is_used(self):
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
        self.assertEqual(result["row"]["workflow_run_id"], "123:cleanup")


if __name__ == "__main__":
    unittest.main()
