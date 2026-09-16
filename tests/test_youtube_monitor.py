import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "youtube_monitor.py"
spec = importlib.util.spec_from_file_location("youtube_monitor", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class YouTubeMonitorTests(unittest.TestCase):
    def test_extracts_day_month_year_near_release_context(self):
        text = "Jailer 2 releases worldwide on 15 October 2026."
        self.assertEqual(module.extract_release_dates(text), ["2026-10-15"])

    def test_extracts_month_day_year_near_cinema_context(self):
        text = "In cinemas October 15, 2026. Official announcement."
        self.assertEqual(module.extract_release_dates(text), ["2026-10-15"])

    def test_extracts_numeric_date_with_release_context(self):
        text = "Worldwide release 11/06/2027"
        self.assertEqual(module.extract_release_dates(text), ["2027-06-11"])

    def test_infers_year_for_yearless_month_day_from_unique_upcoming_year(self):
        text = (
            "RANABAALI is an Upcoming 2026 PAN India Movie. "
            "The savage's oath begins now. RANABAALI In Theatres From October 16th!!"
        )
        contexts = module.extract_release_date_contexts(text)
        self.assertEqual([item["date"] for item in contexts], ["2026-10-16"])
        self.assertIn("October 16th", contexts[0]["excerpt"])
        self.assertIn("2026", contexts[0]["excerpt"])

    def test_infers_year_for_yearless_day_month_from_unique_release_year(self):
        text = "Official 2027 release announcement. In cinemas from 11th June."
        self.assertEqual(module.extract_release_dates(text), ["2027-06-11"])

    def test_does_not_infer_yearless_date_without_release_year_phrase(self):
        text = "Official teaser. In theatres October 16th."
        self.assertEqual(module.extract_release_dates(text), [])

    def test_does_not_infer_yearless_date_when_multiple_years_are_present(self):
        text = (
            "Upcoming 2026 film inspired by the 2024 story. "
            "In theatres October 16th."
        )
        self.assertEqual(module.extract_release_dates(text), [])

    def test_does_not_infer_from_bare_or_copyright_year(self):
        text = "Copyright 2026 Studio. In theatres October 16th."
        self.assertEqual(module.extract_release_dates(text), [])

    def test_release_context_preserves_short_review_excerpt(self):
        text = (
            "Main Na Raha Mera teaser. Watch now. "
            "The film releases worldwide in cinemas on 23 October 2026. "
            "Subscribe for official updates."
        )
        contexts = module.extract_release_date_contexts(text)
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["date"], "2026-10-23")
        self.assertIn("releases worldwide in cinemas", contexts[0]["excerpt"])
        self.assertIn("23 October 2026", contexts[0]["excerpt"])
        self.assertNotIn("\n", contexts[0]["excerpt"])

    def test_release_context_dedupes_multiple_mentions_of_same_date(self):
        contexts = module.extract_release_date_contexts(
            "In cinemas 15 October 2026. Jailer 2 releases worldwide on 15 October 2026."
        )
        self.assertEqual([item["date"] for item in contexts], ["2026-10-15"])

    def test_rejects_unrelated_date(self):
        text = "Our channel started on October 15, 2026. Subscribe now."
        self.assertEqual(module.extract_release_dates(text), [])

    def test_multiple_dates_are_not_collapsed_to_single_candidate(self):
        dates = module.extract_release_dates("Releasing 15 October 2026. In cinemas 22 October 2026 overseas.")
        self.assertEqual(dates, ["2026-10-15", "2026-10-22"])

    def test_filters_historical_catalogue_date_from_recent_upload(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2017-05-12", "2026-10-15"],
            "2026-09-16T06:30:20Z",
            now=now,
        )
        self.assertEqual(dates, ["2026-10-15"])

    def test_rejects_stale_upload_even_with_future_date(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2027-06-11"],
            "2026-01-01T00:00:00Z",
            now=now,
        )
        self.assertEqual(dates, [])

    def test_rejects_release_date_that_has_already_passed_at_scan_time(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2026-09-04"],
            "2026-08-04T05:30:37Z",
            now=now,
        )
        self.assertEqual(dates, [])

    def test_rejects_post_release_promo_date(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2026-09-12"],
            "2026-09-16T06:30:20Z",
            now=now,
        )
        self.assertEqual(dates, [])

    def test_keeps_same_day_release_signal(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2026-09-16"],
            "2026-09-16T06:30:20Z",
            now=now,
        )
        self.assertEqual(dates, ["2026-09-16"])

    def test_keeps_future_release_signal_from_recent_announcement(self):
        now = datetime(2026, 9, 16, tzinfo=timezone.utc)
        dates = module.filter_plausible_release_dates(
            ["2026-10-15"],
            "2026-08-20T06:30:20Z",
            now=now,
        )
        self.assertEqual(dates, ["2026-10-15"])

    def test_rejects_public_response_promo_title(self):
        self.assertTrue(module.is_low_value_promo("Korean Kanakaraju Public Response | Varun Tej"))

    def test_keeps_release_announcement_title(self):
        self.assertFalse(module.is_low_value_promo("Mirzapur The Movie | In Cinemas 4 Sep 2026"))

    def test_fetch_candidate_keeps_only_plausible_date_contexts(self):
        source = {"key": "studio", "name": "Studio"}
        payload = {
            "items": [
                {
                    "snippet": {
                        "title": "Example Film teaser",
                        "description": "Old release 1 January 2020. In cinemas 23 October 2026.",
                        "publishedAt": "2026-09-16T06:30:20Z",
                    },
                    "contentDetails": {"videoId": "abc123"},
                }
            ]
        }
        with patch.object(module, "api_get", return_value=payload):
            candidates = module.fetch_latest_uploads(
                source,
                "UC-studio",
                "UU-studio",
                now=datetime(2026, 9, 16, tzinfo=timezone.utc),
            )
        self.assertEqual(candidates[0]["candidate_dates"], ["2026-10-23"])
        self.assertEqual([item["date"] for item in candidates[0]["date_contexts"]], ["2026-10-23"])

    def test_fetch_candidate_supports_split_year_and_day_metadata(self):
        source = {"key": "studio", "name": "Studio"}
        payload = {
            "items": [
                {
                    "snippet": {
                        "title": "Example Film teaser",
                        "description": "Upcoming 2026 PAN India Movie. In Theatres From October 16th.",
                        "publishedAt": "2026-09-09T06:30:20Z",
                    },
                    "contentDetails": {"videoId": "split123"},
                }
            ]
        }
        with patch.object(module, "api_get", return_value=payload):
            candidates = module.fetch_latest_uploads(
                source,
                "UC-studio",
                "UU-studio",
                now=datetime(2026, 9, 16, tzinfo=timezone.utc),
            )
        self.assertEqual(candidates[0]["candidate_dates"], ["2026-10-16"])
        self.assertEqual(candidates[0]["candidate_release_date"], "2026-10-16")

    def test_sql_keeps_candidates_pending_review(self):
        sql = module.build_sql([
            {
                "source_key": "sun_pictures",
                "video_id": "abc123",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "video_title": "Jailer 2 release date",
                "published_at": "2026-09-16T00:00:00Z",
                "candidate_dates": ["2026-10-15"],
                "candidate_release_date": "2026-10-15",
            }
        ])
        self.assertIn("pending_review", sql)
        self.assertNotIn("verification_status", sql)
        self.assertIn("ON CONFLICT(source_key, external_id) DO UPDATE", sql)

    def test_sql_upserts_source_before_fk_observation(self):
        source = {
            "key": "excel_entertainment",
            "name": "Excel Entertainment",
            "source_type": "production_house",
            "website_url": None,
            "youtube_channel_id": None,
            "youtube_handle": "@ExcelMovies",
            "active": True,
        }
        candidate = {
            "source_key": "excel_entertainment",
            "video_id": "kWh6fgcreyw",
            "video_url": "https://www.youtube.com/watch?v=kWh6fgcreyw",
            "video_title": "Mirzapur The Movie | In Cinemas 4 Sep 2026",
            "published_at": "2026-08-04T05:30:37Z",
            "candidate_dates": ["2026-09-04"],
            "candidate_release_date": "2026-09-04",
        }
        sql = module.build_sql([candidate], [source])
        source_pos = sql.index("INSERT INTO source_channels")
        observation_pos = sql.index("INSERT INTO source_observations")
        self.assertLess(source_pos, observation_pos)
        self.assertIn("@ExcelMovies", sql)
        self.assertIn("pending_review", sql)

    def test_empty_candidate_queue_selects_no_sources_and_builds_no_sql(self):
        source = {"key": "excel_entertainment", "name": "Excel Entertainment"}
        selected = module.sources_for_candidates([], [source])
        self.assertEqual(selected, [])
        self.assertEqual(module.build_sql([], selected), "")

    def test_candidate_queue_selects_only_matching_sources(self):
        sources = [
            {"key": "one", "name": "One"},
            {"key": "two", "name": "Two"},
        ]
        selected = module.sources_for_candidates([{"source_key": "two"}], sources)
        self.assertEqual([source["key"] for source in selected], ["two"])

    def test_handle_only_source_resolves_through_official_channels_api(self):
        source = {
            "key": "dharma_productions",
            "name": "Dharma Productions",
            "youtube_channel_id": None,
            "youtube_handle": "@DharmaMovies",
        }
        payload = {
            "items": [
                {
                    "id": "UC-resolved",
                    "contentDetails": {"relatedPlaylists": {"uploads": "UU-resolved"}},
                }
            ]
        }
        with patch.object(module, "api_get", return_value=payload) as mocked:
            resolved = module.resolve_upload_playlists([source])

        self.assertEqual(
            resolved["dharma_productions"],
            {"channel_id": "UC-resolved", "uploads_playlist_id": "UU-resolved"},
        )
        mocked.assert_called_once_with(
            "channels",
            {"part": "contentDetails", "forHandle": "DharmaMovies", "maxResults": "1"},
        )


if __name__ == "__main__":
    unittest.main()
