import unittest

from scripts import recommendation_delta_materialization as delta


def entry(qid: str, media_type: str = "movie", title: str | None = None):
    return {
        "wikidata_qid": qid,
        "media_type": media_type,
        "display_title": title or qid,
        "source_table": "movies" if media_type == "movie" else "series_titles",
        "source_id": ("wd-" if media_type == "movie" else "series-wd-") + qid,
        "source_url": f"https://www.wikidata.org/wiki/{qid}",
    }


def manifest(entries, sha):
    return {"entries": entries, "sha256": sha}


class RecommendationDeltaMaterializationTests(unittest.TestCase):
    def test_exact_common_entries_are_reusable(self):
        common = entry("Q42")
        result = delta.manifest_delta(
            manifest([common, entry("Q3049630", "series")], "parent"),
            manifest([common, entry("Q99")], "current"),
        )
        self.assertEqual(result["unchanged_count"], 1)
        self.assertEqual(result["added_qids"], ["Q99"])
        self.assertEqual(result["removed_qids"], ["Q3049630"])

    def test_changed_common_entry_hard_fails(self):
        with self.assertRaisesRegex(ValueError, "changed"):
            delta.manifest_delta(
                manifest([entry("Q42", title="Old")], "parent"),
                manifest([entry("Q42", title="New")], "current"),
            )

    def test_unreviewed_removal_hard_fails(self):
        with self.assertRaisesRegex(ValueError, "lack reviewed exclusion provenance"):
            delta.manifest_delta(
                manifest([entry("Q42")], "parent"),
                manifest([], "current"),
            )


if __name__ == "__main__":
    unittest.main()
