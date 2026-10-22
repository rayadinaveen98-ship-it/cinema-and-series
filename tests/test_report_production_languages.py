"""Production language report merges two film tables and leaves series distinct."""
import unittest
from scripts.report_production_languages import summarize, clean_language


class LanguageReportTests(unittest.TestCase):
    def test_aggregates_full_country_and_india_language_rows(self):
        sample = {
            "movies": [
                {"language": "Telugu", "country_code": "IN", "title_count": 4},
                {"language": "English", "country_code": "US", "title_count": 2}],
            "catalogue_titles": [
                {"language": "Telugu", "country_code": "IN", "title_count": 10},
                {"language": "Unknown", "country_code": "XX", "title_count": 3}],
            "series_titles": [
                {"language": "Telugu", "country_code": "IN", "title_count": 8},
                {"language": "English", "country_code": "GB", "title_count": 12}],
        }
        result = summarize(sample)
        self.assertEqual(result["film_count"], 19)
        self.assertEqual(result["series_count"], 20)
        self.assertEqual(result["title_count"], 39)
        self.assertEqual(result["indian_films"], 14)
        self.assertEqual(result["indian_series"], 8)
        self.assertEqual(result["language_count_including_unknown"], 3)
        self.assertEqual(result["languages"][0]["language"], "Telugu")
        self.assertEqual(result["languages"][0]["total"], 22)
        self.assertEqual(result["database_writes"], 0)

    def test_unknown_label(self):
        for original in (None, "", "und", "  UNKnown  ", "n/a"):
            self.assertEqual(clean_language(original), "Unknown")

    def test_rejects_missing_table_and_noninteger_counts(self):
        data = {"movies": [], "catalogue_titles": [], "series_titles": []}
        with self.assertRaises(ValueError):
            summarize({"movies": [], "series_titles": []})
        for bad in (0, -1, True, "10"):
            invalid = {**data, "movies": [{"language":"Hindi","country_code":"IN","title_count": bad}]}
            with self.assertRaises(ValueError):
                summarize(invalid)


if __name__ == "__main__":
    unittest.main()
