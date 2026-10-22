"""Final approval readiness must not leak backups or approve any D1 write."""
import base64
import copy
import json
import unittest
from tests.test_foundation_filebacked_rollback import fixtures
from scripts.foundation_final_prewrite import guarded_select, make_report


def material():
    packet, review, raw = fixtures()
    # Mimic SELECT * rather than selected sparse columns.
    for row in raw[0]["results"]:
        row.update({
            "language_source": None, "language_source_url": None,
            "source_category": "external-source", "source_url":
            "https://www.wikidata.org/wiki/" + row["wikidata_qid"]
        })
    return packet, review, raw


class FinalApprovalReadOnlyTests(unittest.TestCase):
    def test_query_contains_only_20_exact_qids_without_write_verb(self):
        packet, _, _ = material()
        sql = guarded_select(packet)
        self.assertEqual(sql.count("'Q"), 20)
        self.assertTrue(sql.startswith("SELECT * FROM catalogue_titles WHERE"))
        for unsafe in ("UPDATE", "DELETE", "INSERT", "DROP", "ALTER", "--remote"):
            self.assertNotIn(unsafe, sql)

    def test_no_backup_key_never_publishes_raw_rows(self):
        packet, review, raw = material()
        report, sealed = make_report(packet, review, raw, None, "unavailable", None)
        self.assertIsNone(sealed)
        self.assertEqual(report["saved_full_column_rows"], 0)
        self.assertFalse(report["write_approved"])
        self.assertFalse(report["ready_to_write"])
        self.assertEqual(report["reviewed_candidates"], 17)
        self.assertEqual(report["held_disputed_films"], 3)
        self.assertNotIn("source_category", json.dumps(report))
        self.assertEqual(report["production_writes"], 0)

    def test_aes_gcm_encrypted_backup_authenticates_20_full_rows(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        packet, review, raw = material()
        key = bytes(range(32))
        report, sealed = make_report(packet, review, raw, "bookmarked-state-v1",
                                     "captured_read_only", base64.b64encode(key).decode())
        self.assertTrue(report["backup_sealed_and_uploaded_by_workflow"])
        self.assertIsNotNone(sealed)
        self.assertEqual(sealed["row_count"], 20)
        aad = b"cinema-and-series/data-foundation-v2/recovery-only"
        opened = AESGCM(key).decrypt(
            base64.b64decode(sealed["nonce_base64"]),
            base64.b64decode(sealed["ciphertext_base64"]), aad)
        restored = json.loads(opened)
        self.assertEqual(len(restored["rows"]), 20)
        self.assertEqual(restored["bookmark"], "bookmarked-state-v1")
        self.assertNotIn("bookmarked-state-v1", json.dumps(report))
        self.assertNotIn("bookmarked-state-v1", json.dumps(sealed))
        self.assertFalse(report["ready_to_write"])

    def test_one_byte_ciphertext_tampering_is_rejected(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        packet, review, raw = material()
        key = bytes(range(32))
        _, sealed = make_report(packet, review, raw, "bookmark", "captured_read_only",
                                base64.b64encode(key).decode())
        ciphertext = bytearray(base64.b64decode(sealed["ciphertext_base64"]))
        ciphertext[-1] ^= 1
        with self.assertRaises(Exception):
            AESGCM(key).decrypt(base64.b64decode(sealed["nonce_base64"]),
                                bytes(ciphertext),
                                b"cinema-and-series/data-foundation-v2/recovery-only")

    def test_current_value_drift_is_a_hard_failure(self):
        packet, review, raw = material()
        raw[0]["results"][6]["release_year"] += 1
        with self.assertRaises(ValueError):
            make_report(packet, review, raw, None, "unavailable", None)

    def test_invalid_key_or_partial_rows_never_seal(self):
        packet, review, raw = material()
        with self.assertRaises(ValueError):
            make_report(packet, review, raw, None, "unavailable",
                        base64.b64encode(b"x"*16).decode())
        for row in raw[0]["results"]:
            row.pop("language_source")
            row.pop("language_source_url")
            row.pop("source_category")
            row.pop("source_url")
        with self.assertRaisesRegex(ValueError,"full-column"):
            make_report(packet, review, raw, None, "unavailable", None)


if __name__ == "__main__":
    unittest.main()
