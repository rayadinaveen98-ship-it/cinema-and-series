import json
import tempfile
import unittest
from pathlib import Path

from scripts.production_catalogue_quality import analyze_catalogue, load_d1_rows, render_markdown


class ProductionCatalogueQualityTests(unittest.TestCase):
    def test_load_d1_rows_flattens_wrangler_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.json"
            path.write_text(json.dumps([
                {"results": [{"id": "a"}]},
                {"results": [{"id": "b"}]},
            ]), encoding="utf-8")
            self.assertEqual(load_d1_rows(path), [{"id": "a"}, {"id": "b"}])

    def test_movie_projection_prefers_exact_movie_over_year_catalogue_qid(self):
        movies = [{
            "id": "m1", "wikidata_qid": "Q1", "title": "One",
            "language_name": "Telugu", "country_code": "IN",
            "release_date": "2025-01-01", "release_date_source": "wikidata",
        }]
        catalogue = [{
            "id": "c1", "wikidata_qid": "Q1", "title": "One",
            "language_name": "Telugu", "country_code": "IN",
            "release_year": 2025, "source_url": "https://example.test/one",
        }]
        report = analyze_catalogue(movies, catalogue, [])
        self.assertEqual(report["counts"]["projected_movies"], 1)
        self.assertEqual(report["counts"]["catalogue_movie_overlap_removed"], 1)

    def test_overlapping_year_movie_does_not_double_count_unknown_language(self):
        movies = [{
            "id": "m1", "wikidata_qid": "Q11", "title": "Film",
            "language_name": "Unknown", "country_code": "IN",
            "release_date": "2025-01-01", "release_date_source": "wikidata",
        }]
        catalogue = [{
            "id": "c1", "wikidata_qid": "Q11", "title": "Film",
            "language_name": "Unknown", "country_code": "IN",
            "release_year": 2025, "source_url": "",
        }]
        shows = [{
            "id": "s1", "wikidata_qid": "Q12", "title": "Show",
            "language_name": "Unknown", "country_code": "IN",
            "first_air_year": None, "source_url": "https://example.test/show",
            "series_kind": "series", "lifecycle_status": "unknown",
        }]
        report = analyze_catalogue(movies, catalogue, shows)
        self.assertEqual(report["counts"]["projected_total"], 2)
        self.assertEqual(report["counts"]["catalogue_movie_overlap_removed"], 1)
        self.assertEqual(report["counts"]["projected_unknown_language_titles"], 2)
        self.assertEqual(
            report["finding_summary"]["by_rule"]["METADATA.LANGUAGE_UNKNOWN"], 2)
        self.assertEqual(
            report["finding_summary"]["by_rule"].get("PROVENANCE.SOURCE_LOCATOR_MISSING", 0), 0)

    def test_unknown_metadata_count_reconciles_with_projected_coverage(self):
        films = [{
            "id": "m1", "wikidata_qid": "Q5", "title": "Known",
            "country_code": "IN", "language_name": "Tamil",
            "release_date": "2020-01-01", "release_date_source": "official",
        }]
        catalogue = [{
            "id": "c2", "wikidata_qid": "Q6", "title": "Unknown language",
            "country_code": "IN", "language_name": "Unknown",
            "release_year": 2019, "source_url": "https://example.test",
        }]
        r = analyze_catalogue(films, catalogue, [])
        self.assertEqual(r["counts"]["projected_unknown_language_titles"], 1)
        self.assertEqual(r["coverage"]["movies"]["language"]["numerator"], 1)
        self.assertEqual(r["finding_summary"]["by_rule"]["METADATA.LANGUAGE_UNKNOWN"], 1)

    def test_cross_type_qid_collision_is_critical(self):
        movies = [{
            "id": "m42", "wikidata_qid": "Q42", "title": "Collision",
            "language_name": "Hindi", "country_code": "IN",
            "release_date": "2020-01-01", "release_date_source": "wikidata",
        }]
        series = [{
            "id": "s42", "wikidata_qid": "Q42", "title": "Collision Series",
            "language_name": "Hindi", "country_code": "IN",
            "first_air_year": 2020, "last_air_year": 2021,
            "series_kind": "series", "lifecycle_status": "ended",
            "source_url": "https://example.test/collision",
        }]
        report = analyze_catalogue(movies, [], series)
        self.assertEqual(report["finding_summary"]["by_severity"]["S0"], 1)
        self.assertEqual(
            report["finding_summary"]["by_rule"]["IDENTITY.CROSS_TYPE_EXTERNAL_ID_COLLISION"],
            1,
        )

    def test_unknown_metadata_is_reported_without_fabrication(self):
        catalogue = [{
            "id": "c1", "wikidata_qid": "Q2", "title": "Unknown Meta",
            "language_name": "Unknown", "country_code": "XX",
            "release_year": 2000, "source_url": "https://example.test/u",
        }]
        report = analyze_catalogue([], catalogue, [])
        self.assertEqual(report["coverage"]["movies"]["language"]["percent"], 0.0)
        self.assertEqual(report["coverage"]["movies"]["country"]["percent"], 0.0)
        self.assertEqual(report["finding_summary"]["by_rule"]["METADATA.LANGUAGE_UNKNOWN"], 1)
        self.assertEqual(report["finding_summary"]["by_rule"]["METADATA.COUNTRY_UNKNOWN"], 1)

    def test_series_air_year_reversal_is_critical(self):
        series = [{
            "id": "s1", "wikidata_qid": "Q3", "title": "Reverse",
            "language_name": "Tamil", "country_code": "IN",
            "first_air_year": 2025, "last_air_year": 2020,
            "series_kind": "series", "lifecycle_status": "ended",
            "source_url": "https://example.test/reverse",
        }]
        report = analyze_catalogue([], [], series)
        self.assertEqual(report["finding_summary"]["by_severity"]["S0"], 1)
        self.assertEqual(report["finding_summary"]["by_rule"]["SERIES.IMPOSSIBLE_AIR_YEAR_ORDER"], 1)

    def test_markdown_keeps_coverage_dimensions_separate(self):
        markdown = render_markdown(analyze_catalogue([], [], []))
        self.assertIn("no composite quality score", markdown)
        self.assertIn("India priority-language catalogue counts", markdown)


if __name__ == "__main__":
    unittest.main()
