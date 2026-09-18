from __future__ import annotations

import unittest

from scripts.p1_shard_status import build_status_query, evaluate_status


FINGERPRINT = "4a9d095ca258d3718d2c189c8bd6596d20af46a434f38ab60ba2f2ddbea18448"


def sample_sql() -> str:
    return f"""-- Projection manifest SHA-256: {FINGERPRINT}
PRAGMA foreign_keys = ON;
BEGIN;
INSERT INTO recommendation_titles (id,wikidata_qid) VALUES ('wikidata:Q1','Q1');
INSERT INTO recommendation_titles (id,wikidata_qid) VALUES ('wikidata:Q2','Q2');
INSERT INTO genres (id) VALUES ('wikidata:Q10');
INSERT INTO people (id) VALUES ('wikidata:Q20');
INSERT OR IGNORE INTO title_genres (title_id) VALUES ('wikidata:Q1');
INSERT OR IGNORE INTO title_genres (title_id) VALUES ('wikidata:Q2');
INSERT OR IGNORE INTO title_credits (title_id) VALUES ('wikidata:Q1');
COMMIT;
"""


def payload(titles: int, title_genres: int, title_credits: int):
    return [{"results": [{"titles": titles, "title_genres": title_genres, "title_credits": title_credits}]}]


class P1ShardStatusTests(unittest.TestCase):
    def test_builds_title_scoped_query_and_expected_counts(self) -> None:
        query, meta = build_status_query(sample_sql(), FINGERPRINT)
        self.assertIn("wikidata:Q1", query)
        self.assertIn("wikidata:Q2", query)
        self.assertEqual(meta["expected"], {"titles": 2, "title_genres": 2, "title_credits": 1})
        self.assertLess(meta["query_bytes"], 100_000)

    def test_complete_state(self) -> None:
        _, meta = build_status_query(sample_sql(), FINGERPRINT)
        result = evaluate_status(meta, payload(2, 2, 1))
        self.assertEqual(result["state"], "complete")

    def test_not_started_state(self) -> None:
        _, meta = build_status_query(sample_sql(), FINGERPRINT)
        result = evaluate_status(meta, payload(0, 0, 0))
        self.assertEqual(result["state"], "not_started")

    def test_partial_state_is_unsafe(self) -> None:
        _, meta = build_status_query(sample_sql(), FINGERPRINT)
        result = evaluate_status(meta, payload(2, 1, 0))
        self.assertEqual(result["state"], "unsafe_partial")

    def test_overfilled_state_is_unsafe(self) -> None:
        _, meta = build_status_query(sample_sql(), FINGERPRINT)
        result = evaluate_status(meta, payload(3, 2, 1))
        self.assertEqual(result["state"], "unsafe_overfilled")

    def test_rejects_wrong_fingerprint(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected projection fingerprint"):
            build_status_query(sample_sql(), "deadbeef")

    def test_rejects_duplicate_title_ids(self) -> None:
        broken = sample_sql().replace(
            "INSERT INTO recommendation_titles (id,wikidata_qid) VALUES ('wikidata:Q2','Q2');",
            "INSERT INTO recommendation_titles (id,wikidata_qid) VALUES ('wikidata:Q1','Q1');",
        )
        with self.assertRaisesRegex(ValueError, "duplicate recommendation title ids"):
            build_status_query(broken, FINGERPRINT)


if __name__ == "__main__":
    unittest.main()
