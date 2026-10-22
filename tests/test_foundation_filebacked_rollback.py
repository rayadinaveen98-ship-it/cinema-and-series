"""Offline file-backed SQLite backup/recovery proof (production untouched)."""
import copy
import unittest
from scripts.foundation_filebacked_rollback import (
    HELD_QIDS, run_rehearsal, validated_rows,
)


def fixtures():
    qids = sorted(HELD_QIDS) + [f"Q{1000+n}" for n in range(17)]
    packet_items = []
    review_results = []
    current = []
    for index, qid in enumerate(qids):
        old = {
            "table": "catalogue_titles",
            "id": "wd-" + qid,
            "wikidata_qid": qid,
            "title": f"Recorded film {index}",
            "release_year": 1999 + index,
            "country_code": "IN",
            "language_name": "Unknown",
        }
        after = "Telugu"
        packet_items.append({
            "before": old,
            "proposed": {"language_name": after},
            "human_approval": False,
            "source_independent_confirmation": "NOT_YET_OBTAINED",
            "status": "HOLD_PENDING_INDEPENDENT_SOURCE_AND_FRESH_PRODUCTION_PRECONDITION",
        })
        is_held = qid in HELD_QIDS
        review_results.append({
            "qid": qid, "source_id": old["id"],
            "title": old["title"], "year": old["release_year"],
            "proposed_language": after, "current_language": old["language_name"],
            "external_status": "HOLD_YEAR_CONFLICT" if is_held else "SUPPORT",
            "production_status": "CURRENT_PRECONDITIONS_MATCH",
            "status": "HOLD" if is_held else "REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED",
        })
        current.append({k: v for k, v in old.items() if k != "table"})
    packet = {
        "schema": "data-foundation-v2-20-film-dryrun-v1",
        "batch_size": 20,
        "production_writes": 0,
        "ready_for_production_write": False,
        "items": packet_items,
    }
    reviewed = {
        "schema": "data-foundation-v2-reviewed-current-20-v1",
        "preflight_existing_titles": 20, "review_candidates": 17, "held": 3,
        "d1_writes": 0, "production_write_authorized": False,
        "automatically_approved": 0,
        "results": review_results,
    }
    raw = [{"results": current, "success": True, "meta": {"rows_read": 40}}]
    return packet, reviewed, raw


class FoundationFileBackedRollbackTests(unittest.TestCase):
    def test_complete_recovery_rehearsal_on_real_local_files(self):
        result = run_rehearsal(*fixtures())
        self.assertEqual(result["local_simulated_updates"], 17)
        self.assertEqual(result["disputed_held"], 3)
        for key in (
            "full_row_exact_inverse", "sqlite_backup_created_and_verified",
            "sqlite_restore_to_separate_file_verified",
            "held_and_unrelated_rows_unchanged",
            "stale_forward_aborts_atomically", "intervening_edit_blocks_inverse",
        ):
            self.assertTrue(result[key], key)
        self.assertFalse(result["cloudflare_d1_restore_tested"])
        self.assertFalse(result["production_write_authorized"])
        self.assertEqual(result["production_writes"], 0)
        self.assertEqual(result["production_reads_this_run"], 0)

    def test_changed_current_language_refuses_before_updating(self):
        packet, reviewed, raw = fixtures()
        raw[0]["results"][3]["language_name"] = "Malayalam"
        with self.assertRaisesRegex(ValueError, "production row changed"):
            run_rehearsal(packet, reviewed, raw)

    def test_bad_or_duplicate_result_never_enters_sqlite_simulation(self):
        p, r, raw = fixtures()
        raw[0]["results"].append(copy.deepcopy(raw[0]["results"][3]))
        with self.assertRaises(ValueError):
            validated_rows(p, r, raw)
        p, r, raw = fixtures()
        raw[0]["success"] = False
        with self.assertRaises(ValueError):
            validated_rows(p, r, raw)

    def test_disputed_qid_must_not_be_promoted(self):
        p, r, raw = fixtures()
        for row in r["results"]:
            if row["qid"] in HELD_QIDS:
                row["status"] = "REVIEW_CANDIDATE_NOT_WRITE_AUTHORIZED"
                row["external_status"] = "SUPPORT"
                break
        with self.assertRaises(ValueError):
            run_rehearsal(p, r, raw)

    def test_do_not_accept_preapproved_data_or_changed_year(self):
        p, r, raw = fixtures()
        p["items"][0]["human_approval"] = True
        with self.assertRaises(ValueError):
            run_rehearsal(p, r, raw)
        p, r, raw = fixtures()
        raw[0]["results"][0]["release_year"] += 1
        with self.assertRaises(ValueError):
            run_rehearsal(p, r, raw)

    def test_unknown_review_state_is_not_production_authorization(self):
        p, r, raw = fixtures()
        r["production_write_authorized"] = True
        with self.assertRaises(ValueError):
            run_rehearsal(p, r, raw)


if __name__ == "__main__":
    unittest.main()
